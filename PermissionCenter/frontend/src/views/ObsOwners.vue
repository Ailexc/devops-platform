<template>
  <div class="obs-owners">
    <PageHeader title="Owner 巡检视图" desc="程序化兜底：应用 owner 失联提醒 → N 次无响应自动停用 → 新 owner 认领恢复">
      <template #actions>
        <button class="btn btn-ghost" @click="runCheck" :disabled="checking">{{ checking ? '巡检中…' : '🔄 手动触发巡检' }}</button>
      </template>
    </PageHeader>

    <div class="info-box">💡 巡检规则：owner 最近 7 天无活动 → 提醒计数 +1；达 <b>3 次</b> 无响应 → 应用自动停用，可由新 owner 通过「认领」恢复。</div>

    <div class="section-title">失联中的 Owner（{{ (data.items || []).length }}）</div>
    <div class="panel">
      <table v-if="(data.items || []).length" class="data-table">
        <thead><tr><th>应用</th><th>Owner</th><th>角色</th><th>提醒次数</th><th>应用状态</th></tr></thead>
        <tbody>
          <tr v-for="it in data.items" :key="it.app_id + '-' + it.owner_id">
            <td><span class="mono">{{ it.app_code }}</span> {{ it.app_name }}</td>
            <td>{{ it.owner_name }}<span class="mono text-secondary" style="margin-left:6px;">({{ it.owner_username }})</span></td>
            <td><span class="tag" :class="it.is_primary ? 'tag-blue' : 'tag-gray'">{{ it.is_primary ? '主' : '次' }}</span></td>
            <td>
              <span class="tag" :class="it.remind_count >= 3 ? 'tag-red' : it.remind_count >= 2 ? 'tag-amber' : 'tag-ok'">{{ it.remind_count }}/3</span>
            </td>
            <td><span class="tag" :class="it.disabled ? 'tag-red' : 'tag-ok'">{{ it.disabled ? '⛔ 已停用' : '运行中' }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">✅ 暂无失联 owner（应用健康）</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const data = ref<any>({})
const checking = ref(false)

async function load() {
  try {
    data.value = await api.debugOwners()
  } catch (e: any) { ElMessage.error(e.message) }
}

async function runCheck() {
  checking.value = true
  try {
    const r: any = await api.ownerCheck()
    ElMessage.success(`巡检完成：${r.items?.length || 0} 项动作`)
    load()
  } catch (e: any) { ElMessage.error(e.message) } finally { checking.value = false }
}

onMounted(load)
</script>

<style scoped>
.obs-owners { padding: 0 24px 40px; }
.info-box { padding: 12px 16px; border-radius: 10px; background: var(--brand-soft); border: 1px solid rgba(59,130,246,.25); font-size: 13px; margin-bottom: 16px; }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }
.panel { border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
.data-table th { font-size: 11px; font-family: var(--font-mono); color: var(--text-secondary); background: var(--bg-secondary); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-blue { background: rgba(59,130,246,.12); color: #2563eb; }
.tag-gray { background: rgba(156,163,175,.15); color: #6b7280; }
.tag-ok { background: rgba(34,197,94,.12); color: #16a34a; }
.tag-amber { background: rgba(245,158,11,.12); color: #d97706; }
.tag-red { background: rgba(239,68,68,.12); color: #dc2626; }
.btn { padding: 6px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); cursor: pointer; }
.btn-ghost { background: var(--bg-card); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
