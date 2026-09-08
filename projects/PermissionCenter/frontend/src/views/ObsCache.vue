<template>
  <div class="obs-cache">
    <PageHeader title="决策缓存工作台" desc="Redis 决策缓存（authz:dec:*）——策略变更不生效时的首要排查点" />

    <!-- 概览统计 -->
    <div class="stats">
      <div class="stat-card">
        <div class="stat-value">{{ data.dec_count ?? '—' }}</div>
        <div class="stat-label">决策缓存键</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ data.pset_count ?? '—' }}</div>
        <div class="stat-label">策略快照键</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ data.decision_total ?? '—' }}</div>
        <div class="stat-label">累计决策</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ fmtPct(data.hit_rate_pct) }}</div>
        <div class="stat-label">缓存命中率</div>
      </div>
    </div>

    <div class="panel toolbar">
      <div class="text-secondary" style="font-size:12px;">决策缓存 TTL 内命中直接放行；策略发布/变更会全量失效。若修改策略后仍走旧结果，可一键清理。</div>
      <button class="btn btn-danger" @click="clearCache" :disabled="clearing">{{ clearing ? '清理中…' : '🧹 清空决策缓存' }}</button>
    </div>

    <div class="section-title">缓存键明细（值格式：1|pids = allow / 0| = deny）</div>
    <div class="panel">
      <table class="data-table" v-if="(data.entries || []).length">
        <thead><tr><th>缓存键</th><th>值</th><th>剩余 TTL</th><th>判定</th></tr></thead>
        <tbody>
          <tr v-for="e in data.entries" :key="e.key">
            <td class="mono">{{ e.key }}</td>
            <td class="mono">{{ e.value }}</td>
            <td class="mono">{{ e.ttl_seconds }}s</td>
            <td><span class="tag" :class="e.value?.startsWith('1') ? 'tag-ok' : 'tag-amber'">{{ e.value?.startsWith('1') ? 'ALLOW' : 'DENY' }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无决策缓存（产生一次鉴权后出现）</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const data = ref<any>({})
const clearing = ref(false)

function fmtPct(v: any): string {
  return v == null ? '—' : v.toFixed(1) + '%'
}

async function load() {
  try {
    data.value = await api.debugCache()
  } catch (e: any) { ElMessage.error(e.message) }
}

async function clearCache() {
  clearing.value = true
  try {
    const r: any = await api.debugCacheClear()
    ElMessage.success(`已清空 ${r.cleared} 个决策缓存键`)
    load()
  } catch (e: any) { ElMessage.error(e.message) } finally { clearing.value = false }
}

onMounted(load)
</script>

<style scoped>
.obs-cache { padding: 0 24px 40px; }
.stats { display: flex; gap: 16px; margin-bottom: 20px; }
.stat-card { flex: 1; padding: 18px 20px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg-card); }
.stat-value { font-size: 28px; font-weight: 800; line-height: 1; }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }
.panel { border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); padding: 16px; margin-bottom: 14px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
.data-table th { font-size: 11px; font-family: var(--font-mono); color: var(--text-secondary); background: var(--bg-secondary); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: rgba(34,197,94,.12); color: #16a34a; }
.tag-amber { background: rgba(245,158,11,.12); color: #d97706; }
.btn { padding: 6px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); cursor: pointer; }
.btn-danger { background: #ef4444; color: #fff; border-color: #ef4444; }
.btn-danger:hover { opacity: .9; }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
