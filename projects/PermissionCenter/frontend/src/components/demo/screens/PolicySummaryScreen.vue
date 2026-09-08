<template>
  <div class="mock-screen summary-screen">
    <div class="summary-content">
      <div class="celebrate-icon">🎉</div>
      <h2 class="summary-title">策略全生命周期总结</h2>

      <div class="lifecycle">
        <div class="lc-item blue"><div class="lc-icon">⚡</div><div class="lc-name">触发</div><div class="lc-desc">业务操作触发</div></div>
        <div class="lc-arrow">→</div>
        <div class="lc-item violet"><div class="lc-icon">📋</div><div class="lc-name">审批</div><div class="lc-desc">多级审批链</div></div>
        <div class="lc-arrow">→</div>
        <div class="lc-item green"><div class="lc-icon">✅</div><div class="lc-name">生效</div><div class="lc-desc">策略自动创建</div></div>
        <div class="lc-arrow">→</div>
        <div class="lc-item cyan"><div class="lc-icon">🌐</div><div class="lc-name">执行</div><div class="lc-desc">网关实时鉴权</div></div>
        <div class="lc-arrow">→</div>
        <div class="lc-item red"><div class="lc-icon">🔄</div><div class="lc-name">回收</div><div class="lc-desc">权限即时失效</div></div>
      </div>

      <div class="feature-grid">
        <div class="feat"><span>🔗</span><span>审批即策略：审批通过自动创建，无需手动配置</span></div>
        <div class="feat"><span>🔒</span><span>SoD 职责分离：申请人≠审批人，高风险追加复核</span></div>
        <div class="feat"><span>⚡</span><span>即时生效：策略创建后网关立即执行，无延迟</span></div>
        <div class="feat"><span>🔄</span><span>可回收：下架/回收操作即时删除策略，权限立即失效</span></div>
        <div class="feat"><span>📊</span><span>全链路溯源：每条策略关联申请单，审计日志完整</span></div>
        <div class="feat"><span>🧩</span><span>双引擎：Casbin 动作级 + OpenFGA 实例级，细粒度控制</span></div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--success-bg) 0%, var(--bg) 50%, var(--brand-soft) 100%); }
.summary-content { text-align: center; max-width: 55%; }
.celebrate-icon { font-size: 44px; margin-bottom: 8px; animation: bounce 1s ease infinite; }
.summary-title { font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 16px; }
.lifecycle { display: flex; align-items: center; justify-content: center; gap: 4px; margin-bottom: 18px; }
.lc-item { padding: 10px 12px; border-radius: 10px; text-align: center; min-width: 72px; }
.lc-item.blue { background: rgba(47,111,237,0.1); border: 1px solid var(--brand); }
.lc-item.violet { background: rgba(124,58,237,0.1); border: 1px solid var(--purple); }
.lc-item.green { background: rgba(22,163,74,0.1); border: 1px solid var(--success); }
.lc-item.cyan { background: rgba(8,145,178,0.1); border: 1px solid var(--info); }
.lc-item.red { background: rgba(220,38,38,0.1); border: 1px solid var(--danger); }
.lc-icon { font-size: 18px; margin-bottom: 2px; }
.lc-name { font-size: 12px; font-weight: 600; color: var(--text); }
.lc-desc { font-size: 9px; color: var(--text-secondary); }
.lc-arrow { font-size: 16px; color: var(--text-tertiary); }
.feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.feat { display: flex; align-items: center; gap: 6px; padding: 7px 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; font-size: 11px; color: var(--text); }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
</style>
