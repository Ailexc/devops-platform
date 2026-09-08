# 🚀 DevOps 平台全家桶 · 展示页（Showcase）

> 一个 **单文件、零构建、可静态部署** 的滚动画卷式项目介绍页，用于面试展示个人作品集。
> 结构：统一门户 → 全家桶概览 → 架构逐层动画 → 7 个系统深挖（含模拟 UI）→ 技术栈 → 部署 → 跳转统一门户。

---

## 快速预览

直接用浏览器打开即可（无需任何构建）：

```bash
# 方式一：双击文件
open showcase/index.html

# 方式二：本地起一个静态服务（推荐，便于后续调试）
cd showcase && python3 -m http.server 8080
# 访问 http://localhost:8080
```

## 自定义配置

打开 `index.html` 顶部 `CONFIG` 对象，改两个常量即可：

```js
const CONFIG = {
  // 🔧 统一门户地址：本地是 Authentication 的 portal；部署后替换为公网地址
  portalUrl: 'http://portal.authentication.orb.local',
  // 🔧 GitHub 仓库地址（可选）：填了之后「查看项目详情」会指向对应目录；留空则跳 #
  githubRepo: '',
};
```

| 配置项 | 作用 |
|--------|------|
| `portalUrl` | 页面顶部导航、末尾 CTA、页脚「统一门户」按钮跳转地址 |
| `githubRepo` | 系统卡片 / 详情链接的仓库前缀，例如 `https://github.com/yourname/DevOpsPlatform` |

## 部署（三选一，均免费）

### 1. GitHub Pages（推荐）

```bash
# 在仓库 Settings → Pages → Source 选择分支 + /docs 目录 或 单独分支
# 若想从仓库根目录直接部署 index.html，把本文件复制到根目录即可
```

### 2. Cloudflare Pages

```bash
npx wrangler pages deploy showcase --project-name=devops-platform
```

### 3. Render 静态站点 / Netlify / Vercel

- **Render**：New → Static Site → Root Directory 填 `showcase`
- **Netlify / Vercel**：直接拖拽 `showcase/` 文件夹上传即可

> 本页是**纯静态单文件**，任意静态托管都能跑，不需要后端。

## 技术说明

- **滚动动画**：GSAP + ScrollTrigger（CDN 引入）。若 CDN 不可达（如离线面试），页面自动降级为「全部内容直接可见」，不会白屏。
- **架构展开动画**：纯原生 JS（rAF 轮询 + scroll 事件双保险）驱动，不依赖 GSAP，任何环境都可靠。
- **界面素材**：7 个系统全部用 **CSS 模拟 UI** 呈现，无需真实截图。
- **离线可用**：除了 Google Fonts / GSAP 两个 CDN（都有系统字体与降级兜底），无任何其他外部依赖。

## 内容结构

| 区块 | 说明 |
|------|------|
| Hero | 一句话定位 + 核心数字 + 技术跑马灯 |
| 全家桶总览 | 7 个系统卡片速览 |
| 整体架构 | 滚动逐层点亮：接入层 → 门户 → 网关认证 → 系统矩阵 → 基础设施 |
| 系统深挖 ×7 | 每系统定位 / 技术栈 / 面试亮点 + 模拟 UI 窗口 |
| 技术栈全景 | 6 大分类技术选型 |
| 部署形态 | 本地 OrbStack / Render 免费 / 静态托管 |
| 结尾 CTA | 「进入统一门户」按钮 |

---

部署后记得把 `CONFIG.portalUrl` 换成你的公网统一门户地址，这样面试官点「进入统一门户」就能直达真实系统。
