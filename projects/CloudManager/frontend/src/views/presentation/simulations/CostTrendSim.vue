<script setup lang="ts">
defineProps<{ focus?: string }>()

// 全局筛选器 6 维度（跨页面保持）
const filters = [
  { label: '云厂商', val: '全部云厂商' },
  { label: '云账号', val: '全部账号' },
  { label: '区域', val: '全部区域' },
  { label: '部门', val: '全部部门' },
  { label: '应用', val: '全部应用' },
  { label: '月份', val: '2026-08' },
]

// 近 6 月月度成本（万元，含 3 云拆分）
const months = ['3月', '4月', '5月', '6月', '7月', '8月']
const costs = [
  { month: '3月', aws: 4.2, ali: 3.1, tencent: 2.4, total: 9.7 },
  { month: '4月', aws: 4.6, ali: 3.4, tencent: 2.6, total: 10.6 },
  { month: '5月', aws: 5.1, ali: 3.8, tencent: 2.9, total: 11.8 },
  { month: '6月', aws: 5.4, ali: 4.1, tencent: 3.2, total: 12.7 },
  { month: '7月', aws: 5.9, ali: 4.4, tencent: 3.4, total: 13.7 },
  { month: '8月', aws: 6.3, ali: 4.8, tencent: 3.7, total: 14.8 },
]

// 部门分摊
const deptSplit = [
  { name: '技术部', v: 26, color: '#667eea' },
  { name: '研发组', v: 22, color: '#10b981' },
  { name: '运维组', v: 20, color: '#f59e0b' },
  { name: '产品部', v: 17, color: '#8b5cf6' },
  { name: '财务部', v: 15, color: '#ef4444' },
]

// 应用分摊
const appSplit = [
  { name: '订单中心', v: 34, color: '#667eea' },
  { name: '支付中心', v: 28, color: '#10b981' },
  { name: '用户中心', v: 22, color: '#f59e0b' },
  { name: '未归属', v: 16, color: '#94a3b8' },
]

// 账单明细
const bills = [
  { month: '2026-08', dept: '技术部', app: '订单中心', cloud: 'AWS', cost: '¥8,520' },
  { month: '2026-08', dept: '研发组', app: '支付中心', cloud: '阿里云', cost: '¥5,340' },
  { month: '2026-08', dept: '运维组', app: '用户中心', cloud: '腾讯云', cost: '¥3,860' },
  { month: '2026-08', dept: '产品部', app: '订单中心', cloud: 'AWS', cost: '¥2,940' },
  { month: '2026-08', dept: '财务部', app: '未归属', cloud: '阿里云', cost: '¥1,780' },
]
</script>

