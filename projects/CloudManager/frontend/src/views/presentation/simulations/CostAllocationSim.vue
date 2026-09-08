<script setup lang="ts">
// 成本分摊下钻（对齐真实 /cost/share）
const deptSplit = [
  { name: '技术部', apps: '订单中心、用户中心', v: 26, amount: '¥11.4w', color: '#667eea' },
  { name: '研发组', apps: '支付中心、订单中心', v: 22, amount: '¥9.7w', color: '#10b981' },
  { name: '运维组', apps: '基础设施、网关', v: 20, amount: '¥8.8w', color: '#f59e0b' },
  { name: '产品部', apps: '用户中心、BI', v: 17, amount: '¥7.5w', color: '#8b5cf6' },
  { name: '财务部', apps: '财务系统', v: 15, amount: '¥6.6w', color: '#ef4444' },
]

const appSplit = [
  { name: '订单中心', apps: '技术部、研发组', v: 34, amount: '¥15.0w', color: '#667eea' },
  { name: '支付中心', apps: '研发组、财务部', v: 28, amount: '¥12.3w', color: '#10b981' },
  { name: '用户中心', apps: '技术部、产品部', v: 22, amount: '¥9.7w', color: '#f59e0b' },
  { name: '未归属', apps: '无应用标签', v: 16, amount: '¥7.0w', color: '#94a3b8' },
]

// TOP10 资源
const top10 = [
  { name: 'db-master-01', type: 'RDS', cost: '¥4,200' },
  { name: 'web-server-03', type: 'EC2', cost: '¥3,650' },
  { name: 'api-server-01', type: 'EC2', cost: '¥3,120' },
  { name: 'redis-cache-01', type: 'Redis', cost: '¥2,860' },
  { name: 'oss-bucket-07', type: 'OSS', cost: '¥2,540' },
  { name: 'lb-prod-01', type: 'SLB', cost: '¥2,210' },
  { name: 'pay-server-02', type: 'EC2', cost: '¥1,980' },
  { name: 'kafka-cluster', type: 'Kafka', cost: '¥1,750' },
  { name: 'monitor-nodes', type: 'EC2', cost: '¥1,530' },
  { name: 'cdn-edge-02', type: 'CDN', cost: '¥1,280' },
]
</script>

<template>
  <div class="alloc-sim">
    <div class="list-header">
      <h2>📊 成本分摊下钻</h2>
      <div class="tabs">
        <span class="tab active">按部门</span>
        <span class="tab">按应用</span>
        <span class="btn-export">⬇ 导出 CSV</span>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-row">
      <div class="stat-card"><div class="st-label">分摊总额</div><div class="st-value">¥44.0w</div></div>
      <div class="stat-card"><div class="st-label">资源数</div><div class="st-value">1,427</div></div>
      <div class="stat-card"><div class="st-label">最大占比</div><div class="st-value">26%</div></div>
      <div class="stat-card"><div class="st-label">日均成本</div><div class="st-value">¥1.42w</div></div>
    </div>

    <!-- 分摊列表 -->
    <div class="alloc-card">
      <h3>各部门成本占比</h3>
      <div class="alloc-list">
        <div v-for="d in deptSplit" :key="d.name" class="alloc-item">
          <div class="alloc-info">
            <span class="dept-name">{{ d.name }}</span>
            <span class="dept-apps">{{ d.apps }}</span>
          </div>
          <div class="alloc-bar">
            <div class="bar-fill" :style="{ width: `${d.v * 2}%`, background: d.color }"></div>
          </div>
          <div class="alloc-value">{{ d.amount }} ({{ d.v }}%)</div>
          <span class="btn-drill">查看明细 →</span>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <!-- TOP10 -->
      <div class="alloc-card">
        <h3>🏆 TOP10 资源费用</h3>
        <div class="bar-list">
          <div v-for="t in top10" :key="t.name" class="bar-row">
            <span class="bar-name">{{ t.name }}</span>
            <span class="bar-type">{{ t.type }}</span>
            <div class="bar-track"><div class="bar-fill" style="background: #7c3aed"></div></div>
            <span class="bar-val">{{ t.cost }}</span>
          </div>
        </div>
      </div>

      <!-- 数据链路说明 -->
      <div class="alloc-card">
        <h3>🔗 数据来源与分摊链路</h3>
        <div class="chain">
          <span class="chain-node">云账单</span><span class="chain-arrow">→</span>
          <span class="chain-node">Cost Allocation Tag</span><span class="chain-arrow">→</span>
          <span class="chain-node">CostItem 标签</span><span class="chain-arrow">→</span>
          <span class="chain-node">部门/应用聚合</span>
        </div>
        <div class="chain-tip">
          成本分摊依据账单 Cost Allocation Tag（department/application），与资源归属标签分离。
          未打标签的资源归入「未归属」，避免统计失真。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alloc-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  margin-bottom: 20px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.alloc-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 20px 0;
}

.alloc-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.alloc-item:last-child { border-bottom: none; }

.alloc-info {
  width: 160px;
}

.dept-name {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.dept-apps {
  display: block;
  font-size: 12px;
  color: #94a3b8;
}

.alloc-bar {
  flex: 1;
  height: 12px;
  background: #f1f5f9;
  border-radius: 6px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.alloc-value {
  width: 130px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}

/* 追加样式 */
.tabs { display: flex; align-items: center; gap: 8px; }
.tab { padding: 6px 14px; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; color: #475569; cursor: pointer; }
.tab.active { background: #7c3aed; color: #fff; border-color: #7c3aed; font-weight: 600; }
.btn-export { padding: 6px 12px; background: #fff; border: 1px solid #e9d5ff; color: #7c3aed; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04); }
.st-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.st-value { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.btn-drill { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; white-space: nowrap; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.bar-list { display: flex; flex-direction: column; gap: 7px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-name { width: 110px; font-size: 12px; color: #1e293b; font-weight: 500; }
.bar-type { width: 48px; font-size: 11px; color: #94a3b8; }
.bar-track { flex: 1; height: 9px; background: #f1f5f9; border-radius: 5px; overflow: hidden; }
.bar-val { width: 60px; font-size: 12px; color: #334155; text-align: right; font-weight: 500; }
.chain { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.chain-node { padding: 6px 10px; background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 6px; font-size: 12px; color: #7c3aed; font-weight: 500; }
.chain-arrow { color: #cbd5e1; font-size: 14px; }
.chain-tip { font-size: 12px; color: #64748b; line-height: 1.6; background: #f8fafc; border-radius: 8px; padding: 10px 12px; }
</style>
