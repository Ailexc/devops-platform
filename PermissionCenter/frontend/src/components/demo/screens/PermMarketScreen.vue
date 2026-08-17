<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">权限市场</div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🏪 权限市场</h2>
      <p class="mock-sub">两大申请维度 —— 先打通应用访问，再申请具体能力</p>

      <div class="dim-grid">
        <!-- 应用授权申请 -->
        <div class="dim-card">
          <div class="dc-header blue">
            <div class="dc-icon">🔑</div>
            <div class="dc-title">应用授权申请</div>
          </div>
          <div class="dc-desc">申请对某个应用的鉴权方式和网络打通 —— 解决「能不能访问」的问题</div>
          <div class="dc-steps">
            <div class="dc-step"><span class="ds-num">1</span>浏览应用市场，选择目标应用</div>
            <div class="dc-step"><span class="ds-num">2</span>选择鉴权方式（Client Credentials / JWT / API Key）</div>
            <div class="dc-step"><span class="ds-num">3</span>申请网络打通（网关白名单 / VPN / 专线）</div>
            <div class="dc-step"><span class="ds-num">4</span>提交审批 → 审批通过 → 获取凭证 + 网络放行</div>
          </div>
          <div class="dc-example">
            <div class="dc-ex-title">示例</div>
            <div class="dc-ex-row">bob-data（程序）申请「监控服务」的 Client Credentials + 网关白名单</div>
          </div>
          <div class="dc-tag">前置条件：先有应用授权，才能申请能力包</div>
        </div>

        <!-- 能力包申请 -->
        <div class="dc-card highlight">
          <div class="dc-header green">
            <div class="dc-icon">📦</div>
            <div class="dc-title">能力包申请</div>
          </div>
          <div class="dc-desc">在已授权的应用内，申请具体的接口权限和数据范围 —— 解决「能用哪些能力」的问题</div>
          <div class="dc-steps">
            <div class="dc-step"><span class="ds-num">1</span>浏览能力市场，选择能力包</div>
            <div class="dc-step"><span class="ds-num">2</span>选择预设（只读/完整/自定义）</div>
            <div class="dc-step"><span class="ds-num">3</span>选择授权主体 + 数据范围</div>
            <div class="dc-step"><span class="ds-num">4</span>提交审批 → 审批通过 → 策略自动创建</div>
          </div>
          <div class="dc-example">
            <div class="dc-ex-title">示例</div>
            <div class="dc-ex-row">bob 申请「主机监控」只读预设（host:list + host:read + env=prod）</div>
          </div>
          <div class="dc-tag">应用授权是能力包的前置条件</div>
        </div>
      </div>

      <div class="key-point"><span>💡</span><span>关系：应用授权（打通访问）→ 能力包申请（细粒度权限）。程序身份需要先获得应用授权（Client Credentials + 网络白名单），再通过能力包申请具体的接口和数据权限。</span></div>
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
.dim-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.dim-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.dim-card.highlight { border-color: var(--success); background: var(--success-bg); }
.dc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.dc-icon { font-size: 18px; }
.dc-title { font-size: 13px; font-weight: 600; color: var(--text); }
.dc-desc { font-size: 10px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.4; }
.dc-steps { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; }
.dc-step { display: flex; align-items: center; gap: 6px; padding: 3px 6px; background: var(--bg-secondary); border-radius: 4px; font-size: 10px; color: var(--text); }
.ds-num { width: 14px; height: 14px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: 700; flex-shrink: 0; }
.dc-example { background: var(--bg-secondary); border-radius: 6px; padding: 6px 8px; margin-bottom: 6px; }
.dc-ex-title { font-size: 9px; font-weight: 600; color: var(--text-tertiary); margin-bottom: 2px; }
.dc-ex-row { font-size: 10px; color: var(--text); }
.dc-tag { font-size: 9px; color: var(--text-tertiary); font-style: italic; }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 11px; color: var(--info); line-height: 1.5; }
</style>
