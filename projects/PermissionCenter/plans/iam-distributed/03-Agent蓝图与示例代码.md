# 03 · Agent 蓝图与示例代码

> 三态标注：【已实装】/【设计定稿】/【演进项】。协议字段引用 `docs/SDK设计与代码示例-Go.md` §1.1 与接入手册 §5，本文写**实现蓝图与示例代码**。
> 铁律回顾：Agent **只算不算数**——不查数据源、不发业务外呼、不持有数据凭证；fail-closed；last-known-good。

## 1. Agent 内部结构（五件）

```
┌─────────────────────────── iam-agent（独立容器）───────────────────────────┐
│                                                                            │
│  ① BundleManager   轮询 GET /v1/bundles/{app}（app 凭证）                    │
│                    → 校验签名/revision → 原子激活（整包换入）                │
│                    → 失败保留 last-known-good                               │
│  ② RuleStore       内存规则表（接口级动作 + 四形态数据范围 + 组成员关系）      │
│                    读多写少，RWMutex；激活=指针整体换入，判定不阻塞           │
│  ③ Evaluator       接口级：动作命中（原 Casbin 快照语义）                    │
│                    数据级四形态求值（§3）——纯内存/µs 级                     │
│  ④ HTTP 端点       /v1/check · /v1/filter · /v1/manifest · /healthz（仅内网）│
│  ⑤ AuditBuffer     决策记录环形缓冲 → 批量 POST /v1/decisions（异步、可丢注记）│
└────────────────────────────────────────────────────────────────────────────┘
```

版本沿革【已实装】：现 iam-agent 已承载接口级 Casbin 快照判定（bundle 拉取/原子激活/上报骨架在）；本轮 = 补 ② 的数据范围字段、③ 的数据级求值器、`/v1/manifest`、⑤ 批量回传。

## 2. Bundle 拉取与原子激活（示例代码）

```go
// bundle.go —— 拉包循环：轮询 → 校验 → 原子换入；失败保留 last-known-good
type BundleManager struct {
	client   *http.Client
	base     string // 中心地址
	appID    string
	secret   string
	store    atomic.Pointer[RuleStore] // 指针整体换入 = 判定零阻塞
	lastGood *RuleStore
}

func (m *BundleManager) Run(ctx context.Context, every time.Duration) {
	t := time.NewTicker(every)
	defer t.Stop()
	m.pull(ctx) // 启动即拉
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			m.pull(ctx)
		}
	}
}

func (m *BundleManager) pull(ctx context.Context) {
	req, _ := http.NewRequestWithContext(ctx, "GET",
		fmt.Sprintf("%s/v1/bundles/%s", m.base, m.appID), nil)
	req.SetBasicAuth(m.appID, m.secret) // 应用凭证（注册时下发）
	resp, err := m.client.Do(req)
	if err != nil || resp.StatusCode != 200 {
		log.Printf("[agent] pull failed: %v（保留 last-known-good，本轮跳过）", err)
		return // ★ 不清空现有包——拉包失败不是判定失败，更不是放行理由
	}
	var b BundleV2
	if err := json.NewDecoder(resp.Body).Decode(&b); err != nil || !verifySignature(b) {
		log.Printf("[agent] bundle invalid/signature mismatch —— 拒收，保留旧包")
		return
	}
	if rs := m.store.Load(); rs != nil && b.Revision <= rs.Revision {
		return // 旧包/重放，不回退
	}
	next := buildRuleStore(b)               // 解析成内存规则表
	m.lastGood = next
	m.store.Store(next)                     // ★ 原子换入
	log.Printf("[agent] bundle rev=%d activated", b.Revision)
}
```

## 3. 数据级求值器（四形态，纯内存——"能不能做"的答案本体）

```go
// evaluator.go —— 判定材料进、结论出；零 I/O
// ★ 条件语言 = 中心 CEL 子集（== / != / in / !in / contains / startsWith，对齐存量 expr.go 白名单）——
//   两种裁决二选一（P0 契约任务）：① 边缘嵌 cel-go 全语义；② 发布期把 CEL 归一化为受限谓词
//   档位入包，**翻译失败=拒发**（防"翻译丢 op = 过度放行"）。变量四枚对齐存量 scopeVariableContext：
//   $user / $org / $group / $account（运行时按请求者解析，带前缀归一化）。
func (e *Evaluator) CheckData(user string, rule Rule, m core.Material) (allow bool, reason string) {
	switch rule.Scope.Kind {
	case "none", "all":
		return true, ""
	case "instance_set":
		return rule.Scope.IDs.Has(m.ID), "no_matching_scope"
	case "condition", "variable":
		return evalPredicate(rule.Scope.Predicate, m.Attributes, e.varCtx(user)), "no_matching_scope"
	case "dimension":
		// 点判 = 等价谓词求值；列表 = 范围声明交 SDK 下推预过滤，**行内维度字段仍过本求值器二次判**
		// ——下推只是性能优化，正确性裁决永远在 Agent（"点判与列表判一致"进契约测试，M4 修订）
		return evalPredicate(dimToPredicate(rule.Scope), m.Attributes, e.varCtx(user)), "no_matching_scope"
	case "relation": // ⚠️ 关系式=预留形态：材料在中心关系图，边缘不判 → 回源档（05 边界）
		return false, "relation_scope_requires_center"
	}
	return false, "unknown_scope"
}

// evalPredicate：谓词 {field, op, value} 对属性求值；**缺 key = 拒**（fail-closed）
// ★ 改向校验（S4 修订）：调用方先 merge——PATCH 部分更新 = merge(旧属性, changes) 后对合并结果求值，
//   "把 host 改到没权限的账号下"即被拒；批量 Updates（无实体在手）须在 Hook 内先取旧属性再 merge
//   （语义在 P0 契约写死：缺字段按旧值合并；谓词引用的字段缺失 = 拒）。
func evalPredicate(p Predicate, attrs map[string]any, vc varCtx) bool {
	v, ok := attrs[p.Field]
	if !ok {
		return false // 缺字段=拒（fail-closed）
	}
	if val, isVar := vc.resolve(p.Value); isVar {
		v = val // 变量（$user/$org/$group/$account）运行时替换
	}
	return compare(v, p.Op, p.Value)
}
```

