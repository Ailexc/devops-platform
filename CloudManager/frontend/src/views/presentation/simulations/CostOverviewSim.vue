<script setup lang="ts">
import { computed } from 'vue'
// 成本优化总览模拟（对齐真实 /cost/overview 大屏）
const props = defineProps<{ focus?: string }>()

// 数据权限聚焦：focus='perm' 展示普通员工（readonly 研发组）视角
const isPermView = computed(() => props.focus === 'perm')

const adminScope = {
  user: 'admin · 超级管理员',
  scope: '数据范围：全部',
  scopeClass: 'purple',
}
const deptScope = {
  user: 'readonly · 研发组员工',
  scope: '数据范围：本部门',
  scopeClass: 'green',
}

const stats = computed(() => isPermView.value
  ? [
    { label: '⚠️ 待处理建议', value: '119', sub: '共 158 条建议（仅研发组）', color: '#ef4444' },
    { label: '💰 预估月节省', value: '¥18,600', sub: '优化后预计节省', color: '#10b981' },
    { label: '🌐 覆盖云厂商', value: '1', sub: '本部门纳管云账号', color: '#3b82f6' },
    { label: '✅ 已处理', value: '39', sub: '历史已优化项', color: '#8b5cf6' },
    { label: '📈 环比节省', value: '¥2,300', sub: '较上月新增节省', color: '#f59e0b' },
  ]
  : [
    { label: '⚠️ 待处理建议', value: '476', sub: '共 604 条建议', color: '#ef4444' },
    { label: '💰 预估月节省', value: '¥75,800', sub: '优化后预计节省', color: '#10b981' },
    { label: '🌐 覆盖云厂商', value: '4', sub: '纳管云账号资源', color: '#3b82f6' },
    { label: '✅ 已处理', value: '128', sub: '历史已优化项', color: '#8b5cf6' },
    { label: '📈 环比节省', value: '¥8,900', sub: '较上月新增节省', color: '#f59e0b' },
  ])

const cloudSavings = [
  { name: 'AWS', saving: 28000, pct: 37 },
  { name: '阿里云', saving: 21500, pct: 28 },
  { name: '腾讯云', saving: 15200, pct: 20 },
  { name: '华为云', saving: 11100, pct: 15 },
]

const typeDist = [
  { name: '云主机', count: 214, pct: 44 },
  { name: '存储', count: 96, pct: 20 },
  { name: '数据库', count: 78, pct: 16 },
  { name: '网络', count: 52, pct: 11 },
  { name: '中间件', count: 36, pct: 9 },
]

const regions = [
  { name: 'cn-hangzhou', pct: 41 },
  { name: 'us-east-1', pct: 28 },
  { name: 'ap-southeast-1', pct: 19 },
  { name: 'eu-west-1', pct: 12 },
]

const trend = [
  { m: '3月', v: 5.6 }, { m: '4月', v: 6.2 }, { m: '5月', v: 7.1 },
  { m: '6月', v: 7.8 }, { m: '7月', v: 8.5 }, { m: '8月', v: 9.2 },
]

// 成本分摊（账单视角）
const billMonths = ['3月', '4月', '5月', '6月', '7月', '8月']
const billTrend = [62, 68, 75, 81, 88, 94]
const deptSplit = [
  { name: '技术部', v: 26, color: '#667eea' },
  { name: '研发组', v: 22, color: '#10b981' },
  { name: '运维组', v: 20, color: '#f59e0b' },
  { name: '产品部', v: 17, color: '#8b5cf6' },
  { name: '财务部', v: 15, color: '#ef4444' },
]
const appSplit = [
  { name: '订单中心', v: 34, color: '#667eea' },
  { name: '支付中心', v: 28, color: '#10b981' },
  { name: '用户中心', v: 22, color: '#f59e0b' },
  { name: '未归属', v: 16, color: '#94a3b8' },
]

// 建议明细
const suggestions = computed(() => isPermView.value
  ? [
    { cloud: 'AWS', sev: 'high', type: '闲置资源', name: 'web-server-03 近30天 CPU<5%', saving: 3200, status: '待处理', dept: '研发组' },
    { cloud: '腾讯云', sev: 'high', type: '预算告警', name: '支付中心 8月预算使用率达 92%', saving: 0, status: '待处理', dept: '研发组' },
    { cloud: 'AWS', sev: 'low', type: '预留实例', name: 'db-master-01 长期运行建议购买 RI', saving: 2500, status: '已处理', dept: '研发组' },
  ]
  : [
    { cloud: 'AWS', sev: 'high', type: '闲置资源', name: 'web-server-03 近30天 CPU<5%', saving: 3200, status: '待处理', dept: '研发组' },
    { cloud: '阿里云', sev: 'medium', type: '规格降配', name: 'api-server-01 8C16G 实际仅 4C8G', saving: 2800, status: '待处理', dept: '技术部' },
    { cloud: '腾讯云', sev: 'high', type: '预算告警', name: '支付中心 8月预算使用率达 92%', saving: 0, status: '待处理', dept: '财务部' },
    { cloud: 'AWS', sev: 'low', type: '预留实例', name: 'db-master-01 长期运行建议购买 RI', saving: 2500, status: '已处理', dept: '运维组' },
    { cloud: '阿里云', sev: 'medium', type: '趋势上涨', name: '订单中心 连续 3 月费用上涨 18%', saving: 1200, status: '待处理', dept: '产品部' },
    { cloud: '华为云', sev: 'low', type: '存储优化', name: '历史快照 87 个可清理，释放 1.2TB', saving: 1800, status: '待处理', dept: '技术部' },
  ])

