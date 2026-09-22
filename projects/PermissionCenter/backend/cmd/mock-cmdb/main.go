// mock-cmdb：模拟外部数据源（CMDB）
// 提供 OpenAPI 3 文档 + 模型/实例 CRUD + 变更事件（写 Redis Streams，与审计事件总线两用）
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

type Instance struct {
	ID         uint64         `json:"id"`
	Name       string         `json:"name"`
	Attributes map[string]any `json:"attributes"`
	OwnerID    *uint64        `json:"owner_id"`
	UpdatedAt  string         `json:"updated_at"`
}

type Model struct {
	ID               uint64               `json:"id"`
	Name             string               `json:"name"`
	Code             string               `json:"code"`
	AttributesSchema map[string]any       `json:"attributes_schema"`
	Instances        map[uint64]*Instance `json:"-"`
}

type cmdb struct {
	mu      sync.RWMutex
	nextID  uint64
	models  map[string]*Model
	rdb     *redis.Client
	version uint64 // 集合变更计数（指纹端点观测字段，atomic 读写；指纹比对不依赖它）
}

func newCMDB() *cmdb {
	c := &cmdb{nextID: 1, models: map[string]*Model{}}
	// 三个资源板块：host / network / disk
	c.models["host"] = &Model{ID: c.nextID, Name: "主机", Code: "host",
		AttributesSchema: map[string]any{"status": "string", "ip": "string", "env": "string"},
		Instances:        map[uint64]*Instance{}}
	c.nextID++
	c.models["network"] = &Model{ID: c.nextID, Name: "网络", Code: "network",
		AttributesSchema: map[string]any{"cidr": "string", "region": "string"},
		Instances:        map[uint64]*Instance{}}
	c.nextID++
	c.models["disk"] = &Model{ID: c.nextID, Name: "磁盘", Code: "disk",
		AttributesSchema: map[string]any{"size_gb": "number", "type": "string"},
		Instances:        map[uint64]*Instance{}}
	c.nextID++
	c.models["database"] = &Model{ID: c.nextID, Name: "数据库", Code: "database",
		AttributesSchema: map[string]any{"db_name": "string", "owner_dept": "string", "backup_policy": "string"},
		Instances:        map[uint64]*Instance{}}
	// 种子实例（host 带 owner 关系锚点）
	aliceID := uint64(1)
	bobID := uint64(2)
	c.seed("host", "web-01", map[string]any{"status": "active", "ip": "10.0.0.11", "env": "prod"}, &aliceID)
	c.seed("host", "web-02", map[string]any{"status": "active", "ip": "10.0.0.12", "env": "prod"}, &bobID)
	c.seed("host", "db-01", map[string]any{"status": "active", "ip": "10.0.1.11", "env": "prod"}, nil)
	c.seed("network", "vpc-prod", map[string]any{"cidr": "10.0.0.0/16", "region": "cn-north-1"}, nil)
	c.seed("disk", "data-disk-01", map[string]any{"size_gb": 512, "type": "ssd"}, nil)
	c.seed("database", "db-cmdb", map[string]any{"db_name": "db-cmdb", "owner_dept": "效能部门", "backup_policy": "daily"}, nil)
	c.seed("database", "db-order", map[string]any{"db_name": "db-order", "owner_dept": "业务", "backup_policy": "weekly"}, nil)
	return c
}

// seedBaseTime 种子时间固定基准值（A3 演示纪律）：重启 mock 不刷新全表 updated_at →
// 巡检指纹不误判、IAM 侧无假变更洪水；真实变更一律走 API（毫秒精度 RFC3339Nano 时间戳）
var seedBaseTime = time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)

func (c *cmdb) seed(modelCode, name string, attrs map[string]any, owner *uint64) {
	m := c.models[modelCode]
	m.Instances[c.nextID] = &Instance{ID: c.nextID, Name: name, Attributes: attrs, OwnerID: owner, UpdatedAt: seedBaseTime.Format(time.RFC3339Nano)}
	c.nextID++
}

