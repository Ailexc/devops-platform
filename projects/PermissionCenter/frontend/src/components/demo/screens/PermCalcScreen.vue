<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">我的权限 / <b>权限计算</b></div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🧮 权限计算模型</h2>
      <p class="mock-sub">三个维度的权限取并集（Union），任一维度有即放行</p>

      <div class="calc-visual">
        <!-- 三个圆 -->
        <div class="venn">
          <div class="venn-circle personal">
            <div class="venn-label">👤 个人权限</div>
            <div class="venn-items">主机监控<br>数据库管理<br>工单管理</div>
          </div>
          <div class="venn-circle org">
            <div class="venn-label">🏢 组织权限</div>
            <div class="venn-items">主机管理<br>网络管理</div>
          </div>
          <div class="venn-circle group">
            <div class="venn-label">👥 自建组权限</div>
            <div class="venn-items">安全巡检</div>
          </div>
        </div>
      </div>

      <div class="calc-table">
        <table>
          <thead><tr><th>能力包</th><th>个人</th><th>组织</th><th>自建组</th><th>最终结果</th></tr></thead>
          <tbody>
            <tr><td>🖥️ 主机监控</td><td>✅</td><td>—</td><td>—</td><td class="ok">✅ 生效</td></tr>
            <tr><td>🖥️ 主机管理</td><td>—</td><td>✅</td><td>—</td><td class="ok">✅ 生效</td></tr>
            <tr><td>🧭 网络管理</td><td>—</td><td>✅</td><td>—</td><td class="ok">✅ 生效</td></tr>
            <tr><td>🗃️ 数据库管理</td><td>✅</td><td>—</td><td>—</td><td class="ok">✅ 生效</td></tr>
            <tr><td>🎫 工单管理</td><td>✅</td><td>—</td><td>—</td><td class="ok">✅ 生效</td></tr>
            <tr><td>🛡️ 安全巡检</td><td>—</td><td>—</td><td>✅</td><td class="ok">✅ 生效</td></tr>
          </tbody>
        </table>
      </div>

      <div class="key-point"><span>💡</span><span>计算规则：最终权限 = 个人权限 ∪ 组织权限 ∪ 自建组权限。数据范围同理取并集。网关鉴权时，Casbin 评估动作级权限，OpenFGA 评估实例级数据范围。</span></div>
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
.venn { display: flex; gap: 12px; justify-content: center; margin-bottom: 14px; }
.venn-circle { width: 140px; height: 130px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 10px; }
.venn-circle.personal { background: rgba(47,111,237,0.12); border: 2px solid var(--brand); }
.venn-circle.org { background: rgba(124,58,237,0.12); border: 2px solid var(--purple); }
.venn-circle.group { background: rgba(217,119,6,0.12); border: 2px solid var(--warning); }
.venn-label { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.venn-items { font-size: 10px; color: var(--text-secondary); line-height: 1.4; }
.calc-table { margin-bottom: 12px; }
.calc-table table { width: 100%; border-collapse: collapse; font-size: 12px; background: var(--bg-card); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.calc-table th { text-align: left; padding: 6px 8px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); background: var(--bg-secondary); font-size: 11px; }
.calc-table td { padding: 5px 8px; border-bottom: 1px solid var(--border); color: var(--text); }
.calc-table td.ok { color: var(--success); font-weight: 600; }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 11px; color: var(--info); line-height: 1.5; }
</style>
