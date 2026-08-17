<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">审批中心</div><div class="mock-user">👤 小黄</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📋 审批链路</h2>
      <div class="chain-flow">
        <div class="chain-step done"><span class="cs-icon">👤</span><div><div class="cs-name">申请人确认</div><div class="cs-desc">小红本人确认</div></div><span class="cs-status ok">✅ 已确认</span></div>
        <div class="chain-arrow">↓</div>
        <div class="chain-step done"><span class="cs-icon">👤</span><div><div class="cs-name">Owner 审批</div><div class="cs-desc">小黄（应用负责人）</div></div><span class="cs-status ok">✅ 已通过</span></div>
        <div class="chain-arrow">↓</div>
        <div class="chain-step done"><span class="cs-icon">🛡️</span><div><div class="cs-name">平台复核</div><div class="cs-desc">admin（管理员）</div></div><span class="cs-status ok">✅ 已通过</span></div>
      </div>
      <div class="sod-card">
        <div class="sod-title">🔒 SoD 职责分离</div>
        <div class="sod-row">✅ 申请人 ≠ 审批人（小红不能审批自己的申请）</div>
        <div class="sod-row">✅ 高风险操作追加安全复核（admin 审批）</div>
        <div class="sod-row">✅ 低风险操作自动审批（只读权限）</div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 20px 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 16px; }
.chain-flow { max-width: 40%; margin: 0 auto 20px; }
.chain-step { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 4px; }
.chain-step.done { border-color: var(--success); background: var(--success-bg); }
.cs-icon { font-size: 20px; }
.cs-name { font-size: 13px; font-weight: 600; color: var(--text); }
.cs-desc { font-size: 11px; color: var(--text-tertiary); }
.cs-status { margin-left: auto; font-size: 11px; font-weight: 600; }
.cs-status.ok { color: var(--success); }
.chain-arrow { text-align: center; color: var(--text-tertiary); font-size: 14px; padding: 2px 0; }
.sod-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
.sod-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.sod-row { font-size: 12px; color: var(--text-secondary); padding: 4px 0; }
</style>
