<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">我的权限 / <b>组织权限</b></div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🏢 组织权限</h2>
      <p class="mock-sub">来自组织树继承 —— 组即角色，加入组织自动获得对应权限</p>

      <div class="org-chain">
        <div class="chain-node"><span class="cn-icon">🏛️</span><span class="cn-name">总公司</span></div>
        <div class="chain-arrow">↓</div>
        <div class="chain-node"><span class="cn-icon">💻</span><span class="cn-name">研发中心</span></div>
        <div class="chain-arrow">↓</div>
        <div class="chain-node highlight"><span class="cn-icon">👥</span><span class="cn-name">研发一部</span><span class="cn-badge">bob 所在组</span></div>
      </div>

      <div class="perm-section">
        <div class="sec-title">研发一部的组权限（继承自组织树）</div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🧭</span><span class="pc-name">ITSM 工单 · 应用权限开通</span></div>
          <div class="pc-apis">
            <span class="api">POST /api/v1/itsm/perm/apply</span>
          </div>
          <div class="pc-source">来源：组长 alice 为研发一部发起授权申请 → 审批通过</div>
        </div>
      </div>

      <div class="key-point"><span>💡</span><span>组织权限特点：① 自动继承 —— 加入组织即获得，无需个人申请；② 组即角色 —— 组权限 = 该角色的接口权限；③ 组长配置 —— 由组 admin 发起，走审批单授权。</span></div>
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
.org-chain { display: flex; align-items: center; gap: 6px; margin-bottom: 14px; padding: 12px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; }
.chain-node { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 8px; background: var(--bg-secondary); font-size: 13px; font-weight: 500; color: var(--text); }
.chain-node.highlight { background: var(--brand-soft); border: 1px solid var(--brand); font-weight: 600; }
.cn-icon { font-size: 14px; }
.cn-badge { font-size: 9px; padding: 1px 6px; border-radius: 6px; background: var(--brand); color: #fff; font-weight: 600; }
.chain-arrow { color: var(--brand); font-weight: 700; font-size: 14px; }
.perm-section { margin-bottom: 12px; }
.sec-title { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.perm-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; margin-bottom: 6px; }
.pc-head { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.pc-icon { font-size: 14px; }
.pc-name { font-size: 13px; font-weight: 600; color: var(--text); }
.pc-apis { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
.api { font-size: 10px; font-family: var(--font-mono); padding: 2px 6px; border-radius: 4px; background: var(--success-bg); color: var(--success); }
.pc-source { font-size: 10px; color: var(--text-tertiary); }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 11px; color: var(--info); line-height: 1.5; }
</style>
