// Package material v1.5 T2 通用点查取材（方案 §3.1/§3.2/§3.7）
//
// 中心按应用注册的回查地址取【权威行】——行用完即丢，不落库（无新鲜度税）。
// 取材声明三选一的取值在此：
//   - id_path   path.*   → 从路径模板提取（网关链路持有 URI）
//   - id_path   body.*   → 从带体调用的请求体提取（点号/下标路径）
//   - envelope  .meta.x  → 信封字段（创建类"未来的行"，伪造被授权集封顶）
//   - fetch_source       → 绑定字典解参 + 回源（补救档）
//
// 失败语义钉死（§3.2）：查不到=ErrNotFound（deny data_missing）；
// 网络/非 2xx=ErrUnavailable（deny fail-closed，无隐式降级）。
package material

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

var (
	ErrNotFound    = errors.New("material: row not found")      // → deny data_missing
	ErrUnavailable = errors.New("material: source unavailable") // → deny fail-closed
	ErrNoPathID    = errors.New("material: id not in path")     // 声明 path.* 但模板提取不出 → 配置错误 fail-closed
)

// Client 通用点查客户端（短超时：判定链路上点查是唯一外部依赖，快失败早拒）
type Client struct{ hc *http.Client }

func NewClient() *Client {
	return &Client{hc: &http.Client{Timeout: 2 * time.Second}}
}

// FetchRow 按 (model, id) 点查权威行。
// 合同：POST {url} {"model","id"} + X-Perm-Query-Token → 200 {"row":{...}} / 404 / 其余=失败。
func (c *Client) FetchRow(ctx context.Context, url, token, model, id string) (map[string]any, error) {
	if url == "" {
		return nil, fmt.Errorf("%w: 应用未配置回查地址", ErrUnavailable)
	}
	body, _ := json.Marshal(map[string]string{"model": model, "id": id})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("X-Perm-Query-Token", token)
	}
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode == http.StatusNotFound {
		return nil, ErrNotFound
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("%w: HTTP %d", ErrUnavailable, resp.StatusCode)
	}
	var payload struct {
		Row map[string]any `json:"row"`
	}
	if err := json.Unmarshal(raw, &payload); err != nil || payload.Row == nil {
		return nil, fmt.Errorf("%w: 响应缺 row 字段", ErrUnavailable)
	}
	return payload.Row, nil // 行用完即丢：仅在判定内存中参与求值，不写任何存储
}

// ExtractPathParam 从路径模板与实际路径提取参数值。
// template=/disks/{id}、actual=/disks/d-500 → "d-500"；name 指定槽名，找不到时兜底最后一个参数段。
func ExtractPathParam(template, actual, name string) (string, bool) {
	tSegs := strings.Split(strings.Trim(template, "/"), "/")
	aSegs := strings.Split(strings.Trim(actual, "/"), "/")
	if len(tSegs) != len(aSegs) {
		return "", false // 段数不等 = 模板本就不匹配（调用方应先经查表命中）
	}
	lastParam := ""
	for i, t := range tSegs {
		if !strings.HasPrefix(t, "{") {
			continue
		}
		slot := strings.Trim(t, "{}")
		if slot == name || name == "" {
			return aSegs[i], true
		}
		if slot == "id" {
			lastParam = aSegs[i] // 记住具名 id，最终兜底
		} else if lastParam == "" {
			lastParam = aSegs[i]
		}
	}
	if lastParam != "" {
		return lastParam, true
	}
	return "", false
}

// Nested 点号+下标取值：".meta.account" / "meta.account" / "items[0].account"
func Nested(m map[string]any, path string) (any, bool) {
	p := strings.TrimPrefix(strings.TrimSpace(path), ".")
	if p == "" {
		return nil, false
	}
	var cur any = m
	for _, seg := range strings.Split(p, ".") {
		rest := seg
		for {
			key := rest
			idx := -1
			hadIdx := false
			if i := strings.IndexByte(rest, '['); i >= 0 {
				end := strings.IndexByte(rest, ']')
				if end < 0 {
					return nil, false
				}
				key = rest[:i]
				n, err := strconv.Atoi(rest[i+1 : end])
				if err != nil {
					return nil, false
				}
				idx = n
				rest = rest[end+1:]
				hadIdx = true
			}
			if key != "" {
				mm, ok := cur.(map[string]any)
				if !ok {
					return nil, false
				}
				v, ok2 := mm[key]
				if !ok2 {
					return nil, false
				}
				cur = v
			}
			if idx >= 0 {
				arr, ok := cur.([]any)
				if !ok || idx >= len(arr) {
					return nil, false
				}
				cur = arr[idx]
			}
			if !hadIdx || rest == "" {
				break // 纯键段消费完 / 下标后无剩余 → 本段结束
			}
			if !strings.HasPrefix(rest, "[") {
				return nil, false // 段内混入非下标文本（如 a[0]x）
			}
		}
		if cur == nil {
			return nil, false
		}
	}
	return cur, true
}