const sevColor: Record<string, string> = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' }
const sevLabel: Record<string, string> = { high: '高', medium: '中', low: '低' }
</script>

<template>
  <div class="overview-sim">
    <!-- 数据权限说明 -->
    <div class="perm-card">
      <span class="perm-badge">👤 {{ isPermView ? deptScope.user : adminScope.user }}</span>
      <span class="perm-badge" :class="isPermView ? deptScope.scopeClass : adminScope.scopeClass">{{ isPermView ? deptScope.scope : adminScope.scope }}</span>
      <span class="perm-tip">后端按当前用户强制过滤数据范围 · {{ isPermView ? '仅本部门建议与成本可见，越权值自动清空' : '普通员工仅本部门' }}</span>
    </div>

    <!-- 全局筛选器 -->
    <div class="filter-bar">
      <span class="f-label">云厂商</span><select class="f-select"><option>全部云厂商</option><option>AWS</option><option>阿里云</option></select>
      <span class="f-label">云账号</span><select class="f-select"><option>全部账号</option></select>
      <span class="f-label">区域</span><select class="f-select"><option>全部区域</option></select>
      <span class="f-label">部门</span><select class="f-select"><option>全部部门</option><option>技术部</option><option>研发组</option></select>
      <span class="f-label">应用</span><select class="f-select"><option>全部应用</option></select>
      <span class="f-label">月份</span><select class="f-select"><option>2026-08</option></select>
      <span class="f-reset">重置</span>
    </div>

    <!-- 统计卡 -->
    <div class="stats-row">
      <div v-for="s in stats" :key="s.label" class="stat-card">
        <div class="stat-label">{{ s.label }}</div>
        <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-sub">{{ s.sub }}</div>
      </div>
    </div>

    <!-- 图表区 -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">🌐 按云厂商节省分布</div>
        <div class="bar-list">
          <div v-for="c in cloudSavings" :key="c.name" class="bar-row">
            <span class="bar-name">{{ c.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${c.pct}%`, background: '#7c3aed' }"></div></div>
            <span class="bar-val">¥{{ c.saving.toLocaleString() }}</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📦 按资源类型建议分布</div>
        <div class="donut-wrap">
          <div class="donut" style="background: conic-gradient(#7c3aed 0 44%, #10b981 44% 64%, #f59e0b 64% 80%, #3b82f6 80% 91%, #94a3b8 91% 100%)"></div>
          <div class="donut-center"><b>604</b><span>建议总数</span></div>
        </div>
        <div class="legend">
          <span v-for="t in typeDist" :key="t.name" class="legend-item"><i :style="{ background: ['#7c3aed','#10b981','#f59e0b','#3b82f6','#94a3b8'][typeDist.indexOf(t)] }"></i>{{ t.name }} {{ t.count }}</span>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📍 按区域成本分布</div>
        <div class="bar-list">
          <div v-for="r in regions" :key="r.name" class="bar-row">
            <span class="bar-name">{{ r.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${r.pct}%`, background: '#10b981' }"></div></div>
            <span class="bar-val">{{ r.pct }}%</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📈 近6月优化节省趋势</div>
        <div class="line-chart">
          <div v-for="(t, i) in trend" :key="t.m" class="line-col">
            <div class="line-bar" :style="{ height: `${(t.v / 10) * 130}px` }"></div>
            <div class="line-val">¥{{ t.v }}k</div>
            <div class="line-label">{{ t.m }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 成本分摊 -->
    <div class="charts-grid split">
      <div class="chart-card span-2">
        <div class="chart-title">💰 月度成本趋势（万元）</div>
        <div class="line-chart">
          <div v-for="(v, i) in billTrend" :key="i" class="line-col">
            <div class="line-bar purple" :style="{ height: `${(v / 100) * 130}px` }"></div>
            <div class="line-val">{{ v }}w</div>
            <div class="line-label">{{ billMonths[i] }}</div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🏢 部门分摊 <a class="detail-link">查看明细 →</a></div>
        <div class="bar-list">
          <div v-for="d in deptSplit" :key="d.name" class="bar-row">
            <span class="bar-name">{{ d.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${d.v * 2}%`, background: d.color }"></div></div>
            <span class="bar-val">{{ d.v }}%</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📱 应用分摊 <a class="detail-link">查看明细 →</a></div>
        <div class="bar-list">
          <div v-for="a in appSplit" :key="a.name" class="bar-row">
            <span class="bar-name">{{ a.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${a.v * 2}%`, background: a.color }"></div></div>
            <span class="bar-val">{{ a.v }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 建议明细 -->
    <div class="table-card">
      <div class="card-header">
        <h3>📋 优化建议明细</h3>
        <span class="card-hint">点击行查看详情 · 支持标记处理</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>云厂商</th><th>严重度</th><th>规则类型</th><th>建议内容</th><th>部门</th><th class="right">预估节省</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in suggestions" :key="s.name">
              <td><span class="cloud-pill">{{ s.cloud }}</span></td>
              <td><span class="sev-tag" :style="{ color: sevColor[s.sev], background: `${sevColor[s.sev]}15` }">{{ sevLabel[s.sev] }}</span></td>
              <td><span class="type-tag">{{ s.type }}</span></td>
              <td class="sug-name">{{ s.name }}</td>
              <td>{{ s.dept }}</td>
              <td class="right green">{{ s.saving ? `¥${s.saving.toLocaleString()}/月` : '-' }}</td>
              <td><span class="status-tag" :class="s.status === '已处理' ? 'done' : 'todo'">{{ s.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-sim {
  padding: 16px 20px 24px;
  background: #f6f7fb;
  height: 100%;
  overflow-y: auto;
}
.perm-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(90deg, #f3e8ff, #faf5ff);
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  font-size: 12px;
  margin-bottom: 12px;
}
.perm-badge {
  padding: 2px 10px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 999px;
  font-weight: 600;
}
.perm-badge.purple { background: #7c3aed; color: #fff; }
.perm-badge.green { background: #10b981; color: #fff; }
.perm-tip { color: #7c3aed; margin-left: 6px; }
.filter-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.f-label { font-size: 12px; color: #64748b; }
.f-select {
  padding: 4px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  background: #fff;
  color: #0f172a;
}
.f-reset { font-size: 12px; color: #7c3aed; cursor: pointer; margin-left: 6px; font-weight: 500; }
.stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 12px; }
.stat-card {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  padding: 14px 16px;
}
.stat-label { font-size: 12px; color: #64748b; margin-bottom: 6px; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-sub { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 12px; }
.charts-grid.split { grid-template-columns: 1fr 1fr 1fr; }
.span-2 { grid-column: span 2; }
.chart-card {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  padding: 12px 14px;
}
.chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-link { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; }
.bar-list { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-name { width: 86px; font-size: 12px; color: #475569; }
.bar-track { flex: 1; height: 12px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; }
.bar-val { width: 76px; font-size: 12px; color: #334155; text-align: right; font-weight: 500; }
.donut-wrap { display: flex; justify-content: center; align-items: center; position: relative; height: 120px; }
.donut { width: 110px; height: 110px; border-radius: 50%; }
.donut-center { position: absolute; width: 70px; height: 70px; background: #fff; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.donut-center b { font-size: 16px; }
.donut-center span { font-size: 10px; color: #94a3b8; }
.legend { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 8px; }
.legend-item { font-size: 11px; color: #64748b; display: flex; align-items: center; gap: 4px; }
.legend-item i { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.line-chart { display: flex; align-items: flex-end; justify-content: space-around; height: 150px; padding-top: 8px; }
.line-col { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.line-bar { width: 22px; background: linear-gradient(180deg, #a78bfa, #7c3aed); border-radius: 4px 4px 0 0; }
.line-bar.purple { background: linear-gradient(180deg, #8b5cf6, #6366f1); }
.line-val { font-size: 10px; color: #64748b; margin-top: 4px; }
.line-label { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.table-card {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  padding: 12px 14px;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-header h3 { font-size: 13px; font-weight: 600; color: #0f172a; margin: 0; }
.card-hint { font-size: 11px; color: #94a3b8; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th {
  text-align: left;
  padding: 8px 10px;
  color: #64748b;
  font-weight: 500;
  background: #f8fafc;
  border-bottom: 1px solid #eef0f4;
}
td { padding: 8px 10px; border-bottom: 1px solid #f6f7fb; color: #334155; }
.right { text-align: right; }
.green { color: #059669; font-weight: 600; }
.cloud-pill { padding: 2px 8px; background: #f1f5f9; border-radius: 4px; font-size: 11px; }
.sev-tag, .type-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #f1f5f9; }
.sug-name { color: #0f172a; }
.status-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.status-tag.todo { background: #fff7ed; color: #ea580c; }
.status-tag.done { background: #ecfdf5; color: #059669; }
</style>
