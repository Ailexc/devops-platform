# Beeflow 流程设计器接入与改造（方案 B 实施记录）

> 目的：记录"表单设计保留现有 form-create、流程设计接入 Beeflow（workflow-web）流程设计器、并改造办理节点支持任务绑定"的选型结论、实施内容、验证结果与后续事项，供团队评审与后续开发参考。
>
> 关联文档：[03-系统设计方案.md](./03-系统设计方案.md)

---

## 一、背景与选型结论

### 1.1 需求

- 流程设计器要"拿来即用"，减少自研量；
- 表单设计器不重新开发，优先使用项目内已集成的 form-create（`@form-create/designer`）；
- 流程节点模型要清晰，且办理节点需要支持"接入任务绑定"（办理节点绑定具体能力/任务）。

### 1.2 候选方案调研（2026-08 实测数据）

| 候选 | 技术栈 | 规模 | 协议 | 结论 |
|---|---|---|---|---|
| AntFlow-Designer | Vue3 + Element Plus | 125★ | Apache-2.0 | 仿钉钉风格，最贴合需求，但组件与后端绑定较深 |
| wflow（willianfu） | **Vue2** + Element UI | 556★ | Apache-2.0 | 功能更全（并发/延时/触发器、表单控件丰富），但 Vue2 三年未更新，**无办理节点**，只作借鉴 |
| Beeflow（workflow-web） | **Vue3** + Arco Design | 164★ | AGPL-3.0 | 节点语义清晰，**自带办理节点**，与需求最匹配 |
| Warm-Flow | Vue3 + 多 UI 适配 | Gitee 8.7k★ | Apache-2.0 | 设计器 + 引擎一体，适合重选型时考虑 |
| 芋道 yudao SimpleProcessDesignerV2 | Vue3 + Element Plus | 3.7k★ | MIT | 仿钉钉组件独立，可作为备选 |

### 1.3 选型结论（方案 B）

- **表单设计**：保留现有 form-create 表单设计器（`FormBuilder`），不开发；
- **流程设计**：接入 Beeflow（`zhangjinlibra/workflow-web`）流程设计器，仅取其前端设计器组件；
- **解耦方式**：新增 `form-create rules → flowWidgets` 适配层，使流程设计器只依赖"表单控件元数据"，两边互不侵入；
- **业务改造**：办理节点新增「任务绑定」页签（绑定能力 / 绑定表单字段），绑定结果随流程 JSON 持久化。

> 许可说明：Beeflow 为 AGPL-3.0，作者要求商用前登记。当前为 demo 项目，不涉及对外分发，暂不影响；后续商用需评估或替换为 MIT 方案。

---

## 二、整体方案

```text
┌─────────────────────────── 流程模版编辑页（3 步） ───────────────────────────┐
│  ① 基本信息        ② 表单配置                ③ 流程建模                        │
│                     │                        │                              │
│              form-create 设计器        ProcessFlowDesigner（集成壳）          │
│              (FormBuilder)                 │                                │
│                     │                        │                              │
│              form_schema               formCreateToFlowWidgets（适配层）      │
│              (rules/options)                │                                │
│                                            ▼                                │
│                                     Beeflow 流程设计器                        │
│                           （审批/抄送/办理/条件分支节点 + 配置抽屉）             │
│                                            │                                │
│                                            ▼                                │
│                                     definition_json（Beeflow 流程 JSON）      │
└──────────────────────────────────────────────────────────────────────────────┘
```

数据流要点：

1. 表单设计产出 form-create `rules`；
2. 适配层把 `rules` 转为流程设计器所需的 `flowWidgets`（字段名/标签/类型/选项/必填），供**条件分支、节点表单权限、流程校验**使用；
3. 流程设计产出 Beeflow 树状 JSON（`nodeConfig` + `flowWidgets` + `workFlowDef` + `flowPermission`），存入后端 `ProcessDefinition.definition_json`；
4. 办理节点的 `taskBinding` 配置随 `nodeConfig` 一并持久化。

---

## 三、实施内容

### 3.1 依赖与组件引入

