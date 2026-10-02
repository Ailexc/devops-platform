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
func (e *Evaluator) CheckData(user string, rule Rule, m core.Material,
	changes map[string]any) (allow bool, reason string) {

	switch rule.Scope.Kind {
	case "none": // 无数据范围 → 接口级过了就是全量
		return true, ""
	case "all": // 模型/域全量
		return true, ""
	case "instance_set": // 集合式：清单命中即过（µs 哈希查找）
		return rule.Scope.IDs.Has(m.ID), "no_matching_scope"
	case "condition", "variable": // 条件式/变量式：谓词对单行属性求值
		return evalPredicate(rule.Scope.Predicate, m.Attributes, e.requester(user)), "no_matching_scope"
	case "dimension": // 维度式：列表场景交 SDK 拼条件；点场景等价条件求值
		return evalPredicate(dimToPredicate(rule.Scope), m.Attributes, ""), "no_matching_scope"
	case "relation": // ⚠️ 关系式=预留形态：材料在中心关系图，边缘不判 → 回源（§5 边界）
		return false, "relation_scope_requires_center"
	}
	return false, "unknown_scope"
}

// evalPredicate：{field, op(eq|neq|in|gte), value} → 对属性求值；$requester 运行时替换成请求者
// changes（改的新值）参与"改向"校验：变更后的属性也须满足谓词（防改向越界）
func evalPredicate(p Predicate, attrs, requester string) bool {
	v := attrs[p.Field]
	if p.Value == "$requester" {
		v = requester
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
		writeDeny(w, "no_bundle") // ★ 无包=拒（fail-closed；启动竞态短暂出现属预期）
		return
	}
	// ① 接口级（包内存）
	if !rs.AllowsAction(req.User, req.Action) {
		writeDeny(w, "no_matching_action")
		return
	}
	// ② 数据级（带 attributes 才判；create 免——请求参数即"未来的行"）
	if req.Operation != "create" && req.Attributes != nil {
		allow, reason := e.CheckData(req.User, rs.RuleFor(req.Action), core.Material{ID: req.InstanceID, Attributes: req.Attributes}, req.Changes)
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

- 环形缓冲（如 10k 条）+ 每 N 条/每 T 秒批量 `POST /v1/decisions`；**缓冲满丢最旧并计数**（判定绝不因回传阻塞——审计是尽力而为，决策正确性优先；丢弃数在 healthz 暴露指标）；
- 中心侧聚合为决策日志视图（"谁在何时被怎么判"）——补足分布式后审计集中化。

## 6. 契约测试（P2 验收，6 条全绿才发版）

1. 接口级：包内无该动作 → deny；有 → allow；
2. 数据级集合式：ID 在/不在清单各一次；
3. 数据级条件式：属性命中/不命中 + **改向越界被拒**（changes 把 owner 改到范围外 → deny）；
4. fail-closed：无包、包损坏、未知 scope 形态 → 一律 deny（reason 可区分）；
5. last-known-good：新包拉取失败/签名错 → 继续用旧包判定；旧 revision 重放被拒；
6. 性能基线：单次 check（含数据级）本地 < 1ms（P99），bundle 激活不阻塞在途判定。

## 7. 依赖与部署

- 依赖：仅 redis/http 客户端 + 可选 Casbin 库（接口级）——**不引任何数据源驱动**（铁律）；
- 部署：同镜像双入口延续（`command: ["iam-agent"]`），env 见接入手册 §2.3；
- 升级：Agent 独立发版，与中心兼容矩阵随发行说明。
