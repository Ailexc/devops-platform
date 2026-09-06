# 调研报告：本地开发服务器通过 lark-cli 操作飞书文档

> 调研日期：2026-09-05
> 调研环境：ailexc-server（Pop!_OS 24.04 LTS，x86_64，本地开发服务器）
> 调研目的：确认能否在服务器上通过 CLI 工具**新建 / 更新**飞书文档，为后续梳理 DevOpsPlatform 项目知识点并写入飞书文档做准备
> 性质：仅调研，未做任何业务改动

---

## 一、结论（TL;DR）

**可行 ✅，且已找到"一键创建应用 + 扫码授权"的官方方案**。

第二轮调研重大更新：发现飞书**官方 CLI `@larksuite/cli`**（npm 包，v1.0.93），其 `config init --new` 命令支持**终端内生成二维码 + 验证链接**，用户用飞书 App 扫码或打开链接即可**自动创建应用并完成授权配置**，全程无需手动去开放平台建应用、抄 App ID/Secret。已在本服务器实测，流程真实可用（见 §3.1）。

| 方案 | 形态 | 一键创建应用 | 认证方式 | 文档新建 | 文档更新 | 推荐度 |
|---|---|---|---|---|---|---|
| **@larksuite/cli** v1.0.93（飞书官方） | Node CLI | ✅ `config init --new`（扫码/链接） | Device Flow 扫码（`auth login`，支持 `--no-wait` 异步） | ✅ `docs` 域 + `markdown` 域 | ✅ 块级编辑 + Markdown 覆写 | ⭐⭐⭐⭐⭐ |
| **rintays/lark-cli** v0.1.18 | Go 单二进制 | ❌ 需手动建应用 | tenant token（免浏览器）/ user OAuth | ✅ `docs create` | ✅ `docs overwrite`（Markdown 整体覆写） | ⭐⭐⭐⭐ |
| **yjwong/lark-cli** v0.12.0 | Go 单二进制 | ❌ 需手动建应用 | 仅 OAuth 浏览器流程 | ✅ `doc create` | ⚠️ `doc append` 可用；`update-block` 发布版缺失 | ⭐⭐⭐ |
| **@larksuiteoapi/lark-mcp** v0.5.1（官方 MCP） | MCP Server | ❌ | OAuth（需 MCP 客户端） | ✅ | ✅ | ⭐⭐⭐（适合接 Copilot 等 MCP 宿主） |

**推荐组合**：`@larksuite/cli`（官方）作为主力——一键创建应用 + 扫码授权 + 文档读写全覆盖；`rintays/lark-cli` 作为轻量备选（单二进制、tenant token 免浏览器，适合 CI/无人值守脚本）。

---

## 二、服务器环境实测结果

| 检查项 | 结果 |
|---|---|
| 操作系统 | Pop!_OS 24.04 LTS（Ubuntu 系），x86_64 |
| Node.js | v24.20.0 ✅（lark-mcp 可用） |
| Go | 未安装（不影响：两个 CLI 均有预编译二进制） |
| 网络 | open.feishu.cn / registry.npmjs.org / github.com 全部可达 ✅ |
| 现有飞书配置 | 无（`~/.lark`、`~/.config/lark*`、环境变量均无凭据）❗ |

---

## 三、候选工具详细调研

### 3.1 @larksuite/cli（飞书官方，推荐）⭐ 第二轮调研新增

- npm 包：`@larksuite/cli`，版本 1.0.93，命令名 `lark-cli`
- 已实测：安装到 `~/.npm-global/bin/lark-cli`，运行正常
- **一键创建应用（核心亮点，已实测）**：
  ```bash
  lark-cli config init --new --lang zh
  ```
  终端会输出**二维码 + 验证链接**（形如 `https://open.feishu.cn/page/cli?user_code=XXXX-XXXX&...`），用飞书 App 扫码或浏览器打开链接，即可自动创建自建应用并完成 CLI 与应用的绑定，**无需手动去开放平台建应用、无需手动抄 App ID/Secret**。命令会阻塞等待扫码完成，适合后台运行后把链接发给用户。
