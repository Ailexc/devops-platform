package authz

// CasbinModel RBAC + domain 模型
// 主体 key：u:{user_id} / g:{group_id} / r:{role_code} / s:{client_id}
// 对象 key：权限点 code（如 cmdb:host:create），支持 "*" 通配
// pid：策略 ID，用于回查 ABAC conditions（自研策略模型层在 Go 中求值）
// 注意：不用 keyMatch2 —— 权限点 code 含 ":"，keyMatch2 会将其当路径参数通配，
//       导致 cmdb:host:create 误匹配 cmdb:host:read
const CasbinModel = `
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act, eft, pid

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow)) && !some(where (p.eft == deny))

[matchers]
m = g(r.sub, p.sub) && r.dom == p.dom && (r.obj == p.obj || p.obj == "*") && (r.act == p.act || p.act == "*")
`
