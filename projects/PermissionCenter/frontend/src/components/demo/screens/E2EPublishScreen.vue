<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">应用管理 / 小黄的监控服务 / <b>发布能力</b></div><div class="mock-user">👤 小黄</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📦 发布能力包</h2>
      <p class="mock-sub">声明能力 → 配置预设（接口+数据范围+主体）→ 上架市场</p>

      <div class="pub-grid">
        <!-- 声明能力 -->
        <div class="pub-card">
          <div class="pc-header"><span class="pc-num">1</span><span class="pc-title">声明能力</span></div>
          <div class="pc-rows">
            <div class="pc-row"><span class="k">能力名称</span><span class="v">主机监控</span></div>
            <div class="pc-row"><span class="k">数据模型</span><span class="v mono">host（主机）</span></div>
            <div class="pc-row"><span class="k">描述</span><span class="v">主机列表查看与详情读取</span></div>
            <div class="pc-row"><span class="k">标签</span><span class="v"><span class="tag">host</span><span class="tag">监控</span></span></div>
          </div>
          <div class="pc-note">从 OpenAPI 自动解析接口列表</div>
        </div>

        <!-- 配置预设 -->
        <div class="pc-main">
          <div class="pc-header"><span class="pc-num">2</span><span class="pc-title">配置预设</span></div>
          <p class="pc-desc">预设 = 接口绑定 + 数据范围 + 可申请主体，用户申请时选预设即可</p>

          <div class="preset-box">
            <div class="preset-name">🔖 只读监控 <span class="tag draft">草稿</span></div>
            <div class="preset-section">
              <div class="ps-label">🔌 绑定接口</div>
              <div class="ps-items">
                <span class="api on">✅ host:list <span class="method get">GET</span></span>
                <span class="api on">✅ host:read <span class="method get">GET</span></span>
                <span class="api off">⬜ host:create <span class="method post">POST</span></span>
                <span class="api off">⬜ host:update <span class="method put">PUT</span></span>
              </div>
            </div>
            <div class="preset-section">
              <div class="ps-label">🔐 数据范围</div>
              <div class="ps-items">
                <span class="scope-chip active">🌍 prod</span>
                <span class="scope-chip active">📍 cn-north</span>
                <span class="scope-chip active">📍 cn-south</span>
              </div>
              <div class="ps-expr"><code>env == "prod" && region in ["cn-north","cn-south"]</code></div>
            </div>
            <div class="preset-section">
              <div class="ps-label">👥 可申请主体</div>
              <div class="ps-items">
                <span class="scope-chip active">👤 人员</span>
                <span class="scope-chip active">🏢 组织</span>
                <span class="scope-chip">👥 自建组</span>
              </div>
            </div>
          </div>

          <div class="preset-box" style="opacity:0.6">
            <div class="preset-name">🔖 完整监控 <span class="tag draft">草稿</span></div>
            <div class="preset-desc">5 个接口（list+read+create+update+delete）· 无数据范围限制</div>
          </div>
        </div>

        <!-- 上架市场 -->
        <div class="pub-card">
          <div class="pc-header"><span class="pc-num">3</span><span class="pc-title">上架市场</span></div>
          <div class="pc-flow">
            <div class="flow-step done"><span>1</span>点击「🚀 上架」按钮</div>
            <div class="flow-arrow">↓</div>
            <div class="flow-step done"><span>2</span>Owner 确认 + 平台复核</div>
            <div class="flow-arrow">↓</div>
            <div class="flow-step done"><span>3</span>预设 status → published</div>
            <div class="flow-arrow">↓</div>
            <div class="flow-step result"><span>🏪</span>能力市场可见</div>
          </div>
        </div>
      </div>

      <div class="key-point"><span>💡</span><span>预设是能力包的核心配置单元：绑定哪些接口（动作级）+ 数据范围控制（实例级）+ 谁可以申请。用户申请时只需选预设，无需逐个配置。</span></div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 12px 18px; overflow: auto; }
.mock-title { font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 10px; color: var(--text-secondary); margin-bottom: 8px; }
.pub-grid { display: grid; grid-template-columns: 22% 1fr 20%; gap: 8px; margin-bottom: 8px; }
.pub-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.pc-header { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; padding-bottom: 5px; border-bottom: 1px solid var(--border); }
.pc-num { width: 18px; height: 18px; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; flex-shrink: 0; }
.pc-title { font-size: 11px; font-weight: 600; color: var(--text); }
.pc-rows { display: flex; flex-direction: column; gap: 1px; }
.pc-row { display: flex; gap: 4px; padding: 2px 0; font-size: 10px; }
.k { color: var(--text-tertiary); min-width: 48px; }
.v { color: var(--text); font-weight: 500; }
.v.mono { font-family: var(--font-mono); font-size: 9px; }
.tag { font-size: 8px; padding: 1px 5px; border-radius: 4px; background: var(--bg-tertiary); color: var(--text-tertiary); font-weight: 500; }
.tag.draft { color: var(--warning); background: var(--warning-bg); }
.pc-note { font-size: 9px; color: var(--text-tertiary); margin-top: 4px; font-style: italic; }
.pc-main { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.pc-desc { font-size: 10px; color: var(--text-secondary); margin-bottom: 8px; }
.preset-box { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; }
.preset-box:last-child { margin-bottom: 0; }
.preset-name { font-size: 11px; font-weight: 600; color: var(--text); margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.preset-desc { font-size: 9px; color: var(--text-tertiary); }
.preset-section { margin-bottom: 6px; }
.ps-label { font-size: 9px; font-weight: 600; color: var(--text-tertiary); margin-bottom: 3px; }
.ps-items { display: flex; gap: 3px; flex-wrap: wrap; }
.api { font-size: 9px; font-family: var(--font-mono); padding: 2px 5px; border-radius: 3px; display: inline-flex; align-items: center; gap: 3px; }
.api.on { background: var(--success-bg); color: var(--success); }
.api.off { background: var(--bg-tertiary); color: var(--text-tertiary); }
.method { font-size: 7px; font-weight: 700; padding: 0 3px; border-radius: 2px; }
.method.get { background: var(--success-bg); color: var(--success); }
.method.post { background: var(--warning-bg); color: var(--warning); }
.method.put { background: var(--info-bg); color: var(--info); }
.scope-chip { font-size: 9px; padding: 2px 6px; border-radius: 10px; border: 1px solid var(--border); color: var(--text-tertiary); }
.scope-chip.active { border-color: var(--brand); background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.ps-expr { margin-top: 3px; }
.ps-expr code { font-family: var(--font-mono); font-size: 8px; background: #1e293b; color: #38bdf8; padding: 2px 6px; border-radius: 3px; }
.pc-flow { display: flex; flex-direction: column; gap: 2px; }
.flow-step { display: flex; align-items: center; gap: 5px; padding: 4px 6px; background: var(--bg-secondary); border-radius: 4px; font-size: 9px; color: var(--text); }
.flow-step span { width: 14px; height: 14px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 7px; font-weight: 700; flex-shrink: 0; }
.flow-step.result { background: var(--success-bg); color: var(--success); font-weight: 600; }
.flow-step.result span { background: var(--success); color: #fff; font-size: 9px; }
.flow-arrow { text-align: center; color: var(--text-tertiary); font-size: 10px; }
.key-point { display: flex; gap: 6px; padding: 6px 10px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 6px; font-size: 9px; color: var(--info); line-height: 1.5; }
</style>
