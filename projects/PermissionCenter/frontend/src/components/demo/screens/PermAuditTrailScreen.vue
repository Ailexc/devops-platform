<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">我的权限 / <b>授权来源</b></div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">📋 授权来源 —— 每条权限都有申请单</h2>
      <p class="mock-sub">权限来源可追溯：组织权限来自组长申请，个人权限来自个人申请，自建组权限来自组邀请</p>

      <div class="source-card">
        <div class="sc-header"><span class="sc-icon violet">🏢</span><span class="sc-type">组织权限</span></div>
        <div class="sc-row"><span class="sc-key">能力包</span><span class="sc-val">ITSM 工单 · 应用权限开通</span></div>
        <div class="sc-row"><span class="sc-key">授权路径</span><span class="sc-val">bob → 研发一部 → 组权限</span></div>
        <div class="sc-row"><span class="sc-key">发起人</span><span class="sc-val">alice（组长）</span></div>
        <div class="sc-row"><span class="sc-key">申请单</span><span class="sc-val link">#24 · 组权限授权申请</span></div>
        <div class="sc-row"><span class="sc-key">审批链</span><span class="sc-val">alice 确认 → admin 复核 → ✅ approved</span></div>
      </div>

      <div class="source-card">
        <div class="sc-header"><span class="sc-icon blue">👤</span><span class="sc-type">个人权限</span></div>
        <div class="sc-row"><span class="sc-key">能力包</span><span class="sc-val">ITSM 工单 · 新增服务</span></div>
        <div class="sc-row"><span class="sc-key">授权路径</span><span class="sc-val">bob → 个人申请</span></div>
        <div class="sc-row"><span class="sc-key">发起人</span><span class="sc-val">bob（本人）</span></div>
        <div class="sc-row"><span class="sc-key">申请单</span><span class="sc-val link">#25 · 能力包申请</span></div>
        <div class="sc-row"><span class="sc-key">审批链</span><span class="sc-val">bob 确认 → admin 复核 → ✅ approved</span></div>
      </div>

      <div class="source-card">
        <div class="sc-header"><span class="sc-icon amber">👥</span><span class="sc-type">自建组权限</span></div>
        <div class="sc-row"><span class="sc-key">能力包</span><span class="sc-val">公共资源池 · 数据库管理</span></div>
        <div class="sc-row"><span class="sc-key">授权路径</span><span class="sc-val">bob → 业务查询组 → 组权限</span></div>
        <div class="sc-row"><span class="sc-key">发起人</span><span class="sc-val">组管理员（alice）</span></div>
        <div class="sc-row"><span class="sc-key">申请单</span><span class="sc-val link">#18 · 组权限授权申请</span></div>
        <div class="sc-row"><span class="sc-key">有效期</span><span class="sc-val">至 2026-12-31（TTL 组）</span></div>
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
.source-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; }
.sc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.sc-icon { font-size: 16px; }
.sc-icon.blue { }
.sc-icon.violet { }
.sc-icon.amber { }
.sc-type { font-size: 13px; font-weight: 600; color: var(--text); }
.sc-row { display: flex; gap: 8px; padding: 3px 0; font-size: 11px; }
.sc-key { color: var(--text-tertiary); min-width: 55px; flex-shrink: 0; }
.sc-val { color: var(--text); font-weight: 500; }
.sc-val.link { color: var(--brand); }
</style>
