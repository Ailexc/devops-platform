// Package openfga OpenFGA 客户端适配（实例级关系引擎，CNCF/Zanzibar）
package openfga

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// Client 轻量 HTTP 客户端（不引入 SDK，展示对 REST API 的理解）
type Client struct {
	baseURL string
	storeID string
	client  *http.Client
}

func NewClient(addr string) *Client {
	return &Client{baseURL: "http://" + addr, client: &http.Client{Timeout: 5 * time.Second}}
}

// EnsureStore 幂等创建 store（按 name 查已有，避免重复建）
func (c *Client) EnsureStore(ctx context.Context, name string) error {
	// 列出现有 store（响应为 {"stores":[...]}，注意分页）
	var list struct {
		Stores []struct {
			ID   string `json:"id"`
			Name string `json:"name"`
		} `json:"stores"`
	}
	if err := c.do(ctx, http.MethodGet, "/stores", nil, &list); err == nil {
		for _, s := range list.Stores {
			if s.Name == name {
				c.storeID = s.ID
				return nil
			}
		}
	}
	var out struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	}
	if err := c.do(ctx, http.MethodPost, "/stores", map[string]any{"name": name}, &out); err != nil {
		return err
	}
	c.storeID = out.ID
	return nil
}

// TypeDef 授权模型类型定义（含 metadata：OpenFGA 校验要求声明可分配类型）
type TypeDef struct {
	Type      string                    `json:"type"`
	Relations map[string]map[string]any `json:"relations,omitempty"`
	Metadata  map[string]any            `json:"metadata,omitempty"`
}

// EnsureModel 幂等写入授权模型（模型多版本由 OpenFGA 原生支持——版本化白嫖）
func (c *Client) EnsureModel(ctx context.Context, defs []TypeDef) error {
	// 已有模型则跳过
	var models struct {
		AuthorizationModels []struct {
			ID string `json:"id"`
		} `json:"authorization_models"`
	}
	if err := c.do(ctx, http.MethodGet, fmt.Sprintf("/stores/%s/authorization-models", c.storeID), nil, &models); err == nil && len(models.AuthorizationModels) > 0 {
		return nil
	}
	body := map[string]any{"schema_version": "1.1", "type_definitions": defs}
	var out map[string]any
	return c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/authorization-models", c.storeID), body, &out)
}

// WriteTuple 写关系（user 可为 userset，如 group:10#member）
// 幂等：tuple 已存在视为成功（OpenFGA 不支持天然幂等写）
func (c *Client) WriteTuple(ctx context.Context, user, relation, object string) error {
	err := c.write(ctx, []map[string]string{{"user": user, "relation": relation, "object": object}})
	if err != nil && strings.Contains(err.Error(), "already existed") {
		return nil
	}
	return err
}

// DeleteTuple 删关系（孤儿清理）
func (c *Client) DeleteTuple(ctx context.Context, user, relation, object string) error {
	body := map[string]any{"deletes": map[string]any{"tuple_keys": []map[string]string{{"user": user, "relation": relation, "object": object}}}}
	var out map[string]any
	return c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/write", c.storeID), body, &out)
}

// ReadTuplesByObject 按对象读关系元组（OpenFGA read API 带 object 过滤）——
// 实例删除级联清理的前置查询（清单 A5a：已删实例的全部关系必须逐条删除，幽灵授权=判多红线）
func (c *Client) ReadTuplesByObject(ctx context.Context, object string) ([]RelationTuple, error) {
	body := map[string]any{"tuple_key": map[string]string{"object": object}}
	var out struct {
		Tuples []struct {
			Key RelationTuple `json:"key"`
		} `json:"tuples"`
	}
	if err := c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/read", c.storeID), body, &out); err != nil {
		return nil, err
	}
	res := make([]RelationTuple, 0, len(out.Tuples))
	for _, t := range out.Tuples {
		res = append(res, t.Key)
	}
	return res, nil
}

func (c *Client) write(ctx context.Context, tuples []map[string]string) error {
	body := map[string]any{"writes": map[string]any{"tuple_keys": tuples}}
	var out map[string]any
	return c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/write", c.storeID), body, &out)
}

