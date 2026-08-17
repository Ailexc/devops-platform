# 能力包 Demo v12 — 进度总结

## 1. 背景

权限中心（IAM）demo 中的**能力包数据范围**功能，v10 版本存在设计问题：

- **数据范围 = "手写表达式"**：owner 配置时只能写 CEL 表达式（如 `env == "prod"`），applicant 申请时也需要手写表达式
- **用户不会写表达式**：普通用户不可能去学 OpenFGA/CEL 语法
- **编辑器配置不完整**：v10 的 `scopeOptRowHTML` 函数只处理 `all`/`instance`/`expression` 三种类型，新增类型没有对应的编辑器 UI
- **申请人界面没有交互组件**：v10 的 `apStepHTML` step3 只渲染选项卡片，没有实际的下拉框、复选框、输入框等交互组件

## 2. 目标

将数据范围从"手写表达式"升级为**表单字段类型系统**：

- **内置类型** 2 个：`all`（全量）、`instance`（实例勾选）
- **Owner 自定义类型** 4 个：`select`（单选）、`multi_select`（多选）、`variable`（自动匹配）、`input`（自由输入）
- **去掉**：`expression`（高级表达式构建器）、`fixed`（固定条件）
- **applicant 不需要学任何语法**：选择/输入后系统自动生成 CEL 表达式

## 3. 当前状态

### ✅ 已完成

| 项目 | 状态 | 说明 |
|------|------|------|
| v12 基线构建 | ✅ | `scripts/build-v12.js` 从 v10 生成，JS 语法验证通过 |
| 标题/副标题 | ✅ | 更新为 v12 描述 |
| 新增 CSS | ✅ | `.choice-chips`、`.choice-chip`、`.var-display`、`.expr-preview` |
| SCOPE_OPT_LABEL | ✅ | 移除 `expression`，新增 `select`/`multi_select`/`variable`/`input` |
| scopeIcon | ✅ | 6 种类型对应图标 |
| CAPS 数据 | ✅ | 4 个 preset 的 scope options 已替换为新类型 |
| 新增 helper 函数 | ✅ | `apScopeSelectVal`、`apScopeMultiToggle`、`apScopeInput` |
| 移除 composeExpr | ✅ | 不再需要 |
| 重写 scopeOptRowHTML | ✅ | 编辑器：select/multi_select/variable/input 配置表单 |
| 重写 pEdit | ✅ | 新增 soptAdd/soptChoiceAdd/soptChoiceDel/soptVariable/soptPlaceholder |
| 重写 apStepHTML step3 | ✅ | 申请人：radio/checkbox/variable-display/input 交互组件 |
| 浏览器验证 | ✅ | v12 页面正常加载，goTab 可用，申请人 step3 交互正常 |

### ❌ 未完成

| 项目 | 说明 | 优先级 |
|------|------|--------|
| **build-v12.js 完整化** | 需要将 scopeOptRowHTML/pEdit/step3 替换也加入构建脚本（目前通过 replace_string_in_file 完成） | P1 |

## 4. 踩过的坑

### 4.1 shell `-e` 引号转义问题（已解决）

**现象**：`node -e "..."` 内联脚本中，`\"` 在单引号内不会被转义为 `"`，导致生成的 JS 函数包含反斜杠引号。

**解决**：改用独立 `.js` 脚本文件（`scripts/build-v12.js`）。

### 4.2 三元运算符嵌套语法错误（已解决）

**现象**：`on&&i<0?a:(!on&&i>=0?b)` 报 `Unexpected token ')'`。

**原因**：JS 解析器将 `(!on&&i>=0?b)` 解析为一个分组表达式，但分组内的三元运算符缺少 false 分支，导致 `)` 被误认为是外层三元的 `:` 位置。

**解决**：改用 `if/else` 写法：
```js
if(on&&i<0) cur.selectedValues.push(v);
else if(!on&&i>=0) cur.selectedValues.splice(i,1);
```

### 4.3 v10 → v12 增量替换的陷阱

**现象**：多次尝试用正则/行号操作替换大段模板字面量代码，频繁失败。

**原因**：
- 模板字面量跨越多行，行号操作会切断模板结构
- 正则匹配对长字符串不可靠
- `vm.compileFunction` 的行号报错可能不准确（报错行是 `</div>` 但实际问题在更早的位置）

**解决**：用**精确字符串匹配**（`str.replace`）+ **脚本文件**的方式，逐步验证每一步。

## 5. 下一步计划

### Phase 1：数据+基线（✅ 已完成）
- 数据替换、CSS、helper 函数 → v12 可打开

### Phase 2：编辑器交互（待做）
1. 重写 `scopeOptRowHTML`：每种 type 渲染不同的配置表单
2. 重写 `pEdit`：新增 choice 管理、variable 选择、placeholder 配置
3. 移除 `composeExpr` 函数

### Phase 3：申请人交互（待做）
1. 重写 `apStepHTML` step3：渲染 radio/checkbox/variable-display/input
2. 更新 step4 预览逻辑

### Phase 4：高级功能（P1）
1. select/multi_select 支持配置接口获取选项（如 `GET /api/v1/envs`）
2. 表达式自动生成（applicant 选择后实时显示生成的 CEL）

## 6. 文件清单

| 文件 | 说明 |
|------|------|
| `docs/capability-apply-demo-v12.html` | 当前 v12 demo（数据+CSS+helper 已完成） |
| `scripts/build-v12.js` | v12 构建脚本（从 v10 生成） |
| `docs/v12-progress.md` | 本文档 |
| `docs/capability-apply-demo-v10.html` | v10 基线（保留） |
