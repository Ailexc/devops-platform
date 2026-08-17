<template>
  <div class="obs-metrics">
    <PageHeader title="鉴权指标面板" desc="从决策日志聚合：决策量 / 允许拒绝 / 缓存命中 / 延迟 / 趋势 / Top 动作" />

    <div v-if="data.summary" class="stats">
      <div class="stat-card">
        <div class="stat-value">{{ data.summary.total ?? 0 }}</div>
        <div class="stat-label">累计决策</div>
      </div>
      <div class="stat-card tone-green">
        <div class="stat-value">{{ data.summary.allow ?? 0 }}</div>
        <div class="stat-label">允许</div>
      </div>
      <div class="stat-card tone-red">
        <div class="stat-value">{{ data.summary.deny ?? 0 }}</div>
        <div class="stat-label">拒绝</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ pct(data.summary.source_dist) }}</div>
        <div class="stat-label">缓存命中率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ data.summary.p95 ?? 0 }}<span class="unit">ms</span></div>
        <div class="stat-label">P95 延迟</div>
      </div>
    </div>

    <div v-if="data.summary" class="stats secondary">
      <div class="stat-card small"><div class="stat-label">P50</div><div class="stat-value sm">{{ data.summary.p50 ?? 0 }}ms</div></div>
      <div class="stat-card small"><div class="stat-label">P90</div><div class="stat-value sm">{{ data.summary.p90 ?? 0 }}ms</div></div>
      <div v-for="(v, k) in data.summary.source_dist || {}" :key="k" class="stat-card small">
        <div class="stat-label">来源·{{ k }}</div><div class="stat-value sm">{{ v }}</div>
      </div>
    </div>

    <!-- 趋势图（纯 CSS 条形图，无第三方依赖） -->
    <div class="section-title">最近 24h 决策趋势</div>
    <div class="panel">
      <div v-if="(data.trend || []).length" class="trend">
        <div v-for="(t, i) in data.trend" :key="i" class="trend-col" :title="`${t.hour} 总${t.total} 允${t.allow} 拒${t.deny}`">
          <div class="trend-bars">
            <div class="bar allow" :style="{ height: barH(t.allow) }"></div>
            <div class="bar deny" :style="{ height: barH(t.deny) }"></div>
          </div>
          <div class="trend-hour">{{ shortHour(t.hour) }}</div>
        </div>
      </div>
      <div v-else class="empty-state">暂无决策数据</div>
      <div class="legend">
        <span><i class="dot allow"></i> 允许</span>
        <span><i class="dot deny"></i> 拒绝</span>
      </div>
    </div>

    <div class="section-title">Top 被访问权限点</div>
    <div class="panel">
      <div v-if="(data.top_actions || []).length" class="top-list">
        <div v-for="(a, i) in data.top_actions" :key="i" class="top-row">
          <span class="top-idx mono">{{ i + 1 }}</span>
          <span class="mono top-action">{{ a.action }}</span>
          <span class="top-total">{{ a.total }} 次</span>
        </div>
      </div>
      <div v-else class="empty-state">暂无数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const data = ref<any>({})
const maxTotal = ref(1)

function pct(dist: any): string {
  if (!dist) return '—'
  const total = Object.values(dist).reduce((s: any, v: any) => s + v, 0)
  if (!total) return '—'
  return ((dist.cache || 0) / total * 100).toFixed(1) + '%'
}
function barH(v: any): string {
  const h = Math.max((v || 0) / maxTotal.value * 60, 2)
  return h + 'px'
}
function shortHour(h: string): string {
  return h ? h.slice(11) : ''
}

onMounted(async () => {
  try {
    data.value = await api.debugMetrics()
    if ((data.value.trend || []).length) {
      maxTotal.value = Math.max(...data.value.trend.map((t: any) => t.total || 0), 1)
    }
  } catch (e: any) { ElMessage.error(e.message) }
})
</script>

<style scoped>
.obs-metrics { padding: 0 24px 40px; }
.stats { display: flex; gap: 16px; margin-bottom: 14px; }
.stats.secondary { margin-bottom: 20px; }
.stat-card { flex: 1; padding: 16px 20px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg-card); }
.stat-card.small { flex: 1; }
.stat-value { font-size: 28px; font-weight: 800; line-height: 1; }
.stat-value.sm { font-size: 20px; margin-top: 6px; }
.stat-value .unit { font-size: 14px; font-weight: 400; margin-left: 4px; color: var(--text-tertiary); }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }
.tone-green .stat-value { color: #16a34a; }
.tone-red .stat-value { color: #ef4444; }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }
.panel { border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); padding: 16px; }
.trend { display: flex; align-items: flex-end; gap: 4px; height: 120px; overflow-x: auto; padding-bottom: 20px; }
.trend-col { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; flex: 1; min-width: 28px; height: 100%; }
.trend-bars { display: flex; align-items: flex-end; gap: 2px; height: 100%; }
.bar { width: 8px; border-radius: 2px 2px 0 0; }
.bar.allow { background: #22c55e; }
.bar.deny { background: #ef4444; }
.trend-hour { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); margin-top: 4px; }
.legend { display: flex; gap: 16px; margin-top: 10px; font-size: 12px; color: var(--text-secondary); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; vertical-align: middle; }
.dot.allow { background: #22c55e; }
.dot.deny { background: #ef4444; }
.top-list { display: flex; flex-direction: column; }
.top-row { display: flex; align-items: center; gap: 12px; padding: 8px 4px; border-bottom: 1px dashed var(--border); font-size: 13px; }
.top-row:last-child { border-bottom: none; }
.top-idx { color: var(--text-tertiary); }
.top-action { flex: 1; }
.top-total { font-weight: 600; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
