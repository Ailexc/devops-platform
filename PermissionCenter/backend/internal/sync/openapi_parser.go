// Package sync 同步连接器：OpenAPI / CMDB / Identity
package sync

import (
	"encoding/json"
	"fmt"
	"strings"
)

// OpenAPIDoc OpenAPI 3 文档（解析：paths 权限点 + components.schemas 数据模型 + 参数契约）
type OpenAPIDoc struct {
	OpenAPI string `json:"openapi"`
	Info    struct {
		Title string `json:"title"`
	} `json:"info"`
	Paths      map[string]map[string]Operation `json:"paths"`
	Components struct {
		Schemas map[string]SchemaDef `json:"schemas"`
	} `json:"components"`
}

// SchemaDef 组件 Schema 定义（字段级信息用于 data_model 推断 + 接口契约示例生成）
type SchemaDef struct {
	Type       string                `json:"type"`
	Properties map[string]SchemaProp `json:"properties"`
	Required   []string              `json:"required"`
	Ref        string                `json:"$ref"`
	Items      *SchemaProp           `json:"items"`
	Enum       []any                 `json:"enum"`
	Format     string                `json:"format"`
	Example    any                   `json:"example"`
}

type SchemaProp struct {
	Type        string                `json:"type"`
	Ref         string                `json:"$ref"`
	Description string                `json:"description"`
	Properties  map[string]SchemaProp `json:"properties"`
	Items       *SchemaProp           `json:"items"`
	Enum        []any                 `json:"enum"`
	Format      string                `json:"format"`
	Example     any                   `json:"example"`
}

// Operation 单个路径操作：权限点来源 + 接口契约（参数/请求体/响应）
type Operation struct {
	Tags        []string                `json:"tags"`
	OperationID string                  `json:"operationId"`
	Summary     string                  `json:"summary"`
	Description string                  `json:"description"`
	Parameters  []ParamDef              `json:"parameters"`
	RequestBody *RequestBody            `json:"requestBody"`
	Responses   map[string]ResponseDef  `json:"responses"`
}

// ParamDef 参数定义（query/path/header）
type ParamDef struct {
	Name        string      `json:"name"`
	In          string      `json:"in"`
	Required    bool        `json:"required"`
	Description string      `json:"description"`
	Schema      *SchemaProp `json:"schema"`
}

// RequestBody 请求体（仅取 content schema 生成示例）
type RequestBody struct {
	Required bool                   `json:"required"`
	Content  map[string]MediaType   `json:"content"`
}

// ResponseDef 响应定义（取 2xx 的 content schema 生成示例）
type ResponseDef struct {
	Description string                `json:"description"`
	Content     map[string]MediaType  `json:"content"`
}

// MediaType 媒体类型（application/json 等）
type MediaType struct {
	Schema  *SchemaProp `json:"schema"`
	Example any         `json:"example"`
}

// ExtractDataModels 从 OpenAPI components.schemas 提取数据模型候选（表 + 字段）
// 供能力声明 data_model 推断；无 schemas 时返回空（owner 手写兜底）
func ExtractDataModels(raw []byte) ([]DataModelCandidate, error) {
	var doc OpenAPIDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, fmt.Errorf("parse openapi schemas: %w", err)
	}
	var out []DataModelCandidate
	for name, schema := range doc.Components.Schemas {
		if schema.Type != "" && schema.Type != "object" {
			continue // 只取对象类型（表）
		}
		fields := make([]string, 0, len(schema.Properties))
		for f := range schema.Properties {
			fields = append(fields, f)
		}
		out = append(out, DataModelCandidate{
			Code:   singularize(strings.ToLower(name)),
			Name:   name,
			Fields: fields,
		})
	}
	return out, nil
}

// DataModelCandidate 数据模型候选
type DataModelCandidate struct {
	Code   string   `json:"code"`
	Name   string   `json:"name"`
	Fields []string `json:"fields"`
}

// ParsedAction 解析出的权限点（规范化）
type ParsedAction struct {
	Code         string // {app}:{resource}:{operation}
	Name         string
	Resource     string
	Operation    string
	Method       string
	Path         string
	Tag          string // 板块
	IsGeneric    bool   // 通用接口路由（/api/v1/{model}）
	ResourceSlot string // 资源槽位名 / "header"
	// 接口契约（v12）：请求示例 / 响应示例（从 OpenAPI parameters/requestBody/responses 生成）
	ReqExample  string `json:"req_example,omitempty"`
	RespExample string `json:"resp_example,omitempty"`
}

// genericQueryKeywords 统一查询入口关键字（经 X-Resource-Type 解析资源类型）
var genericQueryKeywords = map[string]bool{
	"entities": true, "resources": true, "search": true, "query": true,
}

