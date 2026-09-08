<template>
  <div class="obs-ofga">
    <PageHeader title="数据面图谱（OpenFGA）" desc="实例级授权关系引擎（CNCF/Zanzibar）——数据级授权的关系物化全貌" />

    <div class="stats">
      <div class="stat-card"><div class="stat-value mono">{{ data.total_tuples ?? 0 }}</div><div class="stat-label">关系元组</div></div>
      <div class="stat-card"><div class="stat-value mono">{{ (data.types || []).length }}</div><div class="stat-label">资源类型</div></div>
      <div class="stat-card"><div class="stat-value mono sm">{{ (data.model_id || '').slice(0, 12) }}</div><div class="stat-label">模型 ID</div></div>
    </div>

    <div class="section-title">授权模型（type 定义）</div>
    <div class="panel">
      <div v-if="(data.type_defs || []).length" class="type-list">
        <div v-for="t in data.type_defs" :key="t.type" class="type-item">
          <span class="mono type-name">{{ t.type }}</span>
          <span v-for="(r, rk) in t.relations || {}" :key="rk" class="relation-chip mono">{{ rk }}</span>
        </div>
      </div>
      <div v-else class="empty-state">暂无授权模型</div>
    </div>

    <div class="section-title">关系元组（按资源类型分组）</div>
    <div class="panel">
      <div v-if="(data.by_type || []).length">
        <div v-for="g in data.by_type" :key="g.type" class="type-group">
          <div class="group-head"><span class="mono group-type">{{ g.type }}</span><span class="badge">{{ g.count }} 条</span></div>
          <div class="tuple-list">
            <div v-for="(t, i) in g.tuples" :key="i" class="tuple-row mono">
              <span class="t-user">{{ t.user }}</span>
              <span class="t-rel">—{{ t.relation }}→</span>
              <span class="t-obj">{{ t.object }}</span>
            </div>
            <div v-if="!g.tuples.length" class="empty-state">无关系</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">暂无关系元组</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const data = ref<any>({})

onMounted(async () => {
  try {
    data.value = await api.debugOfga()
  } catch (e: any) { ElMessage.error(e.message) }
})
</script>

<style scoped>
.obs-ofga { padding: 0 24px 40px; }
.stats { display: flex; gap: 16px; margin-bottom: 20px; }
.stat-card { flex: 1; padding: 16px 20px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg-card); }
.stat-value { font-size: 24px; font-weight: 800; line-height: 1; }
.stat-value.sm { font-size: 13px; }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }
.panel { border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); padding: 16px; }
.type-list { display: flex; flex-direction: column; gap: 8px; }
.type-item { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-inset); }
.type-name { font-weight: 700; color: var(--brand); }
.relation-chip { font-size: 11px; padding: 2px 8px; background: var(--brand-soft); color: var(--brand-strong); border-radius: 999px; }
.type-group { margin-bottom: 16px; }
.group-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.group-type { font-weight: 700; font-size: 13px; }
.badge { font-size: 11px; padding: 2px 8px; background: var(--bg-tertiary); border-radius: 999px; font-family: var(--font-mono); }
.tuple-list { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.tuple-row { display: flex; gap: 8px; padding: 6px 10px; border-bottom: 1px dashed var(--border); font-size: 12px; }
.tuple-row:last-child { border-bottom: none; }
.t-user { color: var(--text); }
.t-rel { color: var(--text-tertiary); }
.t-obj { color: var(--brand); }
.mono { font-family: var(--font-mono); }
.empty-state { padding: 24px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
