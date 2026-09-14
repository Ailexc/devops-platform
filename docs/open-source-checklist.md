# 开源发布检查清单

> 背景：DevOpsPlatform 计划开源；AnyHaven（内网缓存平台）不开源。
> 本文档是"发布日照单执行"的唯一正本——日常开发**不需要**记任何开源相关事项。
> 状态（2026-09-14）：代码层预备已全部完成（分支 feat/open-source-prep），发布日仅剩本文档"发布日动作"一节。

## 一、已完成的预备（feat/open-source-prep，发布日无需重做）

- [x] **依赖源 ARG 化**：pip/apk/go 共 18 个 Dockerfile 的内网端点改为 `ARG` 可覆盖，默认值=公网官方源（pypi.org / dl-cdn.alpinelinux.org / proxy.golang.org）。开源用户零配置可构建。
- [x] **内网值注入通道**：compose `build.args`（`${VAR:-公网默认}` 缺省回落）+ `deploy/server/.env.server` 定义 AnyHaven 端点。本机部署缓存收益不变。
- [x] **uv.lock 出 git**：`projects/EventManager/uv.lock` 已 untrack + gitignore（lock 绑定生成环境，内网生成不入仓；本机磁盘文件照常存在）。
- [x] **k8s secret 出 git**：`TaskManager/k8s/02-secret.yaml` untrack + example 模板入库。
- [x] **OIDC secret env 化**：`ReleaseManager/.../oidc_client.py` 改为 `os.environ.get("OIDC_CLIENT_SECRET", 演示值)`。
- [x] **npm lockfile**：resolved 统一 npmmirror（公网可访问，开源用户可用），无需再动。
- [x] **临时产物**：`_httponly-knowledge-card.html` 已归档至 `~/backups/2026-09-14-archives/`。

## 二、发布日动作（预计半天）

1. **敏感复扫**（发布前最后一道闸）：
   ```bash
   git grep -nE '192\.168\.|\.home\.ailexc\.com'          # 内网拓扑，确认无凭据
   git grep -nEi '(password|secret|token)\s*[:=]\s*["'"'"'][^"'"'"']{6,}'  # 复核 demo 凭据均为演示值
   ```
2. **deploy 三套 env 换 example**：`deploy/{server,local,cloud}/.env.*` 从 git 移除、生成占位符版 `.example`（当前 `.gitignore` 白名单是有意设计——demo .env 一键部署——发布时重新评估是否保留该白名单）。
3. **文档面向外人打磨**：README 补"内网缓存加速（可选）"一节（AnyHaven 不开源，只描述标准 registry 配置方式）；演示凭据（admin123 等）注明"演示环境专用"。
4. **LICENSE 选择**：建议 MIT/Apache-2.0（含大量演示代码，宽松型合适）。
5. **干净机器彩排（最终验收）**：全新 `git clone` → 不配任何内网变量 → `make start` 全栈可跑（走公网源，慢但能通）。
6. **发布**：push 公开仓库。

## 三、期间观察项

- [ ] **uv 官方 proxy-for**（astral-sh/uv PR #20790）合并后：EventManager 的 `[[tool.uv.index]]` 块从 pyproject 移除（开源版），lock 重新生成为公网 canonical URL，AnyHaven 流量走 proxy-for 配置——届时本清单 uv 相关项全部作废，一行切换。
