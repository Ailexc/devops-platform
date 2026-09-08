<template>
  <div class="mock-screen summary-screen">
    <div class="summary-content">
      <div class="celebrate-icon">🎉</div>
      <h2 class="summary-title">个人权限板块总结</h2>

      <div class="summary-grid">
        <div class="sum-card personal">
          <div class="sc-icon">👤</div>
          <div class="sc-name">个人权限</div>
          <div class="sc-desc">个人通过能力市场申请<br>审批通过后直接授予</div>
          <div class="sc-example">主机监控、数据库管理、工单管理</div>
        </div>
        <div class="sum-card org">
          <div class="sc-icon">🏢</div>
          <div class="sc-name">组织权限</div>
          <div class="sc-desc">组织树继承，组即角色<br>加入组织自动获得</div>
          <div class="sc-example">主机管理、网络管理</div>
        </div>
        <div class="sum-card group">
          <div class="sc-icon">👥</div>
          <div class="sc-name">自建组权限</div>
          <div class="sc-desc">临时/专项授权<br>支持 TTL 有效期</div>
          <div class="sc-example">安全巡检</div>
        </div>
      </div>

      <div class="formula">
        <div class="formula-label">权限计算公式</div>
        <code>最终权限 = 个人权限 ∪ 组织权限 ∪ 自建组权限</code>
      </div>

      <div class="feature-list">
        <div class="feat"><span>🔗</span><span>每条权限关联申请单，授权来源可追溯</span></div>
        <div class="feat"><span>🔒</span><span>所有授权走审批链（SoD：申请人≠审批人）</span></div>
        <div class="feat"><span>⏰</span><span>自建组支持 TTL，到期自动回收权限</span></div>
        <div class="feat"><span>📊</span><span>工作台四维统计，权限分布一目了然</span></div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--brand-soft) 0%, var(--bg) 50%, var(--purple-bg) 100%); }
.summary-content { text-align: center; max-width: 55%; }
.celebrate-icon { font-size: 48px; margin-bottom: 10px; animation: bounce 1s ease infinite; }
.summary-title { font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 18px; }
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.sum-card { padding: 14px 10px; border-radius: 10px; text-align: center; }
.sum-card.personal { background: rgba(47,111,237,0.1); border: 1px solid var(--brand); }
.sum-card.org { background: rgba(124,58,237,0.1); border: 1px solid var(--purple); }
.sum-card.group { background: rgba(217,119,6,0.1); border: 1px solid var(--warning); }
.sc-icon { font-size: 24px; margin-bottom: 4px; }
.sc-name { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.sc-desc { font-size: 10px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 6px; }
.sc-example { font-size: 9px; color: var(--text-tertiary); font-style: italic; }
.formula { background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; }
.formula-label { font-size: 10px; color: #94a3b8; margin-bottom: 4px; }
.formula code { font-family: var(--font-mono); font-size: 13px; color: #38bdf8; }
.feature-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.feat { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; font-size: 11px; color: var(--text); }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
</style>
