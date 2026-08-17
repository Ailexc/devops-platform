<template>
  <div class="mock-screen submit-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">能力市场 / 主机监控 / 选择预设 / 选择主体 / <b>确认申请</b></div>
      <div class="mock-user">👤 小红</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">📋 确认申请</h2>

      <div class="summary-card">
        <div class="sum-section">
          <div class="sum-label">能力包</div>
          <div class="sum-val">📡 小黄的监控服务 — 主机监控</div>
        </div>
        <div class="sum-section">
          <div class="sum-label">预设</div>
          <div class="sum-val">🔖 只读监控（host:list, host:read）</div>
        </div>
        <div class="sum-section">
          <div class="sum-label">授权主体</div>
          <div class="sum-subjects">
            <div class="subject-chip">👤 小红（人员）</div>
            <div class="subject-chip">🔌 小红的数据分析（程序）</div>
          </div>
        </div>
        <div class="sum-section">
          <div class="sum-label">申请理由</div>
          <div class="reason-box">需要读取生产环境主机，用于日常巡检和监控数据分析</div>
        </div>
      </div>

      <div class="risk-banner low">
        <span class="risk-icon">🟢</span>
        <span>风险评估：<strong>低风险</strong> — 仅读取权限，可自动审批</span>
      </div>

      <div class="submit-banner success">
        <span>✅</span>
        <span>申请已提交！系统生成申请单 <strong>#25</strong>，等待审批。</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px; }
.summary-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 18px; margin-bottom: 14px; }
.sum-section { padding: 8px 0; border-bottom: 1px solid var(--border); }
.sum-section:last-child { border-bottom: none; }
.sum-label { font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px; }
.sum-val { font-size: 14px; font-weight: 500; color: var(--text); }
.sum-subjects { display: flex; gap: 8px; flex-wrap: wrap; }
.subject-chip { font-size: 13px; padding: 4px 12px; border-radius: 6px; background: var(--brand-soft); color: var(--brand); font-weight: 500; }
.reason-box { font-size: 13px; color: var(--text); padding: 8px 12px; background: var(--bg-secondary); border-radius: 6px; }
.risk-banner { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 14px; }
.risk-banner.low { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.risk-icon { font-size: 18px; }
.submit-banner { display: flex; align-items: center; gap: 8px; padding: 14px 18px; border-radius: 10px; font-size: 14px; font-weight: 600; }
.submit-banner.success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
</style>
