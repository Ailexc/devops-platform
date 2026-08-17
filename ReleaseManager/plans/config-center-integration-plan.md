# 配置中心接入发布链路 实施计划

> 状态：**已实施（V1+V2+V3 demo 数据完成）**
> 日期：2026-08-02
> 目标：让「配置模板 + 变量管理」从独立孤岛接入真实发布链路，实现「配置随发布走」闭环，并在 UI 上呈现绑定关系
> 架构决策：**backend 渲染（有 DB）→ 传参 executor → ConfigMap 下发 + Deployment 挂载**，不新增表、不迁移，全部复用现有模型

---

## 0. 实施记录（2026-08-02）

- **V1 发布链路闭环** ✅：`releases/views.py` 新增 `_render_release_config`（渲染 + 记录 ConfigRelease 版本号=同模板同环境最大+1），`_auto_trigger_cd` 渲染失败中断发布、成功将 `params['configs']` 传参；CD 成功 `_watch_execution` 将 `ConfigRelease.status` 置 `applied`。executor `k8s.py` 新增 `apply_configmap`/`mount_configmap`（strategic merge patch 幂等），`runner.py` 新增 `_maybe_config_apply`（创建 ConfigMap + 挂载主 Deployment `/etc/app`），接入 deploy/canary/blue_green 三操作（蓝绿/灰度克隆体基于主 Deployment JSON 克隆**自动继承挂载**）。
- **V2 前端绑定展示** ✅：`configApi` 支持 `templates.list(params)`/`variableValues.list(params)`，新增 `releases.byRelease`；应用详情页新增「📄 配置模板」区块（模板表 + 展开行变量各环境值）；发布详情页新增「📄 本次配置」区块（配置版本 + 渲染内容 + 与上一版 diff）。
- **V3 demo 数据** ✅：go-app(id=13) 补 `app.env` 模板（env 类型，LOG_LEVEL/ENV 变量，dev 值 log_level=debug）；python-app(id=15) 模板补 `version` 变量（默认 1.0.0）让 `{{ version }}` 正常替换；node-app 留空作跳过路径演示。可选「应用读 `/etc/app`」未做（V1/V2 只挂载不强制读取）。
- **端到端验证（容器环境）**：rolling 发布 python-app → `python-app-config` ConfigMap + `/etc/app` 挂载 + ConfigRelease v3 applied + diff 可追溯；blue_green → `python-app-blue` 克隆体继承挂载 + selector 切 blue；node-app 无模板 → CD 日志无配置下发、正常完成；go-app → `go-app-config` ConfigMap（LOG_LEVEL=debug/ENV=dev）+ 挂载 + byRelease 正常。

---

## 1. 背景与目标

### 1.1 现状问题
- 配置模板/变量管理/配置发布记录**功能已修复可用**（`configs` 模型 + API + 页面完整），但：
  1. 渲染出的配置**没有下发到运行时**（Pod 仍用 `deployment.yaml` 写死的 env）
  2. 发布单 CD **不携带配置版本**（`ConfigRelease.release` 外键存在但未串联）
  3. 绑定关系**只在数据层**（`ConfigTemplate.application` / `ConfigVariableValue.environment`），UI 无呈现
- 结果：配置中心是"自洽但无人消费"的孤岛，面试讲不出"配置怎么生效"

### 1.2 目标
1. 发布 CD 时按「应用 × 环境」自动渲染配置 → 生成 K8s ConfigMap → 挂载进 Deployment（**配置随发布走**）
2. 应用详情页展示该应用的配置模板 + 各环境值（**绑定可视化**）
3. 发布详情页展示本次发布的配置版本 + diff（**可追溯可回滚**）
4. 无配置模板的应用正常跳过（兼容路径）

### 1.3 绑定模型（已就位，无需新表）
```
ConfigTemplate.application       模板 → 应用（一个应用可挂多个模板）
ConfigVariableValue.environment  变量值 → 环境（同一模板按环境取不同值）
ConfigRelease.release            配置版本 → 发布单（随发布记录/回滚）
```

---

## 2. 架构总览