func (c *cmdb) publish(ctx context.Context, evType, modelCode string, inst *Instance) {
	atomic.AddUint64(&c.version, 1) // 每次集合变更 +1（观测字段；create/update/delete 五路写入全走这里）
	if c.rdb == nil {
		return
	}
	values := map[string]any{
		"type":        evType,
		"model":       modelCode,
		"instance_id": fmt.Sprintf("%s-%d", modelCode, inst.ID),
		"ts":          time.Now().Format(time.RFC3339Nano),
	}
	if err := c.rdb.XAdd(ctx, &redis.XAddArgs{Stream: "cmdb-events", Values: values}).Err(); err != nil {
		log.Printf("[mock-cmdb] publish event failed: %v", err)
	}
}

func main() {
	addr := os.Getenv("CMDB_HTTP_ADDR")
	if addr == "" {
		addr = ":8090"
	}
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}
	rdb := redis.NewClient(&redis.Options{Addr: redisAddr})
	ctx := context.Background()
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Printf("[mock-cmdb] redis unavailable, events disabled: %v", err)
		rdb = nil
	}

	c := newCMDB()
	c.rdb = rdb

	r := gin.Default()
	r.GET("/healthz", func(g *gin.Context) { g.JSON(200, gin.H{"status": "ok"}) })
	r.GET("/openapi.json", func(g *gin.Context) { g.Data(200, "application/json", openapiJSON()) })

	// A3 集合指纹端点（数据契约算法菜单 L2 的发布方侧实现，实施清单 A3）
	// 指纹契约（IAM A4 巡检同款算法，两侧必须逐字一致）：
	//   external_id = "<model>-<id>"（与 IAM 投影 ExternalID 同构），按字典序排序
	//   hash_ids        = sha256(join(external_ids, "\n"))
	//   hash_updated_at = sha256(join(同序 updated_at, "\n"))
	//   fingerprint     = hash_ids XOR hash_updated_at（hex）
	// version / count / max_updated_at 仅为观测字段——判定只认指纹比对，不数版本
	r.GET("/sync/fingerprint", func(g *gin.Context) {
		code := g.Query("model")
		if code == "" {
			g.JSON(400, gin.H{"error": "model query required"})
			return
		}
		c.mu.RLock()
		defer c.mu.RUnlock()
		m, ok := c.models[code]
		if !ok {
			g.JSON(404, gin.H{"error": "model not found"})
			return
		}
		type pair struct{ ext, ts string }
		pairs := make([]pair, 0, len(m.Instances))
		for id, inst := range m.Instances {
			pairs = append(pairs, pair{fmt.Sprintf("%s-%d", code, id), inst.UpdatedAt})
		}
		sort.Slice(pairs, func(i, j int) bool { return pairs[i].ext < pairs[j].ext })
		var idBuf, tsBuf strings.Builder
		maxTS := ""
		for _, p := range pairs {
			idBuf.WriteString(p.ext)
			idBuf.WriteByte('\n')
			tsBuf.WriteString(p.ts)
			tsBuf.WriteByte('\n')
			if p.ts > maxTS {
				maxTS = p.ts
			}
		}
		h1 := sha256.Sum256([]byte(idBuf.String()))
		h2 := sha256.Sum256([]byte(tsBuf.String()))
		xor := make([]byte, sha256.Size)
		for i := range xor {
			xor[i] = h1[i] ^ h2[i]
		}
		g.JSON(200, gin.H{
			"model": code, "version": atomic.LoadUint64(&c.version), "count": len(pairs),
			"max_updated_at": maxTS,
			"hash_ids":       hex.EncodeToString(h1[:]), "hash_updated_at": hex.EncodeToString(h2[:]),
			"fingerprint": hex.EncodeToString(xor),
		})
	})

	// 模型
	r.GET("/api/v1/models", func(g *gin.Context) {
		c.mu.RLock()
		defer c.mu.RUnlock()
		var out []Model
		for _, m := range c.models {
			out = append(out, *m)
		}
		g.JSON(200, out)
	})

	// 实例列表
	r.GET("/api/v1/models/:code/instances", func(g *gin.Context) {
		c.mu.RLock()
		defer c.mu.RUnlock()
		m, ok := c.models[g.Param("code")]
		if !ok {
			g.JSON(404, gin.H{"error": "model not found"})
			return
		}
		var out []*Instance
		for _, inst := range m.Instances {
			out = append(out, inst)
		}
		g.JSON(200, out)
	})

	// 实例详情
	r.GET("/api/v1/models/:code/instances/:id", func(g *gin.Context) {
		c.mu.RLock()
		defer c.mu.RUnlock()
		m, ok := c.models[g.Param("code")]
		if !ok {
			g.JSON(404, gin.H{"error": "model not found"})
			return
		}
		for _, inst := range m.Instances {
			if fmt.Sprintf("%d", inst.ID) == g.Param("id") {
				g.JSON(200, inst)
				return
			}
		}
		g.JSON(404, gin.H{"error": "instance not found"})
	})

	// 实例创建（模拟：POST 需鉴权，见 APISIX 路由）
	r.POST("/api/v1/models/:code/instances", func(g *gin.Context) {
		var body Instance
		if err := g.ShouldBindJSON(&body); err != nil {
			g.JSON(400, gin.H{"error": err.Error()})
			return
		}
		c.mu.Lock()
		m, ok := c.models[g.Param("code")]
		if !ok {
			c.mu.Unlock()
			g.JSON(404, gin.H{"error": "model not found"})
			return
		}
		body.ID = c.nextID
		body.UpdatedAt = time.Now().Format(time.RFC3339Nano)
		c.nextID++
		m.Instances[body.ID] = &body
		cp := body
		c.mu.Unlock()
		c.publish(g.Request.Context(), "create", m.Code, &cp)
		g.JSON(201, cp)
	})

	// 实例删除
	r.DELETE("/api/v1/models/:code/instances/:id", func(g *gin.Context) {
		c.mu.Lock()
		m, ok := c.models[g.Param("code")]
		if !ok {
			c.mu.Unlock()
			g.JSON(404, gin.H{"error": "model not found"})
			return
		}
		var id uint64
		fmt.Sscanf(g.Param("id"), "%d", &id)
		inst, exists := m.Instances[id]
		if !exists {
			c.mu.Unlock()
			g.JSON(404, gin.H{"error": "instance not found"})
			return
		}
		delete(m.Instances, id)
		c.mu.Unlock()
		c.publish(g.Request.Context(), "delete", m.Code, inst)
		g.JSON(200, gin.H{"ok": true})
	})

	// ---- 公共业务 API（经网关 PEP 保护，路径与 OpenAPI 文档一致）----
	// GET/POST /api/v1/hosts、/api/v1/hosts/{id}（含 networks/disks）
	pub := r.Group("/api/v1")

	// 统一查询入口（阶段 9 演示）：GET /api/v1/entities，经 X-Resource-Type / ?type= 指定资源类型
	// 网关 PEP 据此头解析具体权限点（cmdb:host:list），防类型漂移
	pub.GET("/entities", func(g *gin.Context) {
		resType := g.GetHeader("X-Resource-Type")
		if resType == "" {
			resType = g.Query("type")
		}
		m, ok := c.modelByResource(resType)
		if !ok {
			g.JSON(404, gin.H{"error": "resource type not found: " + resType})
			return
		}
		c.mu.RLock()
		defer c.mu.RUnlock()
		var out []*Instance
		for _, inst := range m.Instances {
			out = append(out, inst)
		}
		g.JSON(200, gin.H{"items": out, "resource_type": resType})
	})

	pub.GET("/:res", func(g *gin.Context) {
		m, ok := c.modelByResource(g.Param("res"))
		if !ok {
			g.JSON(404, gin.H{"error": "resource not found"})
			return
		}
		c.mu.RLock()
		defer c.mu.RUnlock()
		var out []*Instance
		for _, inst := range m.Instances {
			out = append(out, inst)
		}
		g.JSON(200, gin.H{"items": out})
	})
	pub.GET("/:res/:id", func(g *gin.Context) {
		m, ok := c.modelByResource(g.Param("res"))
		if !ok {
			g.JSON(404, gin.H{"error": "resource not found"})
			return
		}
		c.mu.RLock()
		defer c.mu.RUnlock()
		for _, inst := range m.Instances {
			if fmt.Sprintf("%d", inst.ID) == g.Param("id") {
				g.JSON(200, inst)
				return
			}
		}
		g.JSON(404, gin.H{"error": "instance not found"})
	})
	pub.POST("/:res", func(g *gin.Context) {
		m, ok := c.modelByResource(g.Param("res"))
		if !ok {
			g.JSON(404, gin.H{"error": "resource not found"})
			return
		}
		var body Instance
		if err := g.ShouldBindJSON(&body); err != nil {
			g.JSON(400, gin.H{"error": err.Error()})
			return
		}
		c.mu.Lock()
		body.ID = c.nextID
		body.UpdatedAt = time.Now().Format(time.RFC3339Nano)
		c.nextID++
		m.Instances[body.ID] = &body
		cp := body
		c.mu.Unlock()
		c.publish(g.Request.Context(), "create", m.Code, &cp)
		g.JSON(201, cp)
	})
	pub.PATCH("/:res/:id", func(g *gin.Context) {
		m, ok := c.modelByResource(g.Param("res"))
		if !ok {
			g.JSON(404, gin.H{"error": "resource not found"})
			return
		}
		var id uint64
		fmt.Sscanf(g.Param("id"), "%d", &id)
		var body Instance
		if err := g.ShouldBindJSON(&body); err != nil {
			g.JSON(400, gin.H{"error": err.Error()})
			return
		}
		c.mu.Lock()
		inst, exists := m.Instances[id]
		if !exists {
			c.mu.Unlock()
			g.JSON(404, gin.H{"error": "instance not found"})
			return
		}
		if body.Name != "" {
			inst.Name = body.Name
		}
		if body.Attributes != nil {
			inst.Attributes = body.Attributes
		}
		inst.UpdatedAt = time.Now().Format(time.RFC3339Nano)
		cp := *inst
		c.mu.Unlock()
		c.publish(g.Request.Context(), "update", m.Code, &cp)
		g.JSON(200, cp)
	})
	pub.DELETE("/:res/:id", func(g *gin.Context) {
		m, ok := c.modelByResource(g.Param("res"))
		if !ok {
			g.JSON(404, gin.H{"error": "resource not found"})
			return
		}
		var id uint64
		fmt.Sscanf(g.Param("id"), "%d", &id)
		c.mu.Lock()
		inst, exists := m.Instances[id]
		if !exists {
			c.mu.Unlock()
			g.JSON(404, gin.H{"error": "instance not found"})
			return
		}
		delete(m.Instances, id)
		c.mu.Unlock()
		c.publish(g.Request.Context(), "delete", m.Code, inst)
		g.JSON(200, gin.H{"ok": true})
	})

	log.Printf("[mock-cmdb] listening %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}

// modelByResource 公共 API 资源名 → 模型（hosts→host / networks→network / disks→disk；兼容单数）
func (c *cmdb) modelByResource(res string) (*Model, bool) {
	r := strings.ToLower(res)
	code := map[string]string{"hosts": "host", "networks": "network", "disks": "disk"}[r]
	if code == "" {
		if _, ok := c.models[r]; ok {
			code = r
		}
	}
	if code == "" {
		return nil, false
	}
	c.mu.RLock()
	defer c.mu.RUnlock()
	m, ok := c.models[code]
	return m, ok
}

// openapiJSON OpenAPI 3 文档：host/network/disk 三个板块（字面路由）+ 通用接口（阶段 9 演示）
// 通用接口：/api/v1/{model}（资源位置为槽位，PEP 路径模板解析）、/api/v1/entities（X-Resource-Type）
// v12：补充 components.schemas + 每个操作的 parameters/requestBody/responses（接口契约示例生成）
func openapiJSON() []byte {
	doc := map[string]any{
		"openapi": "3.0.0",
		"info":    map[string]any{"title": "CMDB API", "version": "1.0.0"},
		"paths":   map[string]any{},
		"components": map[string]any{
			"schemas": map[string]any{
				"Host": map[string]any{
					"type":     "object",
					"required": []string{"name", "ip", "env"},
					"properties": map[string]any{
						"id":         map[string]any{"type": "integer", "example": 1},
						"name":       map[string]any{"type": "string", "example": "web-01"},
						"ip":         map[string]any{"type": "string", "example": "10.0.0.11"},
						"env":        map[string]any{"type": "string", "enum": []string{"prod", "test"}, "example": "prod"},
						"region":     map[string]any{"type": "string", "example": "cn-east-1"},
						"created_at": map[string]any{"type": "string", "format": "date-time"},
					},
				},
				"Network": map[string]any{
					"type": "object",
					"properties": map[string]any{
						"id":     map[string]any{"type": "integer", "example": 1},
						"name":   map[string]any{"type": "string", "example": "vpc-web"},
						"cidr":   map[string]any{"type": "string", "example": "10.0.0.0/16"},
						"region": map[string]any{"type": "string", "example": "cn-east-1"},
					},
				},
				"Disk": map[string]any{
					"type": "object",
					"properties": map[string]any{
						"id":      map[string]any{"type": "integer", "example": 1},
						"name":    map[string]any{"type": "string", "example": "disk-data-01"},
						"size_gb": map[string]any{"type": "integer", "example": 100},
						"type":    map[string]any{"type": "string", "enum": []string{"ssd", "hdd"}, "example": "ssd"},
					},
				},
				"HostList": map[string]any{
					"type": "object",
					"properties": map[string]any{
						"items": map[string]any{"type": "array", "items": map[string]any{"$ref": "#/components/schemas/Host"}},
						"total": map[string]any{"type": "integer", "example": 2},
					},
				},
				"Ok": map[string]any{
					"type":       "object",
					"properties": map[string]any{"ok": map[string]any{"type": "boolean", "example": true}},
				},
			},
		},
	}
	paths := doc["paths"].(map[string]any)
	resources := []string{"hosts", "networks", "disks"}
	for _, res := range resources {
		base := "/api/v1/" + res
		schemaRef := schemaRefFor(res)
		paths[base] = map[string]any{
			"get": map[string]any{
				"tags": []string{tagOf(res)}, "operationId": "list" + res, "summary": "查询" + res,
				"parameters": []any{
					paramDef("page", "query", map[string]any{"type": "integer", "example": 1}),
					paramDef("page_size", "query", map[string]any{"type": "integer", "example": 20}),
				},
				"responses": map[string]any{"200": respDef(schemaRef + "List")},
			},
			"post": map[string]any{
				"tags": []string{tagOf(res)}, "operationId": "create" + res, "summary": "创建" + res,
				"requestBody": map[string]any{"content": mediaJSON(schemaRef), "required": true},
				"responses":   map[string]any{"201": respDef(schemaRef)},
			},
		}
		paths[base+"/{id}"] = map[string]any{
			"get": map[string]any{
				"tags": []string{tagOf(res)}, "operationId": "get" + res, "summary": "详情" + res,
				"parameters": []any{paramDef("id", "path", map[string]any{"type": "integer"})},
				"responses":  map[string]any{"200": respDef(schemaRef)},
			},
			"patch": map[string]any{
				"tags": []string{tagOf(res)}, "operationId": "update" + res, "summary": "更新" + res,
				"parameters":  []any{paramDef("id", "path", map[string]any{"type": "integer"})},
				"requestBody": map[string]any{"content": mediaJSON(schemaRef), "required": true},
				"responses":   map[string]any{"200": respDef(schemaRef)},
			},
			"delete": map[string]any{
				"tags": []string{tagOf(res)}, "operationId": "delete" + res, "summary": "删除" + res,
				"parameters": []any{paramDef("id", "path", map[string]any{"type": "integer"})},
				"responses":  map[string]any{"200": respDef("Ok")},
			},
		}
	}
	// 通用接口（一个 handler 处理多类资源）
	paths["/api/v1/{model}"] = map[string]any{
		"get": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "listByModel", "summary": "按资源类型查询列表",
			"parameters": []any{
				paramDef("model", "path", map[string]any{"type": "string", "example": "hosts"}),
				paramDef("page", "query", map[string]any{"type": "integer", "example": 1}),
			},
			"responses": map[string]any{"200": respDef("HostList")},
		},
		"post": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "createByModel", "summary": "按资源类型创建",
			"parameters":  []any{paramDef("model", "path", map[string]any{"type": "string", "example": "hosts"})},
			"requestBody": map[string]any{"content": mediaJSON("Host"), "required": true},
			"responses":   map[string]any{"201": respDef("Host")},
		},
	}
	paths["/api/v1/{model}/{id}"] = map[string]any{
		"get": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "getByModel", "summary": "按资源类型查详情",
			"parameters": []any{
				paramDef("model", "path", map[string]any{"type": "string", "example": "hosts"}),
				paramDef("id", "path", map[string]any{"type": "integer"}),
			},
			"responses": map[string]any{"200": respDef("Host")},
		},
		"patch": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "updateByModel", "summary": "按资源类型更新",
			"parameters": []any{
				paramDef("model", "path", map[string]any{"type": "string", "example": "hosts"}),
				paramDef("id", "path", map[string]any{"type": "integer"}),
			},
			"requestBody": map[string]any{"content": mediaJSON("Host"), "required": true},
			"responses":   map[string]any{"200": respDef("Host")},
		},
		"delete": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "deleteByModel", "summary": "按资源类型删除",
			"parameters": []any{
				paramDef("model", "path", map[string]any{"type": "string", "example": "hosts"}),
				paramDef("id", "path", map[string]any{"type": "integer"}),
			},
			"responses": map[string]any{"200": respDef("Ok")},
		},
	}
	// 统一查询入口（X-Resource-Type）
	paths["/api/v1/entities"] = map[string]any{
		"get": map[string]any{
			"tags": []string{"通用接口"}, "operationId": "listEntities", "summary": "统一查询（X-Resource-Type）",
			"parameters": []any{
				paramDef("type", "query", map[string]any{"type": "string", "example": "hosts"}),
				paramDef("X-Resource-Type", "header", map[string]any{"type": "string", "example": "host"}),
			},
			"responses": map[string]any{"200": respDef("HostList")},
		},
	}
	b, _ := json.MarshalIndent(doc, "", "  ")
	return b
}

func schemaRefFor(res string) string {
	return map[string]string{"hosts": "Host", "networks": "Network", "disks": "Disk"}[res]
}
func paramDef(name, in string, schema map[string]any) map[string]any {
	return map[string]any{"name": name, "in": in, "schema": schema}
}
func mediaJSON(schemaRef string) map[string]any {
	return map[string]any{"application/json": map[string]any{"schema": map[string]any{"$ref": "#/components/schemas/" + schemaRef}}}
}
func respDef(schemaRef string) map[string]any {
	return map[string]any{"description": "OK", "content": mediaJSON(schemaRef)}
}

func tagOf(res string) string {
	return map[string]string{"hosts": "主机管理", "networks": "网络管理", "disks": "磁盘管理"}[res]
}