<template>
  <div class="cost-sim">
    <div class="list-header">
      <h2>💰 成本趋势</h2>
      <div class="header-actions">
        <span class="perm-badge">👤 admin · 数据范围：全部</span>
        <span class="filter-btn">📅 2026-03 ~ 2026-08</span>
      </div>
    </div>

    <!-- 全局筛选器（6 维度，跨页面保持） -->
    <div class="global-filter">
      <span v-for="f in filters" :key="f.label" class="g-item">
        <span class="g-label">{{ f.label }}</span>
        <span class="g-select">{{ f.val }} ▾</span>
      </span>
      <span class="g-reset">重置</span>
    </div>

    <div class="chart-card">
      <h3>月度费用趋势（万元）</h3>
      <div class="chart-area">
        <div v-for="item in costs" :key="item.month" class="chart-bar-group">
          <div class="bar-stack" :style="{ height: `${(item.total / 15) * 132}px` }">
            <div class="bar-segment aws" :style="{ height: `${(item.aws / item.total) * 100}%` }"></div>
            <div class="bar-segment ali" :style="{ height: `${(item.ali / item.total) * 100}%` }"></div>
            <div class="bar-segment tencent" :style="{ height: `${(item.tencent / item.total) * 100}%` }"></div>
          </div>
          <div class="bar-label">{{ item.month }}</div>
          <div class="bar-total">¥{{ item.total }}w</div>
        </div>
      </div>
      <div class="chart-legend">
        <span class="legend-item"><span class="dot aws"></span>AWS</span>
        <span class="legend-item"><span class="dot ali"></span>阿里云</span>
        <span class="legend-item"><span class="dot tencent"></span>腾讯云</span>
      </div>
    </div>

    <!-- 部门/应用分摊 -->
    <div class="split-grid">
      <div class="chart-card">
        <h3>🏢 部门分摊 <a class="detail-link">查看明细 →</a></h3>
        <div class="bar-list">
          <div v-for="d in deptSplit" :key="d.name" class="bar-row">
            <span class="bar-name">{{ d.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${d.v * 2}%`, background: d.color }"></div></div>
            <span class="bar-val">{{ d.v }}%</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h3>📱 应用分摊 <a class="detail-link">查看明细 →</a></h3>
        <div class="bar-list">
          <div v-for="a in appSplit" :key="a.name" class="bar-row">
            <span class="bar-name">{{ a.name }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${a.v * 2}%`, background: a.color }"></div></div>
            <span class="bar-val">{{ a.v }}%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="detail-card" :class="{ highlighted: focus === 'detail' }">
      <h3>费用明细</h3>
      <div class="detail-table">
        <div class="table-header">
          <div class="col">月份</div>
          <div class="col">部门</div>
          <div class="col">应用</div>
          <div class="col">云厂商</div>
          <div class="col amount">费用</div>
        </div>
        <div v-for="b in bills" :key="b.cost" class="table-row">
          <div class="col">{{ b.month }}</div>
          <div class="col">{{ b.dept }}</div>
          <div class="col">{{ b.app }}</div>
          <div class="col">{{ b.cloud }}</div>
          <div class="col amount">{{ b.cost }}</div>
        </div>
      </div>
      <div class="bill-total">共 1,427 条费用记录 · 月度合计 ¥14.8w</div>
    </div>
  </div>
</template>

<style scoped>
.cost-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  color: #475569;
}

.chart-card, .detail-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.detail-card.highlighted {
  border: 2px solid #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 16px 0;
}

.chart-area {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 200px;
  padding: 0 20px;
}

.chart-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  height: 100%;
}

.bar-stack {
  display: flex;
  flex-direction: column-reverse;
  justify-content: flex-end;
  gap: 2px;
  width: 40px;
}

.bar-segment {
  width: 40px;
  border-radius: 4px 4px 0 0;
  transition: height 0.5s ease;
}

.bar-segment.aws { background: #f97316; }
.bar-segment.ali { background: #3b82f6; }
.bar-segment.tencent { background: #8b5cf6; }

.bar-label {
  font-size: 12px;
  color: #64748b;
}

.bar-total {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.dot.aws { background: #f97316; }
.dot.ali { background: #3b82f6; }
.dot.tencent { background: #8b5cf6; }

.detail-table {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: flex;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.table-row {
  display: flex;
  padding: 10px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  color: #1e293b;
}

.table-row:last-child { border-bottom: none; }

.col { flex: 1; }
.col.amount { text-align: right; font-weight: 600; color: #1a1a2e; }

/* 全局筛选器 */
.global-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.g-item { display: flex; align-items: center; gap: 5px; }
.g-label { font-size: 12px; color: #64748b; }
.g-select { padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; color: #0f172a; background: #fff; }
.g-reset { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; margin-left: 4px; }
.perm-badge { padding: 4px 12px; background: #7c3aed; color: #fff; border-radius: 999px; font-size: 12px; font-weight: 600; }

/* 分摊 */
.split-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.bar-list { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-name { width: 64px; font-size: 12px; color: #475569; }
.bar-track { flex: 1; height: 12px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; }
.bar-val { width: 40px; font-size: 12px; color: #334155; text-align: right; font-weight: 500; }
.detail-link { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; }
.bill-total { padding-top: 10px; font-size: 12px; color: #94a3b8; text-align: right; }
</style>