// Check 单点判断
func (c *Client) Check(ctx context.Context, user, relation, object string) (bool, error) {
	body := map[string]any{"tuple_key": map[string]string{"user": user, "relation": relation, "object": object}}
	var out struct {
		Allowed bool `json:"allowed"`
	}
	if err := c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/check", c.storeID), body, &out); err != nil {
		return false, err
	}
	return out.Allowed, nil
}

// ListObjects 允许对象集
func (c *Client) ListObjects(ctx context.Context, user, relation, objType string) ([]string, error) {
	body := map[string]any{"user": user, "relation": relation, "type": objType}
	var out struct {
		Objects []string `json:"objects"`
	}
	if err := c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/list-objects", c.storeID), body, &out); err != nil {
		return nil, err
	}
	return out.Objects, nil
}

// RelationTuple OpenFGA 关系元组
type RelationTuple struct {
	User     string `json:"user"`
	Relation string `json:"relation"`
	Object   string `json:"object"`
}

// ReadTuples 读取某主体的关系（PIP 身份解析图谱 / 数据级授权关系展示）
// OpenFGA Read API 要求 object 需带类型：按 objTypes 逐个类型读取（object 传 "type:" 通配该类型全部实例）
// 对应 POST /stores/{store}/read {"tuple_key":{"user":...,"object":"host:"}}
func (c *Client) ReadTuples(ctx context.Context, user string, objTypes []string) ([]RelationTuple, error) {
	all := make([]RelationTuple, 0)
	for _, t := range objTypes {
		body := map[string]any{"tuple_key": map[string]string{"user": user, "object": t + ":"}}
		var out struct {
			Tuples []struct {
				Key struct {
					User     string `json:"user"`
					Relation string `json:"relation"`
					Object   string `json:"object"`
				} `json:"key"`
			} `json:"tuples"`
		}
		if err := c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/read", c.storeID), body, &out); err != nil {
			continue // 该类型无关系或不可读，跳过
		}
		for _, tpl := range out.Tuples {
			all = append(all, RelationTuple{User: tpl.Key.User, Relation: tpl.Key.Relation, Object: tpl.Key.Object})
		}
	}
	return all, nil
}

// ReadTypeTuples 读取某类型下的全部关系（object 通配，不限定 user）——数据面图谱用
func (c *Client) ReadTypeTuples(ctx context.Context, objType string) ([]RelationTuple, error) {
	body := map[string]any{"tuple_key": map[string]string{"object": objType + ":"}}
	var out struct {
		Tuples []struct {
			Key struct {
				User     string `json:"user"`
				Relation string `json:"relation"`
				Object   string `json:"object"`
			} `json:"key"`
		} `json:"tuples"`
	}
	if err := c.do(ctx, http.MethodPost, fmt.Sprintf("/stores/%s/read", c.storeID), body, &out); err != nil {
		return nil, err
	}
	all := make([]RelationTuple, 0, len(out.Tuples))
	for _, tpl := range out.Tuples {
		all = append(all, RelationTuple{User: tpl.Key.User, Relation: tpl.Key.Relation, Object: tpl.Key.Object})
	}
	return all, nil
}

// AuthorizationModel 授权模型视图（type 定义，数据面图谱用）
type AuthorizationModel struct {
	ID       string           `json:"id"`
	TypeDefs []map[string]any `json:"type_definitions"`
}

// LatestModel 最新授权模型（type 定义）
func (c *Client) LatestModel(ctx context.Context) (*AuthorizationModel, error) {
	var models struct {
		AuthorizationModels []struct {
			ID              string           `json:"id"`
			TypeDefinitions []map[string]any `json:"type_definitions"`
		} `json:"authorization_models"`
	}
	if err := c.do(ctx, http.MethodGet, fmt.Sprintf("/stores/%s/authorization-models", c.storeID), nil, &models); err != nil {
		return nil, err
	}
	if len(models.AuthorizationModels) == 0 {
		return nil, nil
	}
	last := models.AuthorizationModels[len(models.AuthorizationModels)-1]
	return &AuthorizationModel{ID: last.ID, TypeDefs: last.TypeDefinitions}, nil
}

func (c *Client) do(ctx context.Context, method, path string, body, out any) error {
	var reader io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reader = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, reader)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("openfga %s %s: %w", method, path, err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("openfga %s %s -> %d: %s", method, path, resp.StatusCode, string(raw))
	}
	if out != nil && len(raw) > 0 {
		return json.Unmarshal(raw, out)
	}
	return nil
}
