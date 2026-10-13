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