- **扫码授权登录（Device Flow）**：
  ```bash
  lark-cli auth login --domain docs,drive,markdown   # 按域申请权限
  lark-cli auth login --no-wait --json              # 异步模式：立即返回验证 URL，适合 Agent 场景
  lark-cli auth qrcode <url> --ascii                # 生成 ASCII/PNG 二维码
  ```
  支持 `--recommend`（仅申请自动批准的权限）、`--scope`（精确 scope）、`--exclude`（排除）。
- **文档能力**（`docs` / `markdown` / `drive` / `wiki` 域）：
  - `docs` 域：文档与内容操作（创建、块级读写）
  - `markdown` 域：**Drive 原生 Markdown 文件的创建、读取、覆写**——对"把项目知识点写成文档"场景最直接
  - `drive` 域：文件、评论、权限、上传管理
  - `wiki` 域：知识库空间与节点管理
  - 每个命令标注风险等级（read / write / high-risk-write），高危写需 `--yes` 确认
  - 支持 `--jq` 过滤输出、`--dry-run` 预览请求、`schema` 命令查看 API 参数
- **Agent 友好设计**：帮助文档内置 "AGENT QUICKSTART"，明确支持 `--no-wait` 异步授权流程，专为 AI Agent 驱动设计
- 其他：`doctor` 健康检查、`profile` 多配置、`update` 自更新

### 3.2 rintays/lark-cli（轻量备选）

- 仓库：https://github.com/rintays/lark-cli （20+ stars，活跃维护，基于官方 `oapi-sdk-go`）
- 已实测：下载 v0.1.18 Linux 预编译二进制到 `~/tools/lark-cli-rintays/`，运行正常
- **认证双模式**（关键优势）：
  - `lark auth tenant`：tenant token，**无需浏览器**，适合服务器无人值守场景
  - `lark auth user login`：user OAuth（个人身份操作个人文档）
- **文档能力**（`lark docs --help` 实测）：
  - `docs create <title>` — 新建文档
  - `docs overwrite <doc-id> --content-file doc.md` — **用 Markdown/HTML 整体覆写文档内容**（还支持 `--upload-images` 自动上传图片）
  - `docs get <doc-id> --format md|txt|blocks` — 读取为 Markdown
  - `docs blocks children create / batch-update / descendant create` — 块级精细编辑
  - `docs convert` — Markdown/HTML 转 Docx blocks
  - `docs export` — 导出为其他格式
  - 另有 wiki、drive、sheets、messages 等全套命令
- 所需权限 scope：`docx:document:readonly`、`docx:document:create`、`docx:document:write_only`、`docx:document.block:convert`（该仓库文档明确建议用这几个细分 scope，避免粗粒度 `docx:document`）

### 3.3 yjwong/lark-cli

- 仓库：https://github.com/yjwong/lark-cli （53 stars，专为 AI 助手设计，JSON 输出）
- 已实测：下载 v0.12.0 二进制到 `~/tools/lark-cli/`，运行正常（需 `LARK_CONFIG_DIR` 环境变量）
- 文档能力：`doc create` / `doc append`（支持 text/heading/code/bullet/table/todo）/ `doc get`（Markdown）/ `doc search` / `doc wiki` 等
- **限制**：
  - 仅支持 OAuth 浏览器流程认证（服务器上需借助端口转发或在本机登录后拷贝 token）
  - v0.12.0 发布版二进制中 `doc update-block` 命令缺失（源码 main 分支已有，需等下个 release 或自行编译）
- 所需权限：`docx:document:readonly`、`docx:document`、`docx:document:create`、`docs:document.content:read`、`drive:drive:readonly`、`wiki:wiki:readonly` 等

### 3.4 @larksuiteoapi/lark-mcp（飞书官方 MCP）

- 已实测：`npm install -g @larksuiteoapi/lark-mcp` 安装到 `~/.npm-global/bin/lark-mcp`，版本 0.5.1，运行正常
- 形态：**MCP Server**（stdio/sse/streamable），不是直接敲的 CLI，需要 MCP 客户端（如 VS Code Copilot、Claude Code）调用
- 认证：`lark-mcp login -a <AppID> -s <Secret>` 走 OAuth；支持 `--token-mode user_access_token|tenant_access_token`
- 优势：官方维护、工具集覆盖全（`-t` 可选 preset 工具组）、未来可直接接入本机 Copilot 的 MCP 配置
- 劣势：纯 shell/脚本场景不如独立 CLI 方便

