package authz

import (
	"strconv"
	"strings"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// T5 列表判定两步之子集校验（方案 §5.2 元组集合语义，v2.1 裁定⑨）：
// 授权范围 = 各策略展开的组合取【集合并】——本维度上：
//   - 无 scope 策略（nil）→ 全量（wildcard，任意值放行）
//   - 条件式且 field==契约参数 → 授权值 = 条件值（单值）
//   - 条件式但 field!=契约参数 → 本维度不受限（wildcard——该策略只约束别的维度）
//   - dimension 式且 dimension==参数 → 授权值 = values 列表；否则 wildcard
//   - 集合式（instance_ids）→ 不覆盖列表维度（勾选实例≠列表范围授权）
//
// 请求值（可逗号多值）必须全部 ∈ 授权集；full=true 时任意值放行。
// 跨策略只并集合、不打散维度重组（S4：投影并集漏洞在单维度退化为值并集，多维组合待契约扩展）。
//
// 返回：full=任意值放行；values=授权值集合（nil 且 !full = 无任何授权 → 全拒）。
// AuthorizedScopeValues 按主体命中策略集合计算契约参数维度上的授权值。
// 纯函数核心 = ScopeValuesOf（策略切片入参，便于无 DB 单测）。
func AuthorizedScopeValues(matchedPids []string, pol *store.PolicyRepo, resource, param string) (full bool, values map[string]bool) {
	ps := make([]model.Policy, 0, len(matchedPids))
	for _, pid := range matchedPids {
		if strings.HasPrefix(pid, "role:") || strings.HasPrefix(pid, "gp:") {
			continue
		}
		id, err := strconv.ParseUint(pid, 10, 64)
		if err != nil {
			continue
		}
		if p, err := pol.ByID(id); err == nil {
			ps = append(ps, *p)
		}
	}
	return ScopeValuesOf(ps, resource, param)
}

// ScopeValuesOf 纯函数核心（T5 单测目标）
func ScopeValuesOf(ps []model.Policy, resource, param string) (full bool, values map[string]bool) {
	values = map[string]bool{}
	for i := range ps {
		p := &ps[i]
		if p.Status != model.PolicyActive {
			continue
		}
		if p.ResourceScope == nil {
			return true, nil // 无数据范围 → 全量
		}
		if sc := scopeModelCode(p); sc != "" && sc != resource {
			continue // 其他数据域的策略不覆盖本域列表
		}
		if instSet := p.ResourceScope["instance_ids"]; instSet != nil {
			continue // 集合式（勾选实例）不覆盖列表维度
		}
		if cond, ok := p.ResourceScope["condition"].(map[string]any); ok {
			f, _ := cond["field"].(string)
			if f != param {
				full = true // 只约束别的维度 → 本维度不受限
				continue
			}
			op, _ := cond["op"].(string)
			if op != "eq" {
				full = true // 非等值谓词无法收敛为值集合 → 按不受限处理（宽松侧由契约测试兜住）
				continue
			}
			values[normVal(cond["value"])] = true
			continue
		}
		if dim, ok := p.ResourceScope["dimension"].(string); ok {
			if dim != param {
				full = true
				continue
			}
			if vals, ok := p.ResourceScope["values"].([]any); ok {
				for _, v := range vals {
					values[normVal(v)] = true
				}
			}
			continue
		}
		// 未知 scope 形态（relation 预留）→ 不覆盖本维度
	}
	return full, values
}

// normVal 值归一（JSONB 数字 → 无尾小数字符串；统一小写比较面外的原样）
func normVal(v any) string {
	switch t := v.(type) {
	case string:
		return t
	case float64:
		if t == float64(int64(t)) {
			return strconv.FormatInt(int64(t), 10)
		}
		return strconv.FormatFloat(t, 'f', -1, 64)
	default:
		return ""
	}
}

// SubsetCheck 请求值集合 ⊆ 授权集（full=任意放行）。
// 返回首个越权值（空=通过）；values 为空且 !full = 无授权 → 首值即越权。
func SubsetCheck(requested []string, full bool, values map[string]bool) (string, bool) {
	for _, v := range requested {
		if full || values[v] {
			continue
		}
		return v, false
	}
	return "", true
}

// ParseScopeParamList query 值 → 请求值集合（逗号分隔多值；空白剔除）
func ParseScopeParamList(raw string) []string {
	out := []string{}
	for _, s := range strings.Split(raw, ",") {
		if s = strings.TrimSpace(s); s != "" {
			out = append(out, s)
		}
	}
	return out
}
