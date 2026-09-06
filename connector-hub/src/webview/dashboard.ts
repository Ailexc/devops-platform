import * as vscode from 'vscode';
import { Connector } from '../registry';
import { HealthResult } from '../doctor';
import { IdentityInfo } from '../larkAuth';
import { InjectionReport } from '../injection';
import { InstallInfo, DomainInfo, SkillInfo, UpdateInfo, ToolCardInfo, DomainCardInfo } from '../larkInfo';

export interface DashboardState {
  version?: string;
  identity?: IdentityInfo;
  health: Record<string, HealthResult>;
  injection?: InjectionReport;
  connectors: Connector[];
  authFlow?: {
    phase: 'idle' | 'setting-up' | 'authorizing';
    qrDataUrl?: string;
    url?: string;
    message?: string;
  };
  /** 阶段性成功横幅（如"应用创建成功"/"授权成功"），显示一次后由前端自动消失 */
  banner?: { kind: 'success' | 'info'; text: string };
  /** lark-cli 深度信息（安装位置/命令域/skills/更新） */
  install?: InstallInfo;
  domains?: DomainInfo[];
  skills?: SkillInfo[];
  update?: UpdateInfo;
  /** Copilot 工具卡片（运行时状态） */
  toolCards?: ToolCardInfo[];
  /** CLI 域卡片（含快捷命令与关联 skill） */
  domainCards?: DomainCardInfo[];
}

