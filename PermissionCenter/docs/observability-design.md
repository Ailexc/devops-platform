# 系统观测能力设计（2026-08-12）

> 定位：本系统是 Demo 系统，承担「还原工作场景 + 扩展学习 + 演示能力」三重价值。
> 可观测性不是为了监控生产，而是把黑盒化的鉴权链路显性化，供演示与学习。
> 本文件记录 5 项观测改进的接口契约、数据来源与页面入口。

## 总体原则

- 全部挂在 `mg` 组（`/api/v1`，JWT + mgScope），`mgScope` 的 observability 分支已放行
- 数据来源不新增表：全部从现有决策日志 / Redis 缓存 / OpenFGA / bundle 记录聚合
- 只读观测优先；唯一写操作是「清空决策缓存」（排障用）

## 1. 决策缓存工作台

**页面**：`/observability/cache`（`frontend/src/views/ObsCache.vue`）
**接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/debug/cache` | dec/pset 键数 + 累计决策 + 命中率 + 键明细 |
| POST | `/api/v1/debug/cache/clear` | 清空 `authz:dec:*`（策略变更不生效时一键失效） |

**数据来源**：
- `store/cache.go` 新增 `ScanPattern(pattern, limit)`、`CountPattern(pattern)`
- 决策命中率：`authz/checker.go` writeLog 在 PEP 里打 `pep["from"]`（`cache`/`remote`），按 `pep->>'from'` 聚合

**缓存键格式**：`authz:dec:{sub}:{app}:{action}`，值 `1|pid1,pid2`（allow）/ `0|`（deny）
**命中率**：`pep->>'from'='cache'` 条数 / 总决策

## 2. 鉴权指标面板

**页面**：`/observability/metrics`（`ObsMetrics.vue`）
**接口**：GET `/api/v1/debug/metrics`

**返回结构**：
```json
{
  "summary": { "total": 461, "allow": 334, "deny": 127, "source_dist": {"cache": 12, "remote": 449},
               "p50": 1, "p90": 10, "p95": 17 },
  "trend": [ { "hour": "2026-08-12 07", "total": 28, "allow": 18, "deny": 10 } ],
  "top_actions": [ { "action": "cmdb:host:read", "count": 243 } ]
}
```

**数据来源**（`store/sync_repo.go`）：
- `DecisionSummary()`：count + `pep->>'from'` 分组 + 延迟百分位（ORDER BY + LIMIT 偏移近似）
- `DecisionTrend(hours)`：`to_char(date_trunc('hour', created_at), 'YYYY-MM-DD HH24')` 按小时分组
- `DecisionByAction(limit)`：按 action 计数 Top N

## 3. OpenFGA 数据面图谱

**页面**：`/observability/ofga`（`ObsOfga.vue`）
**接口**：GET `/api/v1/debug/ofga`

**返回结构**：`{ model_id, type_defs, types, total_tuples, by_type: [{type, count, tuples}] }`
**数据来源**（`openfga/client.go` 新增）：
- `LatestModel(ctx)`：最近授权模型 type 定义
- `ReadTypeTuples(ctx, objType)`：只按对象类型读取全部 tuple（无 user 过滤）

## 4. bundle 内容展开

**页面**：`/observability/agents` → 「策略分发记录」tab（`Agents.vue`）
**接口**：GET `/api/v1/apps/:id/bundles`（`listBundles` 增强）

**新增字段**：
- `policy_preview`：前 20 条策略概要（subject_key / app_code / actions / effect）
- `force_remote`：强制回源动作列表

**UI**：每行「📦 内容 ▸/▾」展开显示策略预览 + 强制回源标签

## 5. Owner 巡检视图

**页面**：`/observability/owners`（`ObsOwners.vue`）
**接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/debug/owners` | `app_owners.remind_count > 0` 展开 owner/应用状态 |
| POST | `/api/v1/owner-check` | 手动触发巡检（已有，owner 失联提醒 + 自动停用） |

**巡检规则**：owner 最近 7 天无活动 → 提醒计数 +1；达 3 次无响应 → 应用自动停用，可由新 owner「认领」恢复。

## 验证记录

- 后端：全部端点 curl 验证通过（cache clear 后 dec 键从 2→0；metrics trend 5 点；ofga model_id + 3 type；owners 触发后 4 条）
- 回归：`bash scripts/demo.sh` 17 步全过
- 前端：浏览器（admin 一键登录）4 页全渲染正常；owner 巡检「手动触发」演示 0→4；bundle v3 展开 5 条策略预览
- 访问入口：侧栏「系统观测」下 4 项 + Agent·分发·同步（bundle 展开）

## 踩坑备忘

1. **DecisionTrend SQL**：`(? || ' hours')::interval`（GORM int 参数）类型不匹配返回空 → 用 `now() - interval '1 hour' * ?`
2. **source_dist 丢行**：GORM 把 SQL NULL 扫进 `string` 静默丢弃该行 → `COALESCE(pep->>'from','')` + 归一空串为 remote，且 **`dist[k] += v` 累加**（`=` 会被真实 remote 组覆盖）
3. **PEP check 路径**：`/v1/authz/check`（az 组，无 `/api/v1` 前缀）+ 头 `X-PEP-Token: pep-shared-secret`；curl 错路径 404 但 `> /dev/null` 吞掉
4. 容器内二进制路径是 `/usr/local/bin/iam-server`（Dockerfile `COPY bin/ /usr/local/bin/`）
