# OpenFGA 条件表达式（CEL）能力对照 · 学习/面试知识文档

> 关联：`plans/能力包v12执行计划书.md` §4.7
> 定位：产品内**不提供表达式手册弹窗**；本文件沉淀「OpenFGA 支持多少种、我们支持多少种、如何转换」，供学习与面试讲解。

## 1. 一句话结论

v12 通过**范围字段类型系统**（6 种表单类型）暴露 OpenFGA CEL 的**安全子集**：owner 配置「字段 + 操作符 + 选项」，applicant 只做选择/输入，**表达式一律由系统生成并在后端用 cel-go 真解析校验**（D2），用户不接触语法、无注入面。

## 2. 能力对照表

| OpenFGA/CEL 能力 | v12 系统暴露 | 表单类型 | 转换规则 |
|------------------|--------------|----------|----------|
| `==` / `!=` | ✅ | select / variable / input | `field == "value"` |
| `in` / `!in` | ✅ | multi_select（D6：仅 in/!in） | `field in ["a","b"]` → 落库 `field in ["a", "b"]`；`!in` 落库为 `!(field in [...])` |
| 字符串方法 `startsWith` / `contains` | ✅ | input | demo 文案 `field startsWith "x"` → 落库 `field.startsWith("x")` / `field.contains("x")` |
| 数值比较 `>=` / `<=` | ❌ 本期不暴露 | — | v10 曾有，v12 移除；需要时用 input + `==`，或留待 P2 扩展 |
| 逻辑组合 `&&` / `||` / `!` | ❌ UI 不暴露（单条件选择） | — | 多模型/多条件写入时由后端自动组合 |
| 实例级关系（tuple） | ✅ | instance | `(host:web-01, reader, client:xxx)` 走 OpenFGA 关系写入通道 |
| 运行时变量 | ✅ | variable | 解析对象 = **grantee（权限作用主体）**，PDP 注入（见 §3） |
| 手写表达式 | ❌ 已移除 | — | 一律系统生成 + cel-go 真解析校验 |

## 3. variable 运行时解析（重点）

**双主体**：`grantee` = 权限作用主体（用户/组织/自建组/程序），`applicant` = 权限申请主体（人，代理申请）。

| 变量 | 解析对象（= grantee） | 示例 |
|------|----------------------|------|
| `@currentUser` | grantee 为用户 → 该用户；grantee 为程序 → `client:xxx` | `owner_id == "@currentUser"` |
| `@currentOrg` | grantee 组织路径 | `owner_dept == "@currentOrg"` |
| `@currentGroup` | grantee 自建组 | `group_id == "@currentGroup"` |
| `@currentAccount` | grantee 云账号 | `account_id == "@currentAccount"` |

申请端展示当前登录人（applicant）仅为示意，**不代表解析对象**。

## 4. 面试讲解要点

1. **Zanzibar 条件授权**：OpenFGA 在 relation 上挂 condition（CEL），把「数据级过滤」从策略文案提升为可执行的条件；
2. **复杂度收敛**：完整 CEL 语言 → 6 种表单类型的安全子集 → 零学习成本、零注入风险；
3. **真解析闭环**：`cel-go` 解析校验生成的每条条件（P0 即真解析，不做白名单过渡）；
4. **凭证与授权分离**：接入申请签发凭证（一次），能力包申请追加 scope（多次），JWT 每次按已授权 scopes 发放；
5. **grantee 优先**：variable 运行时按权限作用主体解析，而不是按申请人解析——程序身份场景尤其关键。
