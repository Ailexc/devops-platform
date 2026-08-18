<script setup lang="ts">
// 分析报告模拟（对齐真实 /cost/reports 左树右表 + 维度联动）
const tree = [
  { name: '全部云 · 4 云', icon: '🌐', children: [
    { name: 'AWS', icon: '☁️', children: [
      { name: '生产账号', icon: '🏢', children: [
        { name: 'us-east-1', icon: '📍', children: [
          { name: 'instance · 14', icon: '🖥️' },
          { name: 'storage · 9', icon: '💾' },
        ]},
        { name: 'ap-southeast-1', icon: '📍', children: [
          { name: 'instance · 8', icon: '🖥️' },
        ]},
      ]},
    ]},
    { name: '阿里云', icon: '🟠', children: [
      { name: '生产账号', icon: '🏢', children: [
        { name: 'cn-hangzhou', icon: '📍', children: [
          { name: 'instance · 21', icon: '🖥️' },
          { name: 'database · 12', icon: '🗄️' },
        ]},
      ]},
    ]},
  ]},
]

const summary = { view: '全部云', matched: 476, saving: '75,800/月', pct: '18.6%' }

const rows = [
  { cloud: 'AWS', account: '生产账号', region: 'us-east-1', type: 'instance', resource: 'web-server-03', rule: '闲置资源', saving: 3200 },
  { cloud: '阿里云', account: '生产账号', region: 'cn-hangzhou', type: 'instance', resource: 'api-server-01', rule: '规格降配', saving: 2800 },
  { cloud: 'AWS', account: '生产账号', region: 'us-east-1', type: 'database', resource: 'db-master-01', rule: '预留实例', saving: 2500 },
  { cloud: '腾讯云', account: '生产账号', region: 'ap-guangzhou', type: 'instance', resource: 'pay-server-02', rule: '预算告警', saving: 0 },
  { cloud: '阿里云', account: '生产账号', region: 'cn-hangzhou', type: 'storage', resource: 'oss-bucket-07', rule: '存储优化', saving: 1800 },
  { cloud: 'AWS', account: '生产账号', region: 'ap-southeast-1', type: 'instance', resource: 'worker-cn-006', rule: '闲置资源', saving: 1500 },
]
</script>

<template>
  <div class="report-sim">
    <div class="page-header">
      <div>
        <h2>📄 分析报告</h2>
        <span class="report-no">报告单号：RPT-20260812-005</span>
      </div>
      <div class="header-actions">
        <span class="badge">2026-08-12 全量检测</span>
        <span class="btn-export">⬇ 导出 CSV</span>
      </div>
    </div>

    <div class="report-body">
      <!-- 左：维度树 -->
      <div class="dim-tree">
        <div class="tree-title">维度下钻</div>
        <div class="tree-item root" v-for="t in tree" :key="t.name">
          <div class="tree-node">
            <span class="node-icon">{{ t.icon }}</span>{{ t.name }}
          </div>
          <div class="tree-item child" v-for="c in t.children" :key="c.name">
            <div class="tree-node" :class="{ active: c.name === '阿里云' }">
              <span class="node-icon">{{ c.icon }}</span>{{ c.name }}
            </div>
            <div class="tree-item grand" v-for="g in c.children" :key="g.name">
              <div class="tree-node"><span class="node-icon">{{ g.icon }}</span>{{ g.name }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右：汇总 + 明细 -->
      <div class="dim-detail">
        <div class="summary-bar">
          <span>当前视图：<b>{{ summary.view }}</b></span>
          <span>匹配资源：<b>{{ summary.matched }}</b></span>
          <span>预估节省：<b class="green">¥{{ summary.saving }}</b></span>
          <span>节省占比：<b>{{ summary.pct }}</b></span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>云厂商</th><th>账号</th><th>区域</th><th>资源类型</th><th>资源</th><th>命中规则</th><th class="right">预估节省</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in rows" :key="r.resource">
                <td>{{ r.cloud }}</td>
                <td>{{ r.account }}</td>
                <td>{{ r.region }}</td>
                <td><span class="type-tag">{{ r.type }}</span></td>
                <td class="res-name">{{ r.resource }}</td>
                <td><span class="rule-tag">{{ r.rule }}</span></td>
                <td class="right green">{{ r.saving ? `¥${r.saving}/月` : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-sim { padding: 16px 20px 24px; background: #f6f7fb; height: 100%; overflow-y: auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.page-header h2 { font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 4px; }
.report-no { font-size: 12px; color: #7c3aed; font-weight: 600; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.badge { padding: 4px 12px; background: #eef2ff; color: #4f46e5; border-radius: 999px; font-size: 12px; font-weight: 600; }
.btn-export { padding: 7px 14px; background: #fff; border: 1px solid #e9d5ff; color: #7c3aed; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
.report-body { display: flex; gap: 12px; background: #fff; border: 1px solid #eef0f4; border-radius: 10px; overflow: hidden; min-height: 380px; }
.dim-tree { width: 230px; border-right: 1px solid #eef0f4; padding: 12px 0; overflow-y: auto; }
.tree-title { font-size: 12px; color: #94a3b8; padding: 0 14px 8px; }
.tree-item.root > .tree-node { font-weight: 600; }
.tree-item { padding-left: 0; }
.tree-item.child { padding-left: 14px; }
.tree-item.grand { padding-left: 28px; }
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
  border-left: 2px solid transparent;
}
.tree-node.active { background: #faf5ff; color: #7c3aed; border-left-color: #7c3aed; font-weight: 500; }
.node-icon { font-size: 13px; }
.dim-detail { flex: 1; padding: 12px 14px; }
.summary-bar { display: flex; gap: 20px; padding: 10px 12px; background: #faf8ff; border: 1px solid #f0ecff; border-radius: 8px; font-size: 12px; color: #64748b; margin-bottom: 12px; flex-wrap: wrap; }
.summary-bar b { color: #0f172a; }
.green { color: #059669 !important; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 8px 10px; color: #64748b; font-weight: 500; background: #f8fafc; border-bottom: 1px solid #eef0f4; }
td { padding: 8px 10px; border-bottom: 1px solid #f6f7fb; color: #334155; }
.right { text-align: right; }
.type-tag, .rule-tag { padding: 2px 8px; background: #f1f5f9; border-radius: 4px; font-size: 11px; }
.rule-tag { background: #faf5ff; color: #7c3aed; }
.res-name { color: #0f172a; font-weight: 500; }
</style>