// LeafKey 信封字段的叶子键名（条件字段名）：.meta.account → account
func LeafKey(path string) string {
	p := strings.Trim(strings.TrimSpace(path), ".")
	if i := strings.LastIndexAny(p, ".["); i >= 0 {
		p = p[i+1:]
		p = strings.Trim(p, "[]")
		p = strings.TrimPrefix(p, "]")
	}
	if i := strings.IndexByte(p, '['); i >= 0 {
		p = p[:i]
	}
	return p
}

// ResolveBind 补救档绑定字典解参（五来源：body/const/ctx/path/query——path/query 由调用方并入 froms）。
// froms 携带非 body 来源（网关链路的 path 参数/带体调用可附带的 query）。
func ResolveBind(bind map[string]any, body map[string]any, froms map[string]map[string]any) (map[string]any, error) {
	out := map[string]any{}
	for key, raw := range bind {
		b, ok := raw.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("bind.%s 形状非法", key)
		}
		from, _ := b["from"].(string)
		switch from {
		case "body":
			k, _ := b["key"].(string)
			v, ok := Nested(body, k)
			if !ok {
				return nil, fmt.Errorf("bind.%s: body 取值 %q 不存在", key, k)
			}
			out[key] = v
		case "const":
			v, ok := b["value"]
			if !ok {
				return nil, fmt.Errorf("bind.%s: const 缺 value", key)
			}
			out[key] = v
		case "ctx":
			k, _ := b["key"].(string)
			if src, ok := froms["ctx"]; ok {
				if v, ok := src[k]; ok {
					out[key] = v
					continue
				}
			}
			return nil, fmt.Errorf("bind.%s: ctx 变量 %q 不存在", key, k)
		case "path", "query":
			k, _ := b["key"].(string)
			if src, ok := froms[from]; ok {
				if v, ok := src[k]; ok {
					out[key] = v
					continue
				}
			}
			return nil, fmt.Errorf("bind.%s: %s.%s 不存在", key, from, k)
		default:
			return nil, fmt.Errorf("bind.%s: from=%q 非法", key, from)
		}
	}
	return out, nil
}

// SubstURL 回源 URL 模板替换：{disk_id} ← bind["disk_id"]
func SubstURL(tmpl string, bind map[string]any) string {
	out := tmpl
	for k, v := range bind {
		out = strings.ReplaceAll(out, "{"+k+"}", fmt.Sprintf("%v", v))
	}
	return out
}

// ResolveFetchURL 补救档回源地址绝对化（§3.7）：
// 支持 "GET /path" 方法前缀（默认 GET）；相对路径以应用回查地址的 origin 为基。
func ResolveFetchURL(raw, base string) (method, u string, err error) {
	method = "GET"
	s := strings.TrimSpace(raw)
	if i := strings.IndexByte(s, ' '); i > 0 {
		head := strings.ToUpper(s[:i])
		switch head {
		case "GET", "POST", "PUT", "PATCH", "DELETE":
			method = head
			s = strings.TrimSpace(s[i+1:])
		}
	}
	if strings.HasPrefix(s, "http://") || strings.HasPrefix(s, "https://") {
		return method, s, nil
	}
	if base == "" {
		return "", "", fmt.Errorf("%w: 相对回源地址缺应用回查基址", ErrUnavailable)
	}
	b, perr := url.Parse(base)
	if perr != nil || b.Scheme == "" || b.Host == "" {
		return "", "", fmt.Errorf("%w: 回查基址非法", ErrUnavailable)
	}
	return method, b.Scheme + "://" + b.Host + s, nil
}

// FetchAny 回源取行（fetch_source 补救档）：200 → {"row":{...}} 或裸 JSON 对象。
// 三态与 FetchRow 一致：404=ErrNotFound、非 200/解析失败=ErrUnavailable（fail-closed）。
func (c *Client) FetchAny(ctx context.Context, method, rawURL, token string) (map[string]any, error) {
	req, err := http.NewRequestWithContext(ctx, method, rawURL, nil)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	if token != "" {
		req.Header.Set("X-Perm-Query-Token", token)
	}
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode == http.StatusNotFound {
		return nil, ErrNotFound
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("%w: HTTP %d", ErrUnavailable, resp.StatusCode)
	}
	var payload struct {
		Row map[string]any `json:"row"`
	}
	if err := json.Unmarshal(raw, &payload); err == nil && payload.Row != nil {
		return payload.Row, nil
	}
	var obj map[string]any
	if err := json.Unmarshal(raw, &obj); err != nil || obj == nil {
		return nil, fmt.Errorf("%w: 响应非 JSON 对象", ErrUnavailable)
	}
	return obj, nil
}
