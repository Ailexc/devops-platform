<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">审批中心 / <b>审批通过</b></div><div class="mock-user">👤 小黄</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📋 审批通过 → 策略自动生成</h2>
      <p class="mock-sub">审批通过的瞬间，系统自动创建策略并同步到网关</p>

      <div class="timeline">
        <div class="tl-item done">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-title">审批通过</div>
            <div class="tl-desc">小黄审批小红的「主机监控 - 只读监控」申请</div>
          </div>
        </div>
        <div class="tl-item done">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-title">创建策略（动作级 · Casbin）</div>
            <div class="tl-code">
              <code>p = user:bob, action:host:list, effect:allow</code>
              <code>p = user:bob, action:host:read, effect:allow</code>
            </div>
          </div>
        </div>
        <div class="tl-item done">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-title">写入关系元组（实例级 · OpenFGA）</div>
            <div class="tl-code">
              <code>(bob, can_read, host:host-01)</code>
              <code>(bob, can_read, host:host-02)</code>
            </div>
          </div>
        </div>
        <div class="tl-item done">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-title">生成 Bundle → Agent 同步</div>
            <div class="tl-code"><code>bundle rev 37 → agent 拉取 → 本地决策生效</code></div>
          </div>
        </div>
        <div class="tl-item active">
          <div class="tl-dot pulse"></div>
          <div class="tl-body">
            <div class="tl-title">✅ 权限立即生效</div>
            <div class="tl-desc">bob 现在可以访问 host:list 和 host:read</div>
          </div>
        </div>
      </div>

      <div class="policy-card">
        <div class="pc-title">📄 生成的策略内容</div>
        <div class="pc-row"><span class="k">策略名称</span><span class="v">bob - 主机监控 - 只读监控</span></div>
        <div class="pc-row"><span class="k">主体</span><span class="v">👤 bob（个人）</span></div>
        <div class="pc-row"><span class="k">接口</span><span class="v mono">host:list, host:read</span></div>
        <div class="pc-row"><span class="k">数据范围</span><span class="v mono">env == "prod" && region in ["cn-north","cn-south"]</span></div>
        <div class="pc-row"><span class="k">来源</span><span class="v">申请单 #25 · 小黄审批</span></div>
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
.timeline { position: relative; padding-left: 20px; margin-bottom: 12px; }
.timeline::before { content: ''; position: absolute; left: 6px; top: 4px; bottom: 4px; width: 2px; background: var(--success); border-radius: 1px; }
.tl-item { position: relative; display: flex; gap: 10px; padding: 6px 0; }
.tl-dot { position: absolute; left: -18px; top: 10px; width: 10px; height: 10px; border-radius: 50%; background: var(--success); border: 2px solid var(--bg); z-index: 1; }
.tl-dot.pulse { animation: pulse 1.5s ease infinite; }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(22,163,74,0.4); } 50% { box-shadow: 0 0 0 6px rgba(22,163,74,0); } }
.tl-title { font-size: 12px; font-weight: 600; color: var(--text); }
.tl-desc { font-size: 11px; color: var(--text-secondary); margin-top: 1px; }
.tl-code { margin-top: 3px; }
.tl-code code { display: block; font-family: var(--font-mono); font-size: 10px; background: #1e293b; color: #38bdf8; padding: 3px 8px; border-radius: 3px; margin-bottom: 2px; }
.policy-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.pc-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.pc-row { display: flex; gap: 8px; padding: 3px 0; font-size: 11px; border-bottom: 1px solid var(--border); }
.pc-row:last-child { border-bottom: none; }
.k { color: var(--text-tertiary); min-width: 55px; }
.v { color: var(--text); font-weight: 500; }
.v.mono { font-family: var(--font-mono); font-size: 10px; }
</style>