/** 生成仪表盘 HTML（VS Code 主题变量自适应，无外部依赖） */
export function renderDashboard(state: DashboardState, cspSource: string, nonce: string): string {
  const { identity, health, injection, connectors, authFlow, version } = state;

  const statusDot = (ok: boolean | undefined) =>
    ok === undefined ? '<span class="dot dot-idle"></span>' : ok ? '<span class="dot dot-ok"></span>' : '<span class="dot dot-bad"></span>';

  // —— lark-cli 主卡片（可折叠：头部常显，内容折叠） ——
  const upd = state.update;
  const updateBadge = upd
    ? upd.hasUpdate
      ? `<span class="state-tag state-warn">有新版 ${esc(upd.latest ?? '')}</span>`
      : `<span class="muted small">已是最新</span>`
    : '';

  const installHtml = state.install ? `
    <div class="kv"><span>安装位置</span><span class="mono small">${esc(shortPath(state.install.binPath))} <button class="mini-btn" data-cmd="copyBinPath" title="复制路径">⧉</button></span></div>
    ${state.install.pkgDir ? `<div class="kv"><span>包目录</span><span class="mono small">${esc(shortPath(state.install.pkgDir))}</span></div>` : ''}
    <div class="kv"><span>版本</span><span>${esc(state.version ?? '—')} ${updateBadge}</span></div>` : '';

  const domainsHtml = state.domainCards?.length ? `
    <div class="section">
      <div class="section-head" data-toggle="domains"><span class="chev">▸</span> CLI 命令域 <span class="badge">${state.domainCards.length}</span></div>
      <div class="section-body" id="domains">
        <div class="mech-note">
          <span class="muted small">机制：lark-cli 二进制内置的命令域（<span class="mono">lark-cli &lt;domain&gt; --help</span> 查看）。Agent 通过读取对应 Skill 后拼 CLI 命令使用。</span>
        </div>
        ${state.domainCards.map(d => `
          <div class="item-card" ${d.skillName ? `data-skill="${esc(d.skillName)}" title="点击查看 ${esc(d.skillName)} SKILL.md"` : ''}>
            <div class="item-head">
              <span class="item-name mono">${esc(d.name)}</span>
              ${d.skillName ? `<span class="state-tag state-ok">skill: ${esc(d.skillName)}${d.skillVersion ? ' ' + esc(d.skillVersion) : ''}</span>` : ''}
            </div>
            <div class="item-desc muted small">${esc(d.description)}</div>
            ${d.shortcuts.length ? `<div class="item-meta small mono">${d.shortcuts.map(s => esc(s)).join(' ')}</div>` : ''}
          </div>`).join('')}
      </div>
    </div>` : '';

  const skillsHtml = state.skills?.length ? `
    <div class="section">
      <div class="section-head" data-toggle="skills"><span class="chev">▸</span> 内置 Skills <span class="badge">${state.skills.length}</span></div>
      <div class="section-body" id="skills">
        ${state.skills.map(s => `
          <div class="skill-row" data-skill="${esc(s.name)}" title="点击查看 SKILL.md">
            <span class="skill-name">${esc(s.name)}</span>
            <span class="badge">${esc(s.version || '?')}</span>
            <div class="skill-desc muted small">${esc(s.description)}</div>
          </div>`).join('')}
      </div>
    </div>` : '';

  const toolsSectionHtml = state.toolCards?.length ? `
    <div class="section">
      <div class="section-head" data-toggle="tools"><span class="chev">▸</span> Copilot 工具 <span class="badge">${state.toolCards.filter(t => t.registered).length}/${state.toolCards.length}</span></div>
      <div class="section-body" id="tools">
        <div class="mech-note">
          <span class="muted small">机制：声明于 <span class="mono">package.json → languageModelTools</span>，实现于 <span class="mono">src/tools/lark.ts</span>，运行时经 <span class="mono">vscode.lm.registerTool</span> 注册，Copilot 自动感知并调用。</span>
        </div>
        ${state.toolCards.map(t => `
          <div class="item-card" data-copyref="${esc(t.name)}" title="点击复制 #${esc(t.name)}">
            <div class="item-head">
              <span class="risk-icon">${t.name.includes('overwrite') || t.name.includes('update') ? '⚠️' : t.name.includes('create') ? '✏️' : '👁'}</span>
              <span class="item-name mono">${esc(t.name)}</span>
              <span class="state-tag ${t.registered ? 'state-ok' : 'state-idle'}">${t.registered ? '已注册' : '未注册'}</span>
            </div>
            <div class="item-desc muted small">${esc(t.description)}</div>
            ${t.params.length ? `<div class="item-meta small">参数: ${t.params.map(p => esc(t.required.includes(p) ? p + '*' : p)).join(' · ')}</div>` : ''}
            <div class="item-meta small muted">引用: #${esc(t.name.replace(/_/g, ''))}（聊天中输入强制调用）</div>
          </div>`).join('')}
      </div>
    </div>` : '';

  // 注入检查项的机制说明与打开方式
  const injectionMeta: Record<string, { mech: string; openCmd: string; openLabel: string }> = {
    registry: {
      mech: 'Agent 的能力清单（单一事实来源）：每个连接器一条记录（路径/认证/工具声明），插件启动时解析它渲染面板、注册工具。任何新对话 Agent 都能从这里感知服务器有哪些能力。',
      openCmd: 'openRegistry',
      openLabel: '打开注册表'
    },
    doctor: {
      mech: '一键自检所有连接器可用性的 shell 脚本：汇总各连接器的 version/doctor 命令输出健康矩阵。Agent 不确定能力状态时先跑它，避免瞎猜。',
      openCmd: 'openDoctor',
      openLabel: '打开脚本'
    },
    tools: {
      mech: 'Copilot 工具注册：package.json 声明 + 运行时 vscode.lm.registerTool 配对。缺失时模型看不见对应工具，需重载窗口恢复。',
      openCmd: 'showToolDeps',
      openLabel: '查看依赖'
    }
  };

  const injectionSectionHtml = injection ? `
    <div class="section">
      <div class="section-head" data-toggle="injection"><span class="chev">▸</span> 注入检查 <span class="badge">${injection.allOk ? '✅' : '❌'}</span></div>
      <div class="section-body" id="injection">
        <div class="mech-note">
          <span class="muted small">机制：三件套一致性校验——注册表（数据）、doctor 脚本（自检）、Copilot 工具注册（执行）三者必须同步，缺一项 Agent 的能力感知就会出现盲区。</span>
        </div>
        ${injection.items.map(i => {
          const meta = injectionMeta[i.id];
          return `
          <div class="item-card" ${meta ? `data-cmd="${meta.openCmd}" title="点击${meta.openLabel}"` : ''}>
            <div class="item-head">
              <span class="risk-icon">${i.ok ? '✅' : '❌'}</span>
              <span class="item-name">${esc(i.label)}</span>
              <span class="state-tag ${i.ok ? 'state-ok' : 'state-warn'}">${i.ok ? '就绪' : '缺失'}</span>
            </div>
            ${meta ? `<div class="item-desc muted small">${esc(meta.mech)}</div>` : ''}
            <div class="item-meta small">${esc(i.detail)}${meta ? ` · <span class="mono">点击${meta.openLabel} →</span>` : ''}</div>
          </div>`;
        }).join('')}
        ${injection.allOk ? '' : '<div class="btn-row"><button class="btn btn-primary" data-cmd="fixInjection">🔧 一键修复</button></div>'}
      </div>
    </div>` : '';

  // 主卡片：身份状态 + 可折叠区块
  const larkCardHtml = `
    <div class="card ${identity?.authorized ? 'card-ok' : identity?.configured ? 'card-warn' : ''}">
      <div class="card-head" data-toggle="cardbody">
        <span class="chev chev-main">▾</span>
        ${statusDot(identity?.authorized)}
        <b>lark-cli</b>
        ${identity?.authorized ? '<span class="state-tag state-ok">③ 已就绪</span>' : identity?.configured ? '<span class="state-tag state-warn">② 待授权</span>' : '<span class="state-tag state-idle">① 未配置</span>'}
        <span class="badge">${version ?? ''}</span>
      </div>
      <div class="card-body" id="cardbody">
        ${identity?.authorized ? `
          <div class="kv"><span>用户</span><span>${esc(identity.user ?? '—')}</span></div>
          <div class="kv"><span>应用</span><span>${esc(identity.app ?? '—')}</span></div>
          <div class="kv"><span>Token 有效期至</span><span>${esc(identity.expiresAt ?? '—')}</span></div>` : ''}
        ${identity?.authorized ? '' : `
          <p class="muted small">${identity?.configured ? '应用已创建成功 ✅，还差最后一步：扫码授权文档权限后即可使用。' : '尚未创建飞书应用。点击下方按钮，用飞书 App 扫码即可自动创建并绑定。'}</p>`}
        ${installHtml}
        <div class="btn-row">
          ${!identity?.configured ? '<button class="btn btn-primary" data-cmd="setupApp">📱 一键创建应用</button>' : ''}
          ${identity?.configured && !identity?.authorized ? '<button class="btn btn-primary" data-cmd="startLogin">🔑 扫码授权</button>' : ''}
          ${identity?.authorized ? '<button class="btn" data-cmd="doctor">健康检查</button><button class="btn" data-cmd="startLogin">重新授权</button><button class="btn" data-cmd="checkUpdate">检查更新</button>' : ''}
        </div>
        ${toolsSectionHtml}
        ${injectionSectionHtml}
        ${domainsHtml}
        ${skillsHtml}
      </div>
    </div>`;

  // —— 授权流程区（二维码/进度，独立卡片） ——
  let authFlowHtml = '';
  if (authFlow && authFlow.phase !== 'idle') {
    const qr = authFlow.qrDataUrl
      ? `<img class="qr" src="${authFlow.qrDataUrl}" alt="二维码"/>`
      : `<div class="qr-placeholder"><span class="spin"></span></div>`;
    authFlowHtml = `
      <div class="card auth-card">
        <div class="card-head"><span class="spin"></span><b>${authFlow.phase === 'setting-up' ? '创建应用' : '扫码授权'}</b></div>
        ${qr}
        <p class="muted small center">${esc(authFlow.message ?? '请用飞书 App 扫码，完成后自动继续…')}</p>
        ${authFlow.url ? `<div class="btn-row"><button class="btn" data-cmd="copyUrl">复制链接</button></div>` : ''}
      </div>`;
  }

  // —— 成功横幅 ——
  const bannerHtml = state.banner
    ? `<div class="banner banner-${state.banner.kind}">${state.banner.kind === 'success' ? '🎉' : 'ℹ️'} ${esc(state.banner.text)}</div>`
    : '';

  return `<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; img-src ${cspSource} data:; script-src 'nonce-${nonce}';">
<style>
  :root { font-size: 13px; }
  body { padding: 10px; color: var(--vscode-foreground); font-family: var(--vscode-font-family); }
  .banner { border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; font-weight: 600; animation: fadein 0.3s ease; }
  .banner-success { background: rgba(78, 201, 176, 0.15); border: 1px solid var(--vscode-testing-iconPassed, #4ec9b0); color: var(--vscode-testing-iconPassed, #4ec9b0); }
  .banner-info { background: rgba(100, 150, 250, 0.12); border: 1px solid var(--vscode-focusBorder, #6496fa); }
  @keyframes fadein { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
  .card { border: 1px solid var(--vscode-panel-border); border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; background: var(--vscode-sideBar-background); }
  .card-ok { border-color: var(--vscode-testing-iconPassed, #4ec9b0); }
  .card-warn { border-color: var(--vscode-editorWarning-foreground, #cca700); }
  .state-tag { font-size: 11px; border-radius: 8px; padding: 1px 8px; font-weight: 600; }
  .state-ok { background: rgba(78, 201, 176, 0.18); color: var(--vscode-testing-iconPassed, #4ec9b0); }
  .state-warn { background: rgba(204, 167, 0, 0.18); color: var(--vscode-editorWarning-foreground, #cca700); }
  .state-idle { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); }
  .card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; cursor: pointer; user-select: none; }
  .chev { display: inline-block; transition: transform 0.15s; color: var(--vscode-descriptionForeground); font-size: 11px; width: 12px; }
  .chev-main { font-size: 13px; }
  .collapsed > .card-body { display: none; }
  .collapsed .chev-main { transform: rotate(-90deg); }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
  .dot-ok { background: var(--vscode-testing-iconPassed, #4ec9b0); }
  .dot-bad { background: var(--vscode-errorForeground, #f14c4c); }
  .dot-warn { background: var(--vscode-editorWarning-foreground, #cca700); }
  .dot-idle { background: var(--vscode-descriptionForeground, #888); }
  .badge { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 8px; padding: 1px 8px; font-size: 11px; }
  .muted { color: var(--vscode-descriptionForeground); }
  .small { font-size: 12px; }
  .mono { font-family: var(--vscode-editor-font-family); }
  .center { text-align: center; }
  .kv { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; align-items: center; }
  .kv > span:first-child { color: var(--vscode-descriptionForeground); flex-shrink: 0; }
  .kv > span:last-child { text-align: right; word-break: break-all; }
  .mini-btn { background: transparent; border: none; cursor: pointer; color: var(--vscode-descriptionForeground); padding: 0 2px; font-size: 12px; }
  .mini-btn:hover { color: var(--vscode-foreground); }
  .btn-row { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
  .btn { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: none; border-radius: 3px; padding: 5px 12px; cursor: pointer; font-size: 12px; }
  .btn:hover { background: var(--vscode-button-secondaryHoverBackground); }
  .btn-primary { background: var(--vscode-button-background); color: var(--vscode-button-foreground); }
  .btn-primary:hover { background: var(--vscode-button-hoverBackground); }
  .qr { display: block; margin: 8px auto; width: 180px; height: 180px; border-radius: 4px; }
  .qr-placeholder { width: 180px; height: 180px; margin: 8px auto; border: 1px dashed var(--vscode-panel-border); border-radius: 4px; display: flex; align-items: center; justify-content: center; }
  .spin { width: 14px; height: 14px; border: 2px solid var(--vscode-descriptionForeground); border-top-color: transparent; border-radius: 50%; display: inline-block; animation: spin 0.9s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .section { border-top: 1px solid var(--vscode-panel-border); margin-top: 8px; padding-top: 6px; }
  .section-head { display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; padding: 2px 0; font-weight: 600; font-size: 12px; }
  .section-head:hover { color: var(--vscode-foreground); }
  .section-head .chev { font-size: 10px; }
  .section.open .chev { transform: rotate(90deg); }
  .section-body { display: none; padding: 6px 0 2px 18px; }
  .section.open .section-body { display: block; }
  .tools { display: flex; flex-wrap: wrap; gap: 6px; }
  .tool-chip { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 4px; padding: 2px 8px; font-size: 11px; font-family: var(--vscode-editor-font-family); }
  .mech-note { background: var(--vscode-textCodeBlock-background, rgba(127,127,127,0.08)); border-left: 2px solid var(--vscode-focusBorder, #6496fa); border-radius: 3px; padding: 5px 8px; margin-bottom: 6px; }
  .item-card { border: 1px solid var(--vscode-panel-border); border-radius: 5px; padding: 6px 9px; margin-bottom: 6px; cursor: pointer; }
  .item-card:hover { background: var(--vscode-list-hoverBackground); border-color: var(--vscode-focusBorder, #6496fa); }
  .item-head { display: flex; align-items: center; gap: 7px; }
  .item-name { font-weight: 600; font-size: 12px; }
  .item-desc { margin-top: 2px; }
  .item-meta { margin-top: 2px; color: var(--vscode-descriptionForeground); }
  .risk-icon { font-size: 12px; }
  .skill-row { padding: 4px 0; border-bottom: 1px solid var(--vscode-panel-border); cursor: pointer; }
  .skill-row:last-child { border-bottom: none; }
  .skill-row:hover { background: var(--vscode-list-hoverBackground); border-radius: 3px; }
  .skill-name { font-family: var(--vscode-editor-font-family); font-size: 12px; font-weight: 600; margin-right: 6px; }
  .skill-desc { margin-top: 1px; }
  h2 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--vscode-descriptionForeground); margin: 14px 0 6px; }
</style>
</head>
<body>
  ${bannerHtml}
  ${larkCardHtml}
  ${authFlowHtml}
<script nonce="${nonce}">
  const vscode = acquireVsCodeApi();
  // 折叠/展开（事件委托，支持重渲染后依然有效）
  document.addEventListener('click', e => {
    const toggle = e.target.closest('[data-toggle]');
    if (toggle && !e.target.closest('[data-cmd]')) {
      const target = toggle.dataset.toggle;
      if (target === 'cardbody') {
        toggle.closest('.card').classList.toggle('collapsed');
      } else {
        const sec = toggle.closest('.section');
        sec.classList.toggle('open');
        toggle.querySelector('.chev').textContent = sec.classList.contains('open') ? '▾' : '▸';
      }
      return;
    }
    const skill = e.target.closest('[data-skill]');
    if (skill) { vscode.postMessage({ cmd: 'readSkill', name: skill.dataset.skill }); return; }
    const copyref = e.target.closest('[data-copyref]');
    if (copyref) { vscode.postMessage({ cmd: 'copyToolRef', name: copyref.dataset.copyref }); return; }
    const btn = e.target.closest('[data-cmd]');
    if (btn) vscode.postMessage({ cmd: btn.dataset.cmd });
  });
  // 成功横幅 8 秒后自动消失
  const banner = document.querySelector('.banner');
  if (banner) setTimeout(() => vscode.postMessage({ cmd: 'dismissBanner' }), 8000);
</script>
</body>
</html>`;
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** 路径缩短显示：~/.npm-global/bin/lark-cli */
function shortPath(p: string): string {
  const home = require('os').homedir();
  return p.startsWith(home) ? '~' + p.slice(home.length) : p;
}