```
backend（有 DB）           executor（有 kubectl）           集群
┌────────────────┐   ┌────────────────────┐   ┌─────────────────────┐
│ _auto_trigger_cd│→  │ op=config_apply    │→  │ ConfigMap {app}-cfg │
│ 查询模板+渲染    │   │ 写 ConfigMap       │   │  └─ 挂载 /etc/app   │
│ render_template │   │ patch Deployment  │   │ Deployment volumes  │
└────────────────┘   └────────────────────┘   └─────────────────────┘
        │（渲染结果作为 params 传参）
        ▼
发布详情页展示「本次配置版本 + diff」
应用详情页展示「该应用配置模板 + 各环境值」
```

- **backend 负责渲染**（executor 独立服务不读 DB，渲染必须在 backend 完成再传参）
- **executor 负责下发**（新增 `op=config_apply`，复用 kubectl/k8s.py 能力）

---

## 3. 详细设计

### 3.1 backend：渲染 + 传参（`backend/apps/releases/views.py`）

改造 `_auto_trigger_cd`（或新增 `_render_release_config(release)`）：

```python
def _render_release_config(release):
    """按 应用×环境 渲染该应用所有配置模板，返回 {template_name: rendered_content}"""
    from apps.configs.models import ConfigTemplate, ConfigVariable, ConfigVariableValue
    from apps.configs.views import render_template
    env = release.env_config.environment
    result = {}
    for tpl in ConfigTemplate.objects.filter(application=release.application, is_active=True):
        # 渲染（内部按该环境的变量值）
        result[tpl.name] = render_template(tpl, env)
        # 记录配置发布版本（ConfigRelease：template+environment+release）
        ConfigRelease.objects.create(
            template=tpl, environment=env, version=(上次版本+1),
            rendered_content=result[tpl.name], release=release,
        )
    return result
```

- 在 `_auto_trigger_cd` 提交 CD 前调用；**无模板返回空 dict（跳过下发，不报错）**
- 渲染结果放入 CD params：`params['configs'] = {name: content}`
- 发布单状态仍按现有流程（CD 成功才 completed；配置渲染失败 → 中断发布并报错）

### 3.2 executor：`op=config_apply`（`executor/app/runner.py` + `k8s.py`）

新增 handler `_do_config_apply(ex, p)`，在 CD 主操作（deploy/blue_green/canary）成功后调用：

1. **创建/更新 ConfigMap** `{app}-config`（namespace = `_cluster_ns()` 解析）：
   - `k8s.py` 新增 `apply_configmap(namespace, name, data: dict)`（CoreV1 create/replace）
   - data 为 `{template_name: rendered_content}`
2. **patch Deployment 挂载**：`kubectl patch deployment/{app} -n {ns}` 添加：
   - `spec.template.spec.volumes` → ConfigMap 卷
   - `spec.template.spec.containers[0].volumeMounts` → 挂载 `/etc/app`
   - 蓝绿/灰度：`{app}-blue` / `{app}-canary` 克隆自主 Deployment，patch 主 Deployment 后再补 patch 克隆体
3. 挂载后无需触发新 rollout（CD 主操作已完成；ConfigMap 变更由 volume 自动同步）

> 边界：仅创建 ConfigMap + 挂载，**不要求应用必须读它**（demo 应用可后续加读 `/etc/app/config.yaml` 逻辑，见 V3 可选）。

### 3.3 前端：绑定展示

**应用详情页**（`frontend/src/pages/apps/detail.tsx`）— 环境配置 Tab 后新增「配置模板」区块：
- 调 `configApi.templates.list({ params: { app_id } })` 按应用过滤（后端已支持 `app_id` 参数）
- 展示：模板名、类型、版本、状态、部署路径；展开可看各环境变量值（复用 config-variable-values）
- 空态："该应用未绑定配置模板"

**发布详情页**（`frontend/src/pages/releases/detail.tsx`）— 新增「📄 本次配置」区块（发布含 configs 时）：
- 展示本次发布的模板名 + 渲染内容（等宽小字）
- 若 `ConfigRelease` 有上一版本，展示与上次的 diff（后端已有 `release_diff`）
- 无配置模板的发布显示"未携带配置"

**API 封装**：`configApi.templates.list` 已支持 app_id；新增 `configApi.releases.byRelease(releaseId)`（后端补一个小接口：按 release 查 ConfigRelease 列表）。

### 3.4 demo 数据（差异化演示）

