<template>
  <div class="mock-screen verify-screen">
    <div class="verify-content">
      <div class="celebrate-icon">🎉</div>
      <h2 class="verify-title">权限验证</h2>
      <p class="verify-desc">小红的数据分析程序访问主机 API</p>

      <div class="curl-card">
        <div class="curl-header">
          <span class="curl-label">Terminal</span>
        </div>
        <div class="curl-body">
          <div class="curl-line">
            <span class="prompt">$</span>
            <span class="cmd">curl -H "X-User: client:data-analysis" https://api.permission-center/hosts</span>
          </div>
          <div class="curl-output success">
            <span class="status">200 OK</span>
            <span class="result">✅ 允许</span>
          </div>
          <div class="curl-line">
            <span class="prompt">$</span>
            <span class="cmd">curl -X POST -H "X-User: client:data-analysis" https://api.permission-center/hosts</span>
          </div>
          <div class="curl-output error">
            <span class="status">403 Forbidden</span>
            <span class="result">🚫 拒绝</span>
          </div>
        </div>
      </div>

      <div class="summary-row">
        <div class="sum-item success">
          <div class="sum-icon">✅</div>
          <div class="sum-text">GET 主机列表</div>
          <div class="sum-val">200</div>
        </div>
        <div class="sum-item error">
          <div class="sum-icon">🚫</div>
          <div class="sum-text">POST 创建主机</div>
          <div class="sum-val">403</div>
        </div>
      </div>

      <div class="particle p1"></div>
      <div class="particle p2"></div>
      <div class="particle p3"></div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--success-bg) 0%, var(--bg) 50%, var(--brand-soft) 100%); }
.verify-content { text-align: center; position: relative; z-index: 1; width: 100%; max-width: 50%; }
.celebrate-icon { font-size: 56px; margin-bottom: 12px; animation: bounce 1s ease infinite; }
.verify-title { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.verify-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; }
.curl-card { background: #1e293b; border-radius: 10px; overflow: hidden; text-align: left; margin-bottom: 20px; }
.curl-header { padding: 8px 14px; background: #0f172a; display: flex; align-items: center; }
.curl-label { font-size: 12px; color: #94a3b8; font-family: var(--font-mono); }
.curl-body { padding: 14px; }
.curl-line { display: flex; gap: 8px; margin-bottom: 6px; }
.prompt { color: var(--success); font-family: var(--font-mono); font-size: 13px; font-weight: 700; }
.cmd { color: #e2e8f0; font-family: var(--font-mono); font-size: 12px; word-break: break-all; }
.curl-output { display: flex; justify-content: space-between; padding: 4px 0 10px; font-family: var(--font-mono); font-size: 12px; }
.curl-output.success .status { color: var(--success); }
.curl-output.success .result { color: var(--success); font-weight: 700; }
.curl-output.error .status { color: #f87171; }
.curl-output.error .result { color: #f87171; font-weight: 700; }
.summary-row { display: flex; gap: 14px; justify-content: center; }
.sum-item { display: flex; align-items: center; gap: 8px; padding: 12px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; }
.sum-item.success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.sum-item.error { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger); }
.sum-icon { font-size: 18px; }
.sum-val { font-family: var(--font-mono); font-weight: 700; }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.particle { position: absolute; width: 6px; height: 6px; border-radius: 50%; animation: float 3s ease-in-out infinite; }
.p1 { background: var(--success); top: 10%; left: 15%; animation-delay: 0s; }
.p2 { background: var(--brand); top: 20%; right: 10%; animation-delay: 0.8s; }
.p3 { background: var(--warning); bottom: 15%; left: 20%; animation-delay: 1.6s; }
@keyframes float { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.5; } 50% { transform: translateY(-15px) scale(1.3); opacity: 1; } }
</style>
