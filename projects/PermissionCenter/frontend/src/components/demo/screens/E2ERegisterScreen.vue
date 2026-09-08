<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">应用管理 / <b>注册应用</b></div><div class="mock-user">👤 小黄</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📦 注册应用</h2>
      <p class="mock-sub">应用注册三步走：基础信息 → 鉴权方式 → 网络信息</p>

      <div class="reg-grid">
        <!-- 基础信息 -->
        <div class="reg-card">
          <div class="rc-header"><span class="rc-num">1</span><span class="rc-title">基础信息</span></div>
          <div class="rc-rows">
            <div class="rc-row"><span class="k">应用名称</span><span class="v">小黄的监控服务</span></div>
            <div class="rc-row"><span class="k">编码</span><span class="v mono">monitor</span></div>
            <div class="rc-row"><span class="k">描述</span><span class="v">主机监控与告警服务</span></div>
            <div class="rc-row"><span class="k">负责人</span><span class="v">👤 小黄 + 👤 admin（≥2人）</span></div>
            <div class="rc-row"><span class="k">状态</span><span class="v tag active">active</span></div>
          </div>
        </div>

        <!-- 鉴权方式 -->
        <div class="reg-card">
          <div class="rc-header"><span class="rc-num">2</span><span class="rc-title">鉴权方式注册</span></div>
          <div class="rc-rows">
            <div class="rc-row"><span class="k">方式</span><span class="v tag blue">Client Credentials</span></div>
            <div class="rc-row"><span class="k">Client ID</span><span class="v mono">client:cloud-mgmt</span></div>
            <div class="rc-row"><span class="k">Client Secret</span><span class="v mono">••••••••••••</span></div>
            <div class="rc-row"><span class="k">Token 端点</span><span class="v mono text-sm">/v1/auth/token</span></div>
            <div class="rc-row"><span class="k">有效期</span><span class="v">3600s（自动续期）</span></div>
          </div>
        </div>

        <!-- 网络信息 -->
        <div class="reg-card">
          <div class="rc-header"><span class="rc-num">3</span><span class="rc-title">网络信息登记</span></div>
          <div class="rc-rows">
            <div class="rc-row"><span class="k">网关白名单</span><span class="v mono">10.0.0.0/8</span></div>
            <div class="rc-row"><span class="k">回调域名</span><span class="v mono">cloud-mgmt.internal</span></div>
            <div class="rc-row"><span class="k">出口 IP</span><span class="v mono">10.0.1.100</span></div>
            <div class="rc-row"><span class="k">网络策略</span><span class="v tag green">已放行</span></div>
          </div>
        </div>
      </div>

      <div class="result-banner ok"><span>✅</span><span>应用注册成功！小黄成为应用 Owner，可管理该应用下的能力包</span></div>

      <div class="key-point"><span>💡</span><span>注册时强制要求 ≥2 负责人，确保应用不因单人离职而失管。鉴权方式支持 Client Credentials / JWT / API Key 三种。网络信息用于网关白名单自动配置。</span></div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 14px 20px; overflow: auto; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 11px; color: var(--text-secondary); margin-bottom: 10px; }
.reg-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px; }
.reg-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.rc-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.rc-num { width: 20px; height: 20px; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0; }
.rc-title { font-size: 12px; font-weight: 600; color: var(--text); }
.rc-rows { display: flex; flex-direction: column; gap: 2px; }
.rc-row { display: flex; gap: 6px; padding: 3px 0; font-size: 10px; }
.k { color: var(--text-tertiary); min-width: 52px; flex-shrink: 0; }
.v { color: var(--text); font-weight: 500; }
.v.mono { font-family: var(--font-mono); font-size: 9px; }
.v.text-sm { font-size: 9px; }
.tag { font-size: 9px; padding: 1px 6px; border-radius: 6px; font-weight: 600; }
.tag.active { color: var(--success); background: var(--success-bg); }
.tag.blue { color: var(--brand); background: var(--brand-soft); }
.tag.green { color: var(--success); background: var(--success-bg); }
.result-banner { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; margin-bottom: 8px; }
.result-banner.ok { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.key-point { display: flex; gap: 8px; padding: 8px 12px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 6px; font-size: 10px; color: var(--info); line-height: 1.5; }
</style>