// ParseOpenAPI 解析 OpenAPI 文档 → 规范化权限点
// 幂等：同一 path+method 输出同一 code
// 通用接口（§6.2）：
//   - /api/v1/{model} 资源位置为参数槽位 → 通用路由（PEP 解析路径槽位）
//   - /api/v1/entities 统一查询入口 → 通用路由（PEP 经 X-Resource-Type 头解析）
func ParseOpenAPI(raw []byte, appCode string) ([]ParsedAction, error) {
	var doc OpenAPIDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, fmt.Errorf("parse openapi: %w", err)
	}
	var out []ParsedAction
	for path, ops := range doc.Paths {
		for method, op := range ops {
			operation := methodToOperation(method)
			if operation == "" {
				continue // 忽略非 CRUD 方法
			}
			resource := ""
			isGeneric := false
			slot := ""

			// 通用接口检测（§6.2）：
			// ① 统一查询入口（/api/v1/entities）→ 经 X-Resource-Type 头解析
			if kw := lastSegment(path); kw != "" && genericQueryKeywords[kw] {
				isGeneric = true
				slot = "header"
				resource = kw
			} else if s, kind, ok := genericSlot(path); ok {
				// ② 资源位置为参数槽位（/api/v1/{model}、/api/v1/{model}/{id}）
				isGeneric = true
				slot = s
				resource = "*"
				if kind == "collection" && operation == "read" {
					operation = "list" // GET /api/v1/{model} = 集合 → list
				}
			} else {
				resource = resourceFromPath(path)
			}
			if resource == "" {
				continue
			}
			// 通用接口：code 用槽位名（cmdb:model:list）；统一查询入口用关键字（cmdb:entities:list）
			codeRes := resource
			if isGeneric && slot != "header" {
				codeRes = slot
			}
			// 集合与详情区分（确定性）：GET 集合路径（无 {param}）→ list 操作，
			// 避免与详情 GET 生成同一 code 互相覆盖
			if !isGeneric && strings.EqualFold(method, "GET") && !strings.Contains(path, "{") {
				operation = "list"
			}
			// 统一查询入口 GET（/api/v1/entities）是集合语义 → list
			if isGeneric && slot == "header" && operation == "read" {
				operation = "list"
			}
			name := op.Summary
			if name == "" {
				name = op.OperationID
			}
			tag := ""
			if len(op.Tags) > 0 {
				tag = op.Tags[0]
			}
			out = append(out, ParsedAction{
				Code:         fmt.Sprintf("%s:%s:%s", appCode, codeRes, operation),
				Name:         name,
				Resource:     resource,
				Operation:    operation,
				Method:       strings.ToUpper(method),
				Path:         path,
				Tag:          tag,
				IsGeneric:    isGeneric,
				ResourceSlot: slot,
				ReqExample:   doc.buildReqExample(method, path, op),
				RespExample:  doc.buildRespExample(op),
			})
		}
	}
	return out, nil
}

// genericSlot 检测通用接口路由并返回资源槽位名：
//   - /api/v1/{model}         → (model, collection)  资源位置本身是槽位
//   - /api/v1/{model}/{id}    → (model, detail)      资源槽位 + 实例 id
func genericSlot(path string) (string, string, bool) {
	segs := strings.Split(strings.Trim(path, "/"), "/")
	for len(segs) > 0 && isVersionSegment(segs[0]) {
		segs = segs[1:]
	}
	if len(segs) == 0 {
		return "", "", false
	}
	isSlot := func(s string) bool {
		return strings.HasPrefix(s, "{") && strings.HasSuffix(s, "}") && len(s) > 2
	}
	isIDSlot := func(s string) bool {
		if !isSlot(s) {
			return false
		}
		inner := s[1 : len(s)-1]
		switch strings.ToLower(inner) {
		case "id", "instanceid", "instance_id", "key", "uuid":
			return true
		}
		return false
	}
	last := segs[len(segs)-1]
	// 集合通用路由：资源位置本身是槽位（排除实例 id 槽位）
	if isSlot(last) && !isIDSlot(last) {
		return last[1 : len(last)-1], "collection", true
	}
	// 详情通用路由：资源槽位 + 实例 id（{model}/{id}）
	if len(segs) >= 2 && isSlot(segs[len(segs)-2]) && isIDSlot(last) {
		s := segs[len(segs)-2]
		return s[1 : len(s)-1], "detail", true
	}
	return "", "", false
}

func lastSegment(path string) string {
	segs := strings.Split(strings.Trim(path, "/"), "/")
	for i := len(segs) - 1; i >= 0; i-- {
		if segs[i] != "" {
			return strings.ToLower(segs[i])
		}
	}
	return ""
}

// methodToOperation HTTP 方法 → 操作
func methodToOperation(m string) string {
	switch strings.ToLower(m) {
	case "get":
		return "read"
	case "post":
		return "create"
	case "put", "patch":
		return "update"
	case "delete":
		return "delete"
	default:
		return ""
	}
}