> 注：npm 上名为 `lark-cli` 的包（0.1.0）是无关占位包，**不要安装**。

---

## 四、落地步骤（待你确认后执行）

1. **一键创建应用 + 授权**（官方 CLI，已实测可行）：
   ```bash
   lark-cli config init --new --lang zh
   ```
   终端输出二维码/链接 → 你用飞书 App 扫码或点链接 → 应用自动创建并绑定 CLI。**这是唯一需要你参与的步骤**（扫码动作）。
2. **申请文档权限并登录**：
   ```bash
   lark-cli auth login --domain docs,drive,markdown
   ```
   同样是扫码/链接授权（Device Flow，支持 `--no-wait` 异步）。
3. **连通性验证**：
   ```bash
   lark-cli doctor                          # 健康检查
   lark-cli docs --help                     # 查看文档命令
   lark-cli markdown --help                 # 查看 Markdown 文件命令
   # 实测：创建测试文档 → 写入内容 → 读取确认 → 删除
   ```
4. **后续工作流**（本次调研的最终目的）：梳理 DevOpsPlatform 各子系统（Authentication / CloudManager / EventManager / PermissionCenter / ReleaseManager / TaskManager / WorkFlowCenter）的知识点 → 生成本地 Markdown → 通过 `markdown`/`docs` 域写入飞书知识库

> 备选路径：若偏好轻量二进制方案，用 rintays/lark-cli 时仍需手动在开放平台建应用（见 §3.2），适合 CI/无人值守场景。

---

## 五、风险与注意事项

- **权限审批**：企业自建应用权限通常需要管理员审批；个人版飞书一般即时生效
- **token 有效期**：tenant token 约 2 小时过期，rintays 版会自动缓存刷新；user token 依赖 `offline_access` 刷新
- **文档归属**：tenant token（应用身份）创建的文档在应用空间，如需文档出现在个人云空间/知识库，用 user OAuth 或创建后手动移动
- **覆盖写风险**：`docs overwrite` 会清空原文档内容，对重要文档建议先 `docs get --format md` 备份
- **速率限制**：飞书 OpenAPI 有频控，批量写文档时注意间隔

---

## 六、本次调研在服务器上留下的产物

| 路径 | 说明 |
|---|---|
| `~/.npm-global/bin/lark-cli` | **@larksuite/cli v1.0.93 官方 CLI（推荐主力）** |
| `~/tools/lark-cli-rintays/` | rintays/lark-cli v0.1.18 二进制（轻量备选） |
| `~/tools/lark-cli/` | yjwong/lark-cli v0.12.0 二进制（备用） |
| `~/.npm-global/bin/lark-mcp` | 飞书官方 lark-mcp v0.5.1（MCP 形态备选） |
| `~/.npm-global/` | npm 用户级全局目录（已配置 prefix，避免 sudo） |

以上均为用户目录安装，未动系统环境，可随时删除清理。

---

## 七、第二轮调研补充记录（2026-09-05）

- 触发问题：是否有"一键创建应用 + 扫码授权"能力
- 调研过程：
  1. 检查 rintays/yjwong 两个社区版 CLI 的 auth 命令 → 均无创建应用能力，需手动建应用
  2. npm 搜索发现 `@larksuite/cli`（官方 CLI，v1.0.93）→ 安装实测
  3. `lark-cli config init --new` 实测：终端输出二维码 + 验证链接（`https://open.feishu.cn/page/cli?user_code=XL5E-6YQT&...`），等待扫码中
- 结论：官方 CLI 完全满足"一键创建应用 + 扫码授权"需求，且 Device Flow 登录（`auth login --no-wait`）对 Agent 场景友好
- 注意：`config init --new` 会阻塞等待扫码；Agent 驱动时应后台运行并提取链接发给用户，或使用 `--no-wait` 模式

---

## 八、连接器统一管理方案（VS Code 痛点治理）

