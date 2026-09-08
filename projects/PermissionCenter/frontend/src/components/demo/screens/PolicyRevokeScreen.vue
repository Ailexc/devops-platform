<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">授权管理 / <b>策略回收</b></div><div class="mock-user">👤 小黄</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🔄 策略回收 — 权限即时失效</h2>
      <p class="mock-sub">下架预设 / 回收授权 → 策略删除 → OpenFGA 关系撤销 → 权限立即失效</p>

      <div class="revoke-flow">
        <div class="rf-card">
          <div class="rf-title">场景 A：下架预设</div>
          <div class="rf-steps">
            <div class="rf-step"><span class="rf-num">1</span>小黄在授权管理页点击「下架」</div>
            <div class="rf-arrow">↓</div>
            <div class="rf-step"><span class="rf-num">2</span>预设 status → draft，市场不可见</div>
            <div class="rf-arrow">↓</div>
            <div class="rf-step"><span class="rf-num">3</span>新用户无法再申请该预设</div>
          </div>
          <div class="rf-note">已有授权不受影响（存量策略保留）</div>
        </div>

        <div class="rf-card deny">
          <div class="rf-title">场景 B：回收个人授权</div>
          <div class="rf-steps">
            <div class="rf-step"><span class="rf-num">1</span>小黄发起回收审批（RevokeRequest）</div>
            <div class="rf-arrow">↓</div>
            <div class="rf-step"><span class="rf-num">2</span>其他 Owner 审批（SoD：不可自审）</div>
            <div class="rf-arrow">↓</div>
            <div class="rf-step"><span class="rf-num">3</span>审批通过 → 策略停用 + OpenFGA 撤销</div>
            <div class="rf-arrow">↓</div>
            <div class="rf-step result"><span>🚫</span>bob 的主机监控权限立即失效</div>
          </div>
          <div class="rf-note">回收走审批链，防止误操作；审计日志完整记录</div>
        </div>
      </div>

      <div class="compare-card">
        <div class="cc-title">对比：下架 vs 回收</div>
        <table>
          <thead><tr><th></th><th>下架预设</th><th>回收授权</th></tr></thead>
          <tbody>
            <tr><td>影响范围</td><td>新用户不可申请</td><td>指定用户失去权限</td></tr>
            <tr><td>存量策略</td><td>保留</td><td>删除</td></tr>
            <tr><td>审批要求</td><td>Owner 确认</td><td>多级审批（SoD）</td></tr>
            <tr><td>即时生效</td><td>市场不可见</td><td>网关拒绝请求</td></tr>
          </tbody>
        </table>
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
.revoke-flow { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.rf-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }
.rf-card.deny { border-color: var(--danger); }
.rf-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
.rf-steps { display: flex; flex-direction: column; gap: 2px; }
.rf-step { display: flex; align-items: center; gap: 6px; padding: 4px 8px; background: var(--bg-secondary); border-radius: 4px; font-size: 10px; color: var(--text); }
.rf-step.result { background: var(--danger-bg); color: var(--danger); font-weight: 600; }
.rf-num { width: 14px; height: 14px; border-radius: 50%; background: var(--bg-tertiary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: 700; flex-shrink: 0; }
.rf-arrow { text-align: center; color: var(--text-tertiary); font-size: 10px; }
.rf-note { font-size: 9px; color: var(--text-tertiary); margin-top: 6px; line-height: 1.4; }
.compare-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.cc-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.compare-card table { width: 100%; border-collapse: collapse; font-size: 10px; }
.compare-card th { text-align: left; padding: 4px 6px; color: var(--text-tertiary); border-bottom: 1px solid var(--border); font-weight: 500; }
.compare-card td { padding: 4px 6px; border-bottom: 1px solid var(--border); color: var(--text); }
</style>
