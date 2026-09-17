# docs/visuals — 飞书文档引用的静态视觉资产

> 创建：2026-09-17 ｜ 定位：**文档叙事资料**（与各系统内部知识库是两个维度，勿混放）

## 这个目录是什么

存放飞书文档（面试叙事/项目介绍）所引用的交互式可视化资产：架构图、流程图、时序图等。

- **与系统内部知识库的区别**：各系统（Authentication 等）自带的"系统文档板块" HTML 是**运行时产品功能**，跟随系统部署；本目录是**叙事资料**，跟随仓库走，服务于文档讲解与面试表达。
- **防丢失**：随仓库迁移（GitHub）不丢、git 版本化、本地随时可看。
- **云端发布**：阿里云 ali-light 通过 Caddy 静态托管本目录，公网 URL 与仓库目录结构一一对应。

## 目录结构与命名规范

```
docs/visuals/
├── README.md                 # 本文件：规范与流程
└── <系统名>/                 # 按项目分类，与 projects/ 下目录同名
    ├── <图名>.json           # archify 源规格（唯一事实来源，可重新生成）
    ├── <图名>.html           # 交互版产物（发布到云端，供文档嵌入/链接）
    └── <图名>.png            # 静态截图（插入飞书文档的离线保底）
```

规则：
1. **源与产物都入库**：`.json` 是源，`.html`/`.png` 是产物。改图永远改 `.json` 再重新生成，禁止直接手改 `.html`。
2. **命名见名知义**：如 `sso-architecture`（SSO 总体架构）、`login-sequence`（登录时序）。
3. **语言**：图内文字、说明一律中文；技术名词保留英文原文。

## 生成命令（archify skill）

```bash
export ARCHIFY_CHROME=~/.cache/ms-playwright/chromium-1148/chrome-linux/chrome
ARCH=~/.agents/skills/archify

node $ARCH/bin/archify.mjs validate architecture <图名>.json --quality showcase --json
node $ARCH/bin/archify.mjs deliver architecture <图名>.json <图名>.html --quality showcase --json
node $ARCH/bin/archify.mjs visual-check <图名>.html --json
```

PNG 截图：visual-check 的 sidecar 截图，或用 Playwright 以 1600×1000 视口截全页。

## 发布流程（本地 → 云端 → 飞书）

```
本地: archify 生成 JSON/HTML/PNG → 存入本目录 → git push
云上: ali-light 仓库 checkout git pull → Caddy serve docs/visuals → 公网 URL 生效
飞书: PNG 插文档保底 + html5-block 内嵌（≤500KB）或链接卡片引用公网 HTML
```

云端 URL 规则：`https://sso-arch.ailexc.com/<系统名>/<图名>.html`（与仓库目录一一对应）。

## 云端托管信息（ali-light）

- Caddy 站点配置：`/home/admin/openclaw/caddy/Caddyfile` 中 `sso-arch.ailexc.com` 块
- 仓库浅 clone 路径：`/home/admin/openclaw/repos/DevOpsPlatform`（`--depth 1`）
- 更新：云上 `git pull` 即生效，无需重启 Caddy（静态文件即时可读）

## 变更记录

- 2026-09-17：目录与规范建立；首图 `Authentication/sso-architecture`（统一认证总体架构）