| 应用 | 绑定 | 用途 |
|------|------|------|
| python-app | ✅ 已有 `app-config` 模板（yaml，变量 app_name，dev 值 python-demo-dev） | 主演示：配置随发布走 |
| go-app | ✅ 新建 1 个简单模板（如 `app.env`） | 展示多应用可分别绑定 |
| node-app | ❌ 留空 | 演示"无模板 → 跳过"兼容路径 |

---

## 4. 分阶段实施

| 阶段 | 内容 | 涉及 | 验收 |
|------|------|------|------|
| **V1 发布链路闭环** | backend `_render_release_config` + 传参；executor `op=config_apply`（ConfigMap + 挂载）+ `k8s.py` 新增方法；CD 成功后调用 | `views.py`、`runner.py`、`k8s.py` | python-app 发布后集群出现 `python-app-config` ConfigMap，Deployment 挂载 `/etc/app` |
| **V2 前端绑定展示** | 应用详情页「配置模板」区块；发布详情页「本次配置」区块 + diff；新增 byRelease 小接口 | `apps/detail.tsx`、`releases/detail.tsx`、`configs/views.py`、`api/index.ts` | 应用详情看到模板清单；发布详情看到配置版本与 diff |
| **V3 demo 数据 + 端到端** | go-app 补模板；python-app 可选加读 `/etc/app/config.yaml`（展示配置真生效）；三策略（rolling/blue_green/canary）各跑一次 | `demo-apps/**`、python-app 代码（可选） | rolling 挂载生效；blue/canary 克隆体也挂载；node-app 发布跳过不报错 |

> 推荐 V1+V2 一起做（都是同一链路的收尾），V3 视演示需要。

---

## 5. 风险与注意点

1. **executor 不读 DB**：渲染必须在 backend 完成、以 params 传参；executor 只做 kubectl 下发（既有架构约束）。
2. **Deployment 挂载方式**：直接 patch 主 Deployment（`kubectl patch` 加 volumes/volumeMounts）。蓝绿/灰度克隆体需额外 patch；`kubectl set image` 不会动 volumes，滚动路径无冲突。
3. **ConfigMap 命名冲突**：`{app}-config` 需避免与既有资源冲突；用 `_cluster_ns()` 解析真实 ns（DB namespace 是模拟名）。
4. **配置版本号**：`ConfigRelease.version` 按"同模板同环境的最大版本 +1"，无历史则从 1 开始。
5. **无模板兼容**：`configs` 为空 → 跳过下发与记录，发布主流程不受影响（node-app 演示点）。
6. **渲染失败**：模板变量缺值等 → 记录错误并**中断该次发布**（配置错误不应带病上线），与 CD failed 分支一致。
7. **权限**：沿用现有模型；配置渲染不新增独立权限，跟随发布权限。
8. **demo 应用是否读配置**：V1/V2 只挂载不强制读取（避免改 demo 代码）；V3 可选让 python-app 读 `/etc/app/config.yaml` 展示"真生效"。

---

## 6. 验收标准

- [ ] python-app 发布后集群出现 `python-app-config` ConfigMap，内容 = 渲染结果（dev 值）
- [ ] Deployment（含 blue/canary 克隆体）挂载 `/etc/app`，无需额外手动操作
- [ ] 应用详情页显示 python-app 的配置模板 + 各环境值；node-app 显示"未绑定"
- [ ] 发布详情页显示本次配置版本；有上一版本时展示 diff
- [ ] node-app 发布不携带配置、正常完成（跳过路径）
- [ ] go-app 发布携带其模板配置（多应用各自独立）
- [ ] 渲染失败时发布中断并给出明确错误
- [ ] 全程不加新表、不迁移（复用 ConfigTemplate/ConfigVariableValue/ConfigRelease）

---

## 7. 相关文件清单

- `backend/apps/releases/views.py`（`_render_release_config` + `_auto_trigger_cd` 传参）
- `backend/apps/configs/views.py`（新增 `release_configs_by_release` 小接口，可选）
- `executor/app/runner.py`（`_do_config_apply` + handlers 注册）
- `executor/app/k8s.py`（`apply_configmap` 方法）
- `frontend/src/pages/apps/detail.tsx`（配置模板区块）
- `frontend/src/pages/releases/detail.tsx`（本次配置区块）
- `frontend/src/api/index.ts`（byRelease 封装）
- `demo-apps/config/go-app/dev/`（V3 补模板数据）
- `plans/config-center-integration-plan.md`（本文档）
