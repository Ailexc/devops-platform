# deny 治理规范（企业规范）

> 版本：v1.0（2026-10-17）｜状态：已成文，机器校验已实装（T8）｜权威源：方案 §4.4
> 适用：权限中心全部应用的显式禁止（黑名单）策略；配套 demo 场景 23 可复现全链

## 1. 定位：deny 是什么、不是什么

| | 说明 |
|---|---|
| **是什么** | `effect=deny` 的策略条目——**显式禁止**：指定主体对指定动作**即使有 allow 也拒** |
| **判定语义** | Casbin **deny-overrides**：`allow && !deny`——任一 deny 命中，再多 allow 也拒（一票否决） |
| **不是什么** | ❌ 不是"删除授权"（deny 不动 allow 策略，解除 deny 后 allow 自然恢复——**授权账本不变**）<br>❌ 不是回收的替代品（想收回授权 → 走回收 revoke；deny 是"保留授权但禁止执行"的冻结语义）<br>❌ 不是默认机制（系统底色=白名单 deny-by-default；deny 是白名单之上的显式覆盖层） |

**典型场景**：安全事件响应（临时封禁读取/操作权限，事件处置完解除）；合规冻结（人员离职交接期冻结权限）；高危动作临时管制。

## 2. 治理三规矩（机器校验已实装——能强制的绝不靠自觉）

deny 比 allow 危险：allow 错了多发一条权限，deny 错了**一票否决一片授权**（误伤面=被禁主体的全部相关 allow）。因此 deny 走更严的门：

### 规矩① 精确性：必须显式 action_ids，禁通配 deny

- **校验点**：`POST /api/v1/policies`（effect=2）`action_ids` 为空 → **400 拒**
- **理由**：deny-overrides 一票否决——通配 deny（不指定动作）会误伤该主体的**全部**授权，这不是封禁是事故
- **要求**：deny 必须逐动作显式列出被禁动作码。想封"整个应用"？那说明该主体不该持有该应用的任何权限——走**回收**，不是 deny

### 规矩② 同一审批链：与授权同权重留痕

- **机制**：deny 走 grant 方向的申请-审批流（`POST /api/v1/policies` → 申请单 → 审批）——**与授权完全同一审批链、同一审计账本**，无直授后门
- **被禁方知情**：审批链含被授权方确认节点（让他知道、让他同意）——封禁不是暗杀
- **reason 必填**：`reason` 为空 → **400 拒**。"为什么禁"与"为什么给"同权重留痕——审计要能回答"这条封禁是谁批的、为什么"
- **SoD**：申请人不能审批自己的 deny 单（与授权同硬约束）

### 规矩③ 配额 + 审计

- **配额**：单应用 active deny 策略上限 **20 条**（`DenyPolicyQuotaPerApp`）——超限 400 拒，先清理/归档存量 deny
- **理由**：失控的 deny 面比失控的 allow 面更危险（误伤全部授权）；配额逼着"用完即清"，防 deny 堆积成永久封锁层
- **审计**：deny 的创建/审批/生效/回收全链审计留痕（`policy.grant.request` / `request.approve` / `grant.revoke.*`），策略行关联 `request_id`——**每条 deny 都能指认到申请单、审批人与理由**

## 3. 生命周期

```
发起（owner，显式 action_ids + reason 必填）
  → 审批（grant 同链：被禁方确认 + owner 复核；SoD）
  → 生效（落 deny 策略，deny-overrides 立即一票否决）
  → 解除（回收 revoke：owner/grantee 发起 → owner 审批 → 策略置 0）
  → allow 自然恢复（原授权策略未动，解除即复通——无需重新授权）
```

**解除≠恢复授权**：解除只是移除覆盖层，原有 allow 策略一直在账本上——这是"冻结语义"的直接推论。

## 4. 机器校验清单（实现落点）

| 校验 | 时机 | 行为 | 实现 |
|---|---|---|---|
| deny 无 action_ids | 提单（createPolicy） | 400 拒 | `handler_policy.go` deny 治理块 |
| deny 无 reason | 提单 | 400 拒 | 同上 |
| 单应用 deny 配额 ≥20 | 提单 | 400 拒 | 同上（`DenyPolicyQuotaPerApp`） |
| effect 传播 | 审批通过落策略 | content.effect=2 → 落 deny 策略 | `grantFromRequest` polEffect（T8 修复：此前硬编码 allow） |
| deny-overrides | 判定 | `allow && !deny` | Casbin model.conf `e` 表达式 |

## 5. 反例（不要这么做）

| 反例 | 为什么错 | 正确做法 |
|---|---|---|
| 通配 deny 封整个应用 | 误伤全部 allow——一票否决面失控 | 回收（revoke）该主体的授权 |
| deny 不填 reason | 审计断链——半年后没人知道为什么封 | 理由必填（机器已拦） |
| deny 堆积不清理 | 失控 deny 面=永久封锁层，新人永远解不开 | 配额逼清（机器已拦）；事件结束即解除 |
| 用 deny 当回收 | 语义混淆：deny=冻结（授权还在），revoke=收回（授权没了） | 想收回 → revoke；想冻结 → deny |

## 6. 业界锚点

- **Casbin deny-overrides**：`e = some(where (p.eft == allow)) && !some(where (p.eft == deny))`——业界标准组合效果
- **ABAC/XACML Obligation**：deny 带审计义务（reason/审批链）与 XACML 的 obligation 同族
- **AWS IAM 的边界**：AWS 只有 allow（策略拒绝=隐式 deny，无显式 deny 条目）——显式 deny 是更强的治理要求，不是行业最低配

## 7. demo 复现

```bash
cd projects/PermissionCenter
IAM_DEMO=http://localhost:18080 GW_DEMO=http://localhost:19080 bash scripts/demo.sh  # 场景 23
```

场景 23 全链：基线 allow → 治理钉子×2（通配 deny 400 / 无 reason 400）→ deny 授权单审批生效 → **deny-overrides 一票否决** → **精确性**（封 read 不误伤 list）→ 审计可指认 → 回收解除 → **allow 复通**。