- 新增依赖：`@arco-design/web-vue`（Beeflow 设计器 UI 库）、`less`（其样式编译器）；
- 拷贝自 Beeflow 仓库的代码：
  - `src/components/flow/`（设计器主体：画布、节点、配置抽屉、公共工具）
  - `src/components/common/EditableText.vue`（节点名编辑组件）
  - `src/directive/focus.js`（节点名输入自动聚焦指令）
  - `src/utils/is.js`（公式弹窗依赖的工具函数）
- `main.js` 注册 ArcoVue 与 `v-focus` 指令。

### 3.2 Store 与组织架构 API

- `src/stores/index.js`：统一导出 `useFlowStore` / `useOrganStore`（与 Beeflow 组件引用约定一致）；
- `src/stores/flow.js`：流程设计器状态（节点抽屉开关、节点配置回写、流程定义持有）；
- `src/stores/organ.js`：组织架构数据（用户/部门/角色）+ 名称解析 getters；
- `src/api/modules/organ.js`：对接后端 `/users`、`/departments`、`/roles`（自动翻页拉全量），**后端未启动时自动降级为演示数据**，保证 demo 可独立运行。

### 3.3 表单适配层（关键解耦点）

文件：`src/components/SchemaConverter/formCreateToFlowWidgets.js`

- 控件类型映射：input→单行文本、textarea→多行文本、number/inputNumber→数字、money→金额、select/radio→单选、checkbox/多选 select→多选、datePicker→日期（range 变体→日期区间）、upload→附件、cascader→单选、rate→评分；
- 无法映射的控件（switch、slider、colorPicker 等）不进入条件/权限体系，后续可按需在 `WIDGET` 常量与映射表中扩展；
- 输出结构：`{ name, label, type, required, options }`，满足条件分支、表单权限、流程校验的最小契约。

### 3.4 集成壳组件

文件：`src/components/FlowDesigner/ProcessFlowDesigner.vue`

- props：`modelValue`（Beeflow 流程 JSON）、`formSchema`（form-create schema）；
- 职责：
  - 初始化/回显流程定义到 flow store；
  - 监听表单变化，实时同步 `flowWidgets`；
  - 提供「保存流程配置」「导出 JSON」「重置」工具栏；
  - 保存时输出 `{ nodeConfig, flowWidgets, workFlowDef, flowPermission }` 完整 JSON；
- 画布区采用点阵背景 + 圆角卡片容器，与整体设计语言一致。

### 3.5 编辑页改造

文件：`src/views/process/ProcessDefinitionEditor.vue`

- 第三步「流程建模」由原 LogicFlow 建模器替换为 `ProcessFlowDesigner`；
- 表单步骤（第二步）保持不变；
- 流程数据字段由 `flow_schema`（未落库）改为 `definition_json`（后端 `ProcessDefinition.definition_json` 对应字段），保存/回显打通；
- 页面布局打磨：最大宽度、步骤条样式、按钮微交互、流程步骤全高展示。

### 3.6 办理节点「任务绑定」

| 文件 | 改动 |
|---|---|
| `src/components/flow/common/FlowConstant.js` | 新增 `TASK_BIND`（不绑定/绑定能力/绑定表单字段）与 `TASK_BIND_LIST` |
| `src/components/flow/AddNode.vue` | 办理节点默认配置携带 `taskBinding` 结构（enabled/bindType/capabilityId/formField/taskName 等） |
| `src/components/flow/drawer/TransactDrawer.vue` | 新增第 4 个页签「任务绑定」：启用开关、绑定方式、能力下拉（对接能力接口，含演示兜底）、表单字段选择、任务名称 |
| `src/components/flow/NodeWrap.vue` | 办理节点卡片展示「任务：xxx」，配置一目了然 |

能力数据来自后端 `/capabilities`（`getCapabilities`），后端不可用时降级为演示能力列表。

### 3.7 视觉与设计系统

