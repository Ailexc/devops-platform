<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">能力市场</div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🏪 Step 3：申请能力</h2>
      <p class="mock-sub">普通用户在能力市场浏览 → 选预设 → 选主体 → 选数据范围 → 提交申请</p>

      <div class="apply-flow">
        <div class="af-step"><div class="af-num">1</div><div class="af-info"><div class="af-title">浏览市场</div><div class="af-desc">发现「小黄的监控服务 - 主机监控」，2 个预设已上架</div></div></div>
        <div class="af-arrow">↓</div>
        <div class="af-step"><div class="af-num">2</div><div class="af-info"><div class="af-title">选择预设</div><div class="af-desc">选择「只读监控」（host:list + host:read）</div></div></div>
        <div class="af-arrow">↓</div>
        <div class="af-step"><div class="af-num">3</div><div class="af-info"><div class="af-title">选择主体</div><div class="af-desc">双主体：👤 bob（人）+ 🔌 bob-data（程序）</div></div></div>
        <div class="af-arrow">↓</div>
        <div class="af-step"><div class="af-num">4</div><div class="af-info"><div class="af-title">数据范围</div><div class="af-desc">env == "prod" && region in ["cn-north","cn-south"]</div></div></div>
        <div class="af-arrow">↓</div>
        <div class="af-step"><div class="af-num">5</div><div class="af-info"><div class="af-title">提交申请</div><div class="af-desc">理由：生产环境主机巡检 → 生成申请单 #30</div></div></div>
        <div class="af-arrow">↓</div>
        <div class="af-step result"><span>📋</span><div class="af-info"><div class="af-title">申请单已创建</div><div class="af-desc">进入审批流程，等待 Owner 和管理员审批</div></div></div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 16px 22px; overflow: auto; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 11px; color: var(--text-secondary); margin-bottom: 12px; }
.apply-flow { max-width: 42%; margin: 0 auto; }
.af-step { display: flex; gap: 8px; padding: 8px 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; }
.af-step.result { border-color: var(--success); background: var(--success-bg); }
.af-num { width: 22px; height: 22px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0; }
.af-step.result .af-num { background: var(--success); color: #fff; font-size: 12px; }
.af-title { font-size: 12px; font-weight: 600; color: var(--text); }
.af-desc { font-size: 10px; color: var(--text-secondary); }
.af-arrow { text-align: center; color: var(--text-tertiary); font-size: 12px; }
</style>