// resourceFromPath 从路径提取资源名（去掉路径参数段 + 复数归一化）
// /api/v1/hosts/{id} → hosts → host；/api/v1/networks → network
func resourceFromPath(path string) string {
	segs := strings.Split(strings.Trim(path, "/"), "/")
	for i := len(segs) - 1; i >= 0; i-- {
		s := segs[i]
		if s == "" || strings.HasPrefix(s, "{") {
			continue
		}
		// 去掉版本前缀段
		if isVersionSegment(s) && i < len(segs)-1 {
			continue
		}
		return singularize(strings.ToLower(s))
	}
	return ""
}

// singularize 简单复数归一化（hosts→host；es 结尾 disks→disk）
func singularize(s string) string {
	if strings.HasSuffix(s, "ies") && len(s) > 3 {
		return s[:len(s)-3] + "y"
	}
	if strings.HasSuffix(s, "ses") {
		return s[:len(s)-2]
	}
	if strings.HasSuffix(s, "s") && len(s) > 1 {
		return s[:len(s)-1]
	}
	return s
}

func isVersionSegment(s string) bool {
	return strings.HasPrefix(s, "v") && len(s) > 1 && s[1] >= '0' && s[1] <= '9'
}

// ---- 接口契约：请求/响应示例生成（v12）----

// buildReqExample 生成请求示例：`METHOD path?query` + 请求体 JSON
func (d *OpenAPIDoc) buildReqExample(method, path string, op Operation) string {
	queries := []string{}
	var body any
	for _, p := range op.Parameters {
		if p.In != "query" {
			continue
		}
		queries = append(queries, p.Name+"="+fmt.Sprint(d.schemaPropExample(p.Schema)))
	}
	if op.RequestBody != nil {
		for _, mt := range op.RequestBody.Content {
			body = d.schemaPropExample(mt.Schema)
			if body != nil {
				break
			}
		}
	}
	var sb strings.Builder
	sb.WriteString(strings.ToUpper(method))
	sb.WriteString(" ")
	sb.WriteString(path)
	if len(queries) > 0 {
		qs := "?" + strings.Join(queries, "&")
		sb.WriteString(qs)
	}
	if body != nil {
		if b, err := json.MarshalIndent(body, "", "  "); err == nil {
			sb.WriteString("\n")
			sb.WriteString(string(b))
		}
	}
	return sb.String()
}

// buildRespExample 生成响应示例：取第一个 2xx 响应的 content schema
func (d *OpenAPIDoc) buildRespExample(op Operation) string {
	for code, resp := range op.Responses {
		if !strings.HasPrefix(code, "2") {
			continue
		}
		for _, mt := range resp.Content {
			ex := d.schemaPropExample(mt.Schema)
			if ex == nil {
				continue
			}
			if b, err := json.MarshalIndent(ex, "", "  "); err == nil {
				return string(b)
			}
		}
	}
	return ""
}

// schemaPropExample Schema → 示例值（$ref 解引用 / object 递归 / array / 标量默认）
func (d *OpenAPIDoc) schemaPropExample(s *SchemaProp) any {
	if s == nil {
		return nil
	}
	if s.Ref != "" {
		return d.schemaNamedExample(s.Ref)
	}
	switch s.Type {
	case "object":
		obj := map[string]any{}
		for f, prop := range s.Properties {
			obj[f] = d.schemaPropExample(&prop)
		}
		return obj
	case "array":
		if s.Items != nil {
			return []any{d.schemaPropExample(s.Items)}
		}
		return []any{}
	case "string":
		if len(s.Enum) > 0 {
			return s.Enum[0]
		}
		if s.Example != nil {
			return s.Example
		}
		if s.Format == "date-time" {
			return "2026-01-01T00:00:00Z"
		}
		return "string"
	case "integer", "number":
		if s.Example != nil {
			return s.Example
		}
		return 0
	case "boolean":
		if s.Example != nil {
			return s.Example
		}
		return true
	}
	return nil
}

// schemaNamedExample 按组件 schema 名生成示例（$ref 解引用）
func (d *OpenAPIDoc) schemaNamedExample(ref string) any {
	name := strings.TrimPrefix(ref, "#/components/schemas/")
	sub, ok := d.Components.Schemas[name]
	if !ok {
		return nil
	}
	// SchemaDef → SchemaProp 桥接
	prop := schemaDefToProp(&sub)
	return d.schemaPropExample(prop)
}

// schemaDefToProp SchemaDef → SchemaProp（统一示例生成入口）
func schemaDefToProp(s *SchemaDef) *SchemaProp {
	if s == nil {
		return nil
	}
	return &SchemaProp{
		Type:        s.Type,
		Ref:         s.Ref,
		Description: "",
		Items:       s.Items,
		Enum:        s.Enum,
		Format:      s.Format,
		Example:     s.Example,
		Properties:  s.Properties,
	}
}