- `src/styles/global.scss`：
  - 统一 Arco 与 Element Plus 品牌色（主色 `#409EFF`，含 10 档色阶）；
  - 统一圆角、弱化文字色、边框色；
  - 全局焦点环（键盘可达性）、可点击元素 `cursor: pointer`；
  - 卡片/抽屉/弹窗圆角一致化；
- `vite.config.js`：分包优化（arco / element / form-create / logicflow / vue-flow / vendor 独立 chunk），主包体积明显下降；
- 预览页与编辑页均采用 8px 间距体系与一致的卡片/按钮风格。

### 3.8 免登录预览页

文件：`src/views/demo/FlowDesignerPreview.vue`，路由 `/preview/flow-designer`

- 左侧展示示例 form-create schema，右侧直接渲染流程设计器；
- 支持导出流程 JSON，方便快速体验与联调，不依赖登录与后端。

---

## 四、验证结果

| 验证项 | 结果 |
|---|---|
| `npm run build` 生产构建 | ✅ 通过（依赖已分包） |
| Vite 开发模式关键模块编译（13 个） | ✅ 全部通过，无编译错误 |
| 预览路由 `/preview/flow-designer` | ✅ 返回 200，可访问 |
| 新增引用完整性检查（@/ 路径） | ✅ 无缺失模块 |

---

## 五、使用方式

```bash
cd frontend
npm install        # 首次
npm run dev
```

- **快速体验**：`http://localhost:5173/preview/flow-designer`（无需登录/后端）；
- **正式入口**：登录后进入「模版管理 → 新建模版 → 第 3 步 流程建模」；
- 后端启动时，组织架构（用户/部门/角色）与能力列表自动从接口加载；未启动时使用演示兜底数据。

---

## 六、限制与后续事项

1. **运行时引擎转换器（下一步重点）**：当前流程设计结果以 Beeflow 树状 JSON 存入 `definition_json`，而后端引擎 `engine.py` 期望 `nodes/edges` 格式。demo 阶段设计器可正常使用；后续需编写「树状 JSON → nodes/edges」转换器（含条件分支表达式映射），引擎才能执行设计出的流程。
2. **表单控件映射白名单**：form-create 的 switch/slider/colorPicker 等暂不参与条件/权限；扩展方式为 `WIDGET` 常量 + 适配层映射各加一行。
3. **双 UI 库并存**：流程设计器使用 Arco、应用主体使用 Element Plus，demo 可接受；若后续追求包体与一致性，可做 Arco 按需引入或组件替换。
4. **组织/能力接口依赖**：人员、角色、部门、能力列表依赖后端接口可用性；已提供演示兜底，但真实数据需后端启动。
5. **许可证**：Beeflow 为 AGPL-3.0 且作者要求商用登记，demo 阶段无碍；进入商用前需评估（替换为 MIT 的 yudao SimpleProcessDesignerV2 或 Warm-Flow，或与作者确认授权）。

---

## 附：关键文件清单

```text
frontend/src/components/flow/                    # Beeflow 流程设计器（拷贝+改造）
frontend/src/components/flow/drawer/TransactDrawer.vue   # 办理节点配置（新增任务绑定页签）
frontend/src/components/flow/AddNode.vue                 # 办理节点默认配置（taskBinding）
frontend/src/components/flow/NodeWrap.vue                # 节点卡片（任务绑定展示）
frontend/src/components/flow/common/FlowConstant.js      # 节点/控件/任务绑定常量
frontend/src/components/FlowDesigner/ProcessFlowDesigner.vue  # 集成壳组件
frontend/src/components/SchemaConverter/formCreateToFlowWidgets.js  # 表单适配层
frontend/src/stores/index.js / flow.js / organ.js        # 流程与组织状态
frontend/src/api/modules/organ.js                        # 组织架构接口（含兜底）
frontend/src/views/process/ProcessDefinitionEditor.vue   # 编辑页（第 3 步替换）
frontend/src/views/demo/FlowDesignerPreview.vue          # 免登录预览页
frontend/src/styles/global.scss                          # 设计系统/主题统一
frontend/src/main.js                                     # Arco 注册
frontend/vite.config.js                                  # 分包优化
```
