<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">策略触发场景</div><div class="mock-user">— 系统视角</div></div>
    <div class="mock-content">
      <h2 class="mock-title">⚡ 策略从哪里来？</h2>
      <p class="mock-sub">策略不是手动创建的，而是由业务操作自动触发生成</p>

      <div class="trigger-grid">
        <div class="trigger-card">
          <div class="tc-header blue">方式一：应用 Owner 上架预设</div>
          <div class="tc-flow">
            <div class="tc-step"><span class="tc-num">1</span>小黄编辑能力包</div>
            <div class="tc-arrow">↓</div>
            <div class="tc-step"><span class="tc-num">2</span>上架「只读监控」预设</div>
            <div class="tc-arrow">↓</div>
            <div class="tc-step"><span class="tc-num">3</span>审批通过</div>
            <div class="tc-arrow highlight">↓ <span class="tc-label">触发</span></div>
            <div class="tc-step result"><span>📋</span>系统自动创建「预设级策略」</div>
          </div>
          <div class="tc-note">策略绑定：预设包含的接口 + 数据范围 + 可申请主体</div>
        </div>

        <div class="trigger-card">
          <div class="tc-header green">方式二：用户申请权限</div>
          <div class="tc-flow">
            <div class="tc-step"><span class="tc-num">1</span>小红在能力市场选预设</div>
            <div class="tc-arrow">↓</div>
            <div class="tc-step"><span class="tc-num">2</span>选择主体 + 数据范围</div>
            <div class="tc-arrow">↓</div>
            <div class="tc-step"><span class="tc-num">3</span>提交申请单</div>
            <div class="tc-arrow highlight">↓ <span class="tc-label">触发</span></div>
            <div class="tc-step result"><span>📋</span>系统生成「授权申请单」</div>
          </div>
          <div class="tc-note">审批通过后，系统自动创建「用户级策略」</div>
        </div>
      </div>

      <div class="key-point"><span>💡</span><span>核心设计：Policy.Source 关联 RequestID —— 每条策略都能追溯到触发它的业务操作，实现「授权即审批」无死角。</span></div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 16px 22px; overflow: auto; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 11px; color: var(--text-secondary); margin-bottom: 14px; }
.trigger-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
.trigger-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.tc-header { font-size: 12px; font-weight: 600; padding: 6px 10px; border-radius: 6px; margin-bottom: 10px; text-align: center; }
.tc-header.blue { background: var(--brand-soft); color: var(--brand); }
.tc-header.green { background: var(--success-bg); color: var(--success); }
.tc-flow { display: flex; flex-direction: column; gap: 2px; }
.tc-step { display: flex; align-items: center; gap: 6px; padding: 5px 8px; background: var(--bg-secondary); border-radius: 5px; font-size: 11px; color: var(--text); }
.tc-step.result { background: var(--success-bg); color: var(--success); font-weight: 600; border: 1px solid var(--success); }
.tc-num { width: 16px; height: 16px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; flex-shrink: 0; }
.tc-arrow { text-align: center; color: var(--text-tertiary); font-size: 12px; }
.tc-arrow.highlight { color: var(--brand); font-weight: 700; }
.tc-label { font-size: 9px; background: var(--brand); color: #fff; padding: 0 5px; border-radius: 4px; }
.tc-note { font-size: 10px; color: var(--text-tertiary); margin-top: 8px; line-height: 1.4; }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 11px; color: var(--info); line-height: 1.5; }
</style>
