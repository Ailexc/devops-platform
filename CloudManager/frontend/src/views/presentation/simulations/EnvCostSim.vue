<script setup lang="ts">
// 环境成本 Tab 模拟（对齐真实 TopologyCompose「💰 成本」Tab）
const overview = [
  { label: '本月成本', value: '¥20,316.93', color: '#0f172a' },
  { label: '环比上月', value: '-14%', color: '#10b981' },
  { label: '预算使用率', value: '10.2%', color: '#7c3aed' },
  { label: '本月预算', value: '¥200,000', color: '#0f172a' },
  { label: '费用记录', value: '70 条', color: '#0f172a' },
]

const rows = [
  { name: 'lb-cn-004', id: 'lb-06f20b85081e', type: 'load_balancer', spec: 'slb.s1.small', region: 'cn-hangzhou', date: '2026-08-20', cost: 660.72, dept: '财务部' },
  { name: 'subnet-cn-001', id: 'subnet-3273a5dbf89d', type: 'subnet', spec: '', region: 'cn-hangzhou', date: '2026-08-09', cost: 649.82, dept: '技术部' },
  { name: 'api-cn-009', id: 'i-d8f96e1c021c', type: 'instance', spec: 't3.xlarge', region: 'cn-hangzhou', date: '2026-08-10', cost: 545.27, dept: '研发组' },
  { name: 'vpc-cn-003', id: 'vpc-ac9a70ba076d', type: 'vpc', spec: '', region: 'cn-hangzhou', date: '2026-08-28', cost: 536.6, dept: '研发组' },
  { name: 'sg-cn-005', id: 'sg-87e8d8c8d92f', type: 'security_group', spec: '', region: 'cn-hangzhou', date: '2026-08-23', cost: 521.64, dept: '运维组' },
  { name: 'worker-cn-014', id: 'i-2555a9509351', type: 'instance', spec: 't3.medium', region: 'cn-hangzhou', date: '2026-08-21', cost: 369.12, dept: '产品部' },
  { name: 'web-cn-005', id: 'i-e0a07a909cb2', type: 'instance', spec: 't3.xlarge', region: 'cn-hangzhou', date: '2026-08-18', cost: 312.89, dept: '运维组' },
]
</script>

<template>
  <div class="env-cost-sim">
    <!-- 概览条 -->
    <div class="overview-bar">
      <div v-for="o in overview" :key="o.label" class="ov-item">
        <div class="ov-label">{{ o.label }}</div>
        <div class="ov-value" :style="{ color: o.color }">{{ o.value }}</div>
      </div>
      <span class="btn-budget">📝 申请增加预算</span>
    </div>

    <div class="env-hint">📍 该环境（Mock 账号 / cn-hangzhou）下各资源费用明细：</div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <span class="f-label">筛选：</span>
      <select class="f-select"><option selected>2026-08</option><option>2026-07</option><option>2026-06</option></select>
      <select class="f-select"><option selected>全部类型</option><option>云主机</option><option>数据库</option><option>负载均衡</option><option>VPC</option><option>子网</option></select>
      <select class="f-select"><option selected>全部区域</option><option>cn-hangzhou</option></select>
      <span class="f-search">🔍 搜索资源名...</span>
      <span class="f-reset">重置</span>
    </div>

    <!-- 明细表 -->
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>资源名称</th><th>资源ID</th><th>类型</th><th>规格</th><th>区域</th><th>费用日期</th><th class="right">费用</th><th>部门</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td class="res-name">{{ r.name }}</td>
            <td class="mono">{{ r.id }}</td>
            <td><span class="type-tag">{{ r.type }}</span></td>
            <td>{{ r.spec || '-' }}</td>
            <td>{{ r.region }}</td>
            <td>{{ r.date }}</td>
            <td class="right cost">¥{{ r.cost.toFixed(2) }}</td>
            <td>{{ r.dept }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pagination">共 70 条 <span class="page">‹</span> <span class="page active">1</span> <span class="page">2</span> <span class="page">3</span> <span class="page">4</span> <span class="page">›</span></div>
  </div>
</template>

<style scoped>
.env-cost-sim { padding: 16px 20px; background: #fff; height: 100%; overflow-y: auto; }
.overview-bar { display: flex; align-items: center; gap: 28px; padding: 14px 18px; background: linear-gradient(90deg, #faf5ff, #f6f7fb); border: 1px solid #f0ecff; border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.ov-label { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
.ov-value { font-size: 18px; font-weight: 700; }
.btn-budget {
  margin-left: auto;
  padding: 7px 14px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #fff;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}
.env-hint { font-size: 12px; color: #64748b; margin-bottom: 10px; }
.filter-bar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #eef0f4; border-radius: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.f-label { font-size: 12px; color: #64748b; }
.f-select { padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; background: #fff; color: #0f172a; }
.f-search { flex: 1; min-width: 160px; padding: 5px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; color: #94a3b8; background: #fff; }
.f-reset { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 8px 10px; color: #64748b; font-weight: 500; background: #f8fafc; border-bottom: 1px solid #eef0f4; }
td { padding: 8px 10px; border-bottom: 1px solid #f6f7fb; color: #334155; }
.right { text-align: right; }
.res-name { color: #0f172a; font-weight: 500; }
.mono { font-family: monospace; font-size: 11px; color: #64748b; }
.type-tag { padding: 2px 8px; background: #f1f5f9; border-radius: 4px; font-size: 11px; }
.cost { color: #059669; font-weight: 600; }
.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 6px; padding-top: 12px; font-size: 12px; color: #64748b; }
.page { width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; }
.page.active { background: #7c3aed; color: #fff; border-color: #7c3aed; }
</style>