### 8.1 痛点分析

- Trae 等国内 IDE 有**显式连接器面板**（如"已连接：飞书"），Agent 天然知道能力边界，切换对话/项目不丢失
- VS Code Copilot 无此 UI，Agent 对服务器能力的感知来源分散：MCP 配置 / instructions 文件 / memory / 自行探索
- 后果：新对话、新项目里 Agent 不知道服务器装了 `lark-cli`，需要人工重复告知；未来装更多连接器（Notion、Confluence…）会更混乱

### 8.2 两类连接器、两条感知通道

| 类型 | 例子 | 感知通道 | 显式程度 |
|---|---|---|---|
| **MCP 型** | `lark-mcp`（官方） | 用户级 `mcp.json` → Copilot Chat 工具面板（🔧 图标）可见、可开关、**跨项目持久** | 高（最接近 Trae 体验） |
| **CLI 型** | `lark-cli`、`gh`、`docker` 等 | instructions / memory 文本注入 | 中（无 UI 面板，但稳定可靠） |

**结论：MCP 管"显式"，instructions 管"兜底"，注册表管"扩展"。** 两者不冲突：MCP 适合需要结构化工具调用的场景；CLI 适合脚本化、无人值守、以及 MCP 未覆盖的能力（如 lark-cli 的 `markdown` 域）。

### 8.3 推荐架构：注册表 + 注入 + 自检 三件套

```text
~/.agent/connectors.md                                    ← ① 单一事实来源（注册表）
~/.vscode-server/data/User/prompts/connectors.instructions.md   ← ② 自动注入（applyTo: **）
~/tools/connector-doctor.sh                               ← ③ 一键自检所有连接器
```

**① 注册表**（每个连接器一条记录，可纳入 dotfiles 版本管理）：

```markdown
## lark-cli（飞书官方 CLI）
- 类型: CLI ｜ 路径: ~/.npm-global/bin/lark-cli ｜ 版本: 1.0.93
- 认证: `config init --new` 扫码创建应用；`auth login --domain docs,drive,markdown` 扫码授权
- 能力: 文档 CRUD、markdown 域原生 md 文件、wiki、drive
- 自检: `lark-cli doctor`
- 详细: DevOpsPlatform/docs/lark-cli-飞书文档操作调研.md
```

**② 注入文件**（用户级 instructions，`applyTo: **` 全项目生效，保持 <50 行）：

- 声明"本服务器已安装以下连接器，清单见 `~/.agent/connectors.md`"
- 路由规则：文档类操作 → 先查注册表再动手；能力不确定 → 跑 `connector-doctor.sh`
- 明确禁止"凭空假设能力不存在"

> 路径说明：服务器端 prompts 目录为 `~/.vscode-server/data/User/prompts/`；若实测未生效，改放到客户端 `~/Library/Application Support/Code/User/prompts/`（与现有全局 `copilot-instructions.md` 同目录）。

**③ 自检脚本**：汇总各连接器的 doctor/status 命令，输出健康矩阵；Agent 在不确定时先跑它，避免瞎猜。

### 8.4 新连接器接入 SOP（未来扩展）

1. 安装（用户目录，不动系统环境）
2. 注册表 `~/.agent/connectors.md` 加一条
3. `connector-doctor.sh` 加一行自检
4. **instructions 文件无需改动**（它只指向注册表）

→ 任何新对话/新项目，Agent 自动感知新连接器。装 Notion/Confluence 连接器时照此办理即可。

### 8.5 分层职责

| 层级 | 内容 | 作用域 |
|---|---|---|
| 用户级 | 注册表 + instructions + 用户级 mcp.json | 所有项目、所有对话 |
| 项目级 | repo memory / 项目 `copilot-instructions.md` | 项目特有用法（如飞书知识库目录结构、文档命名规范） |

### 8.6 立即生效的措施（本次已执行）

- ✅ 已将 lark-cli 能力写入 Copilot **用户记忆**（跨项目、跨对话自动加载）——这是 Copilot 场景下最快生效的"连接器感知"
- ⏳ 待确认后执行：创建注册表文件 + instructions 文件 + doctor 脚本（§8.3 三件套）
