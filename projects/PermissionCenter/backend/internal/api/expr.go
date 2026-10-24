package api

import (
	"fmt"
	"strings"

	"github.com/google/cel-go/cel"
	"github.com/xcy/permission-center/internal/model"
)

// buildConditionCEL 将 v12 范围字段类型操作符转换为可落库的 CEL 条件（D2：真解析；1.5 判定=CheckRow 对权威行求值）
// demo 文案（field contains "v" / field !in [...]）→ 真实 CEL（field.contains("v") / !(field in [...])）
func buildConditionCEL(field, op, value string, values []string) (string, error) {
	quoted := func(vs []string) (string, error) {
		out := make([]string, 0, len(vs))
		for _, v := range vs {
			if v == "" {
				continue
			}
			out = append(out, fmt.Sprintf("%q", v))
		}
		if len(out) == 0 {
			return "", fmt.Errorf("op %q 需要至少一个值", op)
		}
		return strings.Join(out, ", "), nil
	}
	switch op {
	case "==", "!=":
		if value == "" {
			return "", fmt.Errorf("op %q 需要值", op)
		}
		return fmt.Sprintf("%s %s %q", field, op, value), nil
	case "in":
		vs := values
		if value != "" {
			vs = append([]string{value}, values...)
		}
		q, err := quoted(vs)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("%s in [%s]", field, q), nil
	case "!in":
		q, err := quoted(values)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("!(%s in [%s])", field, q), nil
	case "contains", "startsWith":
		if value == "" {
			return "", fmt.Errorf("op %q 需要值", op)
		}
		return fmt.Sprintf("%s.%s(%q)", field, op, value), nil
	}
	return "", fmt.Errorf("unsupported op %q", op)
}

// validateCEL 用 cel-go 真解析校验 CEL 表达式语法（P0 即真解析，D2 定案）
// 字段标识符未声明时仅做语法解析（类型检查由落库侧声明约束）
func validateCEL(expr string) error {
	if strings.TrimSpace(expr) == "" {
		return nil
	}
	env, err := cel.NewEnv()
	if err != nil {
		return err
	}
	ast, iss := env.Parse(expr)
	if iss != nil && iss.Err() != nil {
		return fmt.Errorf("CEL 语法错误: %v", iss.Err())
	}
	if ast == nil {
		return fmt.Errorf("CEL 解析失败")
	}
	return nil
}

// scopeVariableContext variable 类型运行时解析：解析对象 = grantee（权限作用主体），
// applicant（权限申请主体）仅为代理申请，不代表权限主体。Phase 6 授权生效/请求校验时由 PDP 注入。
func scopeVariableContext(variable, granteeType, granteeName string) string {
	switch variable {
	case model.VarCurrentUser:
		if granteeType == model.GranteeApp {
			return granteeName // client:xxx
		}
		return granteeName
	case model.VarCurrentOrg:
		return "org:" + granteeName
	case model.VarCurrentGroup:
		return "group:" + granteeName
	case model.VarCurrentAccount:
		return "account:" + granteeName
	}
	return variable
}

// applyScenarioParam T6 场景参数联动（§4.2 升级一，纯函数可单测）：
//   - selections 值位置 "$key" 引用 → 从 scenarioParams 解析（一次选定，全域同值=结构防错位）；
//     解析值回写 sel——调用方 content/审批视图直接可见解析后值；
//   - shared 联动模式服务端钉子：条件 field 与场景参数 key 同名的域禁填字面值，只认 "$key"
//     引用——前端被绕过也错不了位（"结构上不可能错位"的服务端半边）。
func applyScenarioParam(preset map[string]any, sel map[string]any, optField, modelCode string, scenarioParams map[string]any) error {
	resolveRef := func(v string) (string, error) {
		if !strings.HasPrefix(v, "$") {
			return v, nil
		}
		key := strings.TrimPrefix(v, "$")
		rv, ok := scenarioParams[key]
		if !ok || rv == nil || strings.TrimSpace(anyString(rv)) == "" {
			return "", fmt.Errorf("场景参数 %q 未提供（联动模式只选一次）", key)
		}
		return anyString(rv), nil
	}
	// shared 防错位：field 命中场景参数 key → 禁字面值
	if lm, _ := preset["param_linkage"].(string); lm == "shared" {
		paramKeys := map[string]bool{}
		if sps, ok := preset["scenario_params"].([]any); ok {
			for _, raw := range sps {
				if sp, ok := raw.(map[string]any); ok {
					if k, _ := sp["key"].(string); k != "" {
						paramKeys[k] = true
					}
				}
			}
		}
		if paramKeys[optField] {
			lit := anyString(sel["selectedValue"])
			if lit == "" {
				vs := anyStrings(sel["selectedValues"])
				if len(vs) > 0 {
					lit = vs[0]
				}
			}
			if lit != "" && !strings.HasPrefix(lit, "$") {
				return fmt.Errorf("联动模式：%s 域条件字段 %q 绑定场景参数——值须用 \"$%s\" 引用（防域间错位），禁填字面值", modelCode, optField, optField)
			}
		}
	}
	if sv, ok := sel["selectedValue"].(string); ok && sv != "" {
		rv, err := resolveRef(sv)
		if err != nil {
			return err
		}
		sel["selectedValue"] = rv
	}
	if svs := anyStrings(sel["selectedValues"]); len(svs) > 0 {
		// 回写 []any 形态（下游 anyStrings 只吃 []any——写 []string 会被静默丢值）
		out := make([]any, 0, len(svs))
		for _, v := range svs {
			rv, err := resolveRef(v)
			if err != nil {
				return err
			}
			out = append(out, rv)
		}
		sel["selectedValues"] = out
	}
	return nil
}