**关键语义（写进单测）**：集合式=哈希 O(1) 与条件式谓词 O(1) 判定计算同速，差别只在取材（集合式请求自带 ID、条件式要行属性）；**改向校验**（changes 满足谓词）防"把 host 改到没权限的账号下"；fail-closed——rule 缺失/未知形态/求值异常一律 deny。

## 4. HTTP 端点（示例骨架）

```go
// endpoints.go —— 仅监听内网（AGENT_ADDR 默认 :9090，不映射宿主口）
mux.HandleFunc("/v1/check", func(w http.ResponseWriter, r *http.Request) {
	var req core.CheckRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeDeny(w, "bad_request") // ★ 协议错误=拒
		return
	}
	rs := m.store.Load()
	if rs == nil {
		writeDeny(w, "no_bundle") // ★ 无包=拒（fail-closed）；启动窗口的可用性账见 05 风险 M 行
		return                       //   （healthz 区分 starting/ready + 迁移期回源过渡档），不是"属预期"
	}
	// ① 接口级（包内存）
	if !rs.AllowsAction(req.User, req.Action) {
		writeDeny(w, "no_matching_action")
		return
	}
	// ② 数据级：**有数据范围就必须有材料——缺材料=拒（data_missing），绝不跳过判定**（S1 修订）
	rule := rs.RuleFor(req.Action)
	if req.Operation != "create" && rule.HasDataScope() {
		if req.Attributes == nil {
			writeDeny(w, "data_missing") // ★ 材料缺失=判定失败=拒；把信任外包给被判定方=穿透
			return
		}
		merged := mergeAttrs(req.Attributes, req.Changes) // ★ 改向校验：合并新值后求值（S4）
		allow, reason := e.CheckData(req.User, rule, core.Material{ID: req.InstanceID, Attributes: merged})
		if !allow {
			writeDeny(w, reason)
			return
		}
	}
	audit.Push(req) // 异步批量回传（不阻塞判定）
	writeAllow(w)
})
// /v1/filter 同构：rows 进 → 逐行 CheckData → allowed_ids 出
// /v1/manifest：返回本应用声明（路由映射/QueryDecl/范围）——SDK 启动时读
// /healthz：进程存活（仅内网）
```

## 5. 决策回传（⑤ AuditBuffer）

- 环形缓冲（如 10k 条）+ 每 N 条/每 T 秒批量 `POST /v1/decisions`；**溢出策略两档**（M7 修订）：默认本地磁盘溢写（丢弃降为异常），资源受限环境退"丢最旧 + 计数"——丢弃窗口必须能通过告警圈定时段（合规口径），判定绝不因回传阻塞；
- 中心侧聚合为决策日志视图（"谁在何时被怎么判"**尽力查全**）——分布式后审计集中化，但不承诺"无损全量"（边界表措辞）。

## 6. 契约测试（P2 验收，6 条全绿才发版）

1. 接口级：包内无该动作 → deny；有 → allow；
2. 数据级集合式：ID 在/不在清单各一次；
3. 数据级条件式：属性命中/不命中 + **改向越界被拒**（changes 把 owner 改到范围外 → deny）+ **仅带变更字段的 PATCH**（merge 后求值）+ 批量 Updates（无实体 → Hook 内取旧属性再判）；
4. fail-closed 五连：无包、包损坏、未知 scope 形态、**缺判定材料（data_missing）**、谓词缺字段 → 一律 deny（reason 可区分）；
5. last-known-good：新包拉取失败/校验错 → 继续用旧包判定；旧 revision 重放被拒；
6. **维度式一致性**：同一资源点判与列表判结果一致（下推预过滤 + 行内二次判）；
7. 条件语言一致性：CEL 归一化档位样本（含 contains/!in）边缘求值与中心求值结果一致；
8. 性能基线：单次 check（含数据级）本地 < 1ms（P99），bundle 激活不阻塞在途判定。

## 7. 依赖与部署

- 依赖：http 客户端 + Casbin 库（接口级）+ **cel-go（若 P0 裁决①：边缘全语义求值；裁决②则不引）**——**不引任何数据源驱动**（铁律）；
- 部署：同镜像双入口延续（`command: ["iam-agent"]`），env 见接入手册 §2.3；
- 升级：Agent 独立发版，与中心兼容矩阵随发行说明。
