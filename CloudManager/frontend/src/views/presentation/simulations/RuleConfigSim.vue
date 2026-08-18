<script setup lang="ts">
// 规则配置模拟（对齐真实 /cost/rules 可配置规则引擎）
const groups = [
  {
    cloud: '全部云',
    icon: '🌐',
    rules: [
      { name: '闲置资源检测', type: '闲置资源', typeIcon: '🔄', priority: 'P1', scope: '全部云 / 全部账号', condition: 'cpu<5% 且连续30天', saving: '¥12,400/月', matched: 86 },
      { name: '未使用资源检测', type: '未使用资源', typeIcon: '🗑️', priority: 'P2', scope: '全部云 / 全部账号', condition: '7天无访问流量', saving: '¥8,900/月', matched: 43 },
    ],
  },
  {
    cloud: 'AWS',
    icon: '☁️',
    rules: [
      { name: '规格降配建议', type: '规格降配', typeIcon: '📉', priority: 'P2', scope: 'AWS / 生产账号', condition: 'CPU峰值<40% 且内存<50%', saving: '¥6,200/月', matched: 28 },
      { name: '预留实例推荐', type: '预留实例', typeIcon: '🎫', priority: 'P3', scope: 'AWS / 生产账号', condition: '持续运行>6个月', saving: '¥5,400/月', matched: 19 },
    ],
  },
  {
    cloud: '阿里云',
    icon: '🟠',
    rules: [
      { name: '预算告警', type: '预算告警', typeIcon: '🚨', priority: 'P1', scope: '阿里云 / 全部账号', condition: '本月花费>预算80%', saving: '¥3,100/月', matched: 12 },
      { name: '趋势上涨检测', type: '趋势上涨', typeIcon: '📈', priority: 'P2', scope: '阿里云 / 全部账号', condition: '连续3月涨幅>15%', saving: '¥4,800/月', matched: 9 },
    ],
  },
  {
    cloud: '腾讯云',
    icon: '🟣',
    rules: [
      { name: '存储优化', type: '存储优化', typeIcon: '💾', priority: 'P3', scope: '腾讯云 / 全部账号', condition: '快照保留>90天', saving: '¥2,300/月', matched: 15 },
    ],
  },
]

const ruleTypes = ['闲置资源', '规格降配', '未使用资源', '预算告警', '趋势上涨', '预留实例', '存储优化']
</script>

<template>
  <div class="rule-sim">
    <div class="page-header">
      <div>
        <h2>⚙️ 规则配置</h2>
        <p class="sub">可配置成本优化规则引擎 · 由运维按需定义检测逻辑，平台统一执行</p>
      </div>
      <div class="header-actions">
        <span class="badge">7 种规则类型</span>
        <span class="btn-run">🚀 立即检测全部</span>
      </div>
    </div>

    <!-- 规则类型说明 -->
    <div class="type-strip">
      <span v-for="t in ruleTypes" :key="t" class="type-chip">{{ t }}</span>
    </div>

    <!-- 按云分组 -->
    <div v-for="g in groups" :key="g.cloud" class="group-card">
      <div class="group-header">
        <span class="cloud-icon">{{ g.icon }}</span>
        <span class="cloud-name">{{ g.cloud }}</span>
        <span class="rule-count">{{ g.rules.length }} 条规则</span>
        <span class="group-total">预估节省 ¥{{ (g.rules.reduce((s, r) => s + parseInt(r.saving.replace(/[^0-9]/g, '')), 0) / 1000).toFixed(1) }}k/月</span>
      </div>
      <div class="rule-list">
        <div v-for="r in g.rules" :key="r.name" class="rule-item">
          <span class="rule-icon">{{ r.typeIcon }}</span>
          <div class="rule-info">
            <div class="rule-name">{{ r.name }}
              <span class="prio" :class="r.priority.toLowerCase()">{{ r.priority }}</span>
            </div>
            <div class="rule-meta">检测范围：{{ r.scope }} · 条件：{{ r.condition }}</div>
          </div>
          <div class="rule-stat">
            <div class="matched">匹配 {{ r.matched }} 资源</div>
            <div class="saving">{{ r.saving }}</div>
          </div>
          <span class="btn-run sm">单独检测</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rule-sim { padding: 16px 20px 24px; background: #f6f7fb; height: 100%; overflow-y: auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.page-header h2 { font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 4px; }
.sub { font-size: 12px; color: #94a3b8; margin: 0; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.badge { padding: 4px 12px; background: #eef2ff; color: #4f46e5; border-radius: 999px; font-size: 12px; font-weight: 600; }
.btn-run {
  padding: 7px 14px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #fff;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}
.btn-run.sm { padding: 5px 10px; font-size: 11px; box-shadow: none; background: #7c3aed; }
.type-strip { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.type-chip { padding: 4px 10px; background: #fff; border: 1px solid #e9d5ff; color: #7c3aed; border-radius: 6px; font-size: 11px; }
.group-card { background: #fff; border: 1px solid #eef0f4; border-radius: 10px; margin-bottom: 12px; overflow: hidden; }
.group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #faf8ff;
  border-bottom: 1px solid #f0ecff;
}
.cloud-icon { font-size: 16px; }
.cloud-name { font-size: 14px; font-weight: 600; color: #0f172a; }
.rule-count { font-size: 11px; color: #94a3b8; }
.group-total { margin-left: auto; font-size: 12px; color: #059669; font-weight: 600; }
.rule-list { padding: 4px 14px; }
.rule-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f6f7fb; }
.rule-item:last-child { border-bottom: none; }
.rule-icon { font-size: 20px; }
.rule-info { flex: 1; }
.rule-name { font-size: 13px; font-weight: 600; color: #0f172a; display: flex; align-items: center; gap: 6px; }
.prio { padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 500; }
.prio.p1 { background: #fef2f2; color: #dc2626; }
.prio.p2 { background: #fff7ed; color: #ea580c; }
.prio.p3 { background: #f1f5f9; color: #64748b; }
.rule-meta { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.rule-stat { text-align: right; margin-right: 12px; }
.matched { font-size: 11px; color: #64748b; }
.saving { font-size: 13px; color: #059669; font-weight: 600; }
</style>
