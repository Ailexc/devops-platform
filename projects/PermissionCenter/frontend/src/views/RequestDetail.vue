<template>
  <div class="req-detail" v-if="data">
    <header class="page-header">
      <button class="back-link" @click="$router.back()">← 返回</button>
      <h1>申请单 <span class="mono">#{{ data.request.id }}</span></h1>
      <span class="page-desc">{{ data.applicant }} · {{ statusLabel(data.request.status) }} · 风险 {{ riskLabel(data.request.risk_level) }}</span>
    </header>

    <div class="panel grid-2">
      <div class="kv"><span class="k">授权主体（grantee）</span><span class="v">{{ data.request.grantee_type || '—' }} · {{ data.request.grantee_name || '—' }}</span></div>
      <div class="kv"><span class="k">申请人（applicant）</span><span class="v">{{ data.applicant }}</span></div>
      <div class="kv"><span class="k">能力包</span><span class="v">{{ data.capability_name || '—' }} <span v-if="data.preset_name" class="tag">/ {{ data.preset_name }}</span></span></div>
      <div class="kv"><span class="k">申请理由</span><span class="v">{{ data.request.reason || '—' }}</span></div>
    </div>

    <!-- T7 多包审批视图：合并展示各包范围与表达式（一单一审批 → 批量开通） -->
    <template v-if="data.request.content?.multi">
      <div class="section-title">📦 多包申请（{{ data.request.content.packages?.length }} 包——单一审批视图，落底各包独立策略）</div>
      <div v-for="p in data.request.content.packages || []" :key="p.capability_id" class="panel multi-pkg-detail">
        <div class="multi-pkg-title">
          <b>{{ p.capability_name }}</b><span class="tag">/ {{ p.preset_name }}</span>
          <span class="tag" :class="(p.risk_label || '').includes('高') ? 'tag-red' : 'tag-amber'">{{ p.risk_label }}</span>
        </div>
        <table class="data-table data-table-sm">
          <thead><tr><th>模型</th><th>类型</th><th>选择值</th></tr></thead>
          <tbody>
            <tr v-for="(s, si) in p.scope_selections || []" :key="si">
              <td class="mono">{{ s.model }}</td>
              <td>{{ SCOPE_LABEL[s.type] || s.type }}</td>
              <td class="mono">{{ s.selectedValue || (s.selectedValues || []).join(', ') || '全部' }}</td>
            </tr>
          </tbody>
        </table>
        <pre class="codeblock">{{ p.scope_expression }}</pre>
      </div>
    </template>

    <div class="section-title" v-else>数据范围选择（v12 结构化）</div>
    <div class="panel">
      <div v-if="!scopeSelections.length" class="empty-state">接口级申请（无数据范围）或接入申请</div>
      <table v-else class="data-table data-table-sm">
        <thead><tr><th>模型</th><th>类型</th><th>选择值</th></tr></thead>
        <tbody>
          <tr v-for="s in scopeSelections" :key="s.model">
            <td class="mono">{{ s.model }}</td>
            <td>{{ SCOPE_LABEL[s.type] || s.type }}</td>
            <td class="mono">{{ s.selectedValue || (s.selectedValues || []).join(', ') || '全部' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="section-title" v-if="!data.request.content?.multi">权限表达式（Casbin + OpenFGA）</div>
    <div class="panel" v-if="!data.request.content?.multi"><pre class="codeblock">{{ data.request.content?.scope_expression || '—' }}</pre></div>

    <div v-if="data.request.content?.onboard" class="section-title">🔑 接入申请 · 凭证</div>
    <div v-if="data.request.content?.onboard" class="panel">
      <div class="kv"><span class="k">鉴权方式</span><span class="v mono">{{ data.request.content.auth_method }}</span></div>
      <div class="kv"><span class="k">网络打通工单</span><span class="v">{{ data.request.content.network_ticket ? '✅ 已提交（并入接入申请）' : '—' }}</span></div>
      <div v-if="data.request.content.onboard_status === 'issued'" class="cred-box">
        <div class="kv"><span class="k">client_id</span><span class="v mono">{{ data.request.content.client_id }}</span></div>
        <div class="kv"><span class="k">client_secret</span><span class="v mono">{{ data.request.content.onboard_secret }}</span></div>
        <div class="hint">⚠️ 明文仅此一次展示，请妥善保存；后续只能轮换。</div>
      </div>
    </div>

    <div class="section-title">审批链</div>
    <div class="panel">
      <div class="flow">
        <div class="flow-step done"><div class="step-title">提交申请</div><div class="step-desc">{{ data.applicant }}</div></div>
        <div v-for="t in data.approval_tasks" :key="t.id" class="flow-step" :class="{ done: t.action === 1 }">
          <div class="step-title">审批节点 #{{ t.step }}</div>
          <div class="step-desc">approver#{{ t.approver_id }} · {{ t.action === 1 ? '✅ 通过' : t.action === 2 ? '❌ 驳回' : '待审批' }} · {{ t.comment || '' }}</div>
        </div>
        <div v-if="!data.approval_tasks.length" class="empty-state">暂无审批记录</div>
        <div class="flow-step"><div class="step-title">授权生效 / 凭证签发</div><div class="step-desc">{{ data.request.status === 2 ? '✅ 已生效' : '待审批通过' }}</div></div>
      </div>
    </div>
  </div>
  <div v-else class="empty-state" style="padding:60px;">加载中…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const data = ref<any>(null)
const SCOPE_LABEL: Record<string, string> = { all: '所有数据', instance: '具体实例', select: '单选', multi_select: '多选', variable: '自动匹配', input: '自由输入' }

const scopeSelections = computed(() => data.value?.request?.content?.scope_selections || [])

function statusLabel(s: number) {
  return ['', '待审批', '已通过', '已拒绝', '已回收'][s] || s
}
function riskLabel(r: number) {
  return ['', '低', '中', '高'][r] || r
}

onMounted(async () => {
  try {
    data.value = await api.requestDetail(Number(route.params.id))
  } catch (e: any) {
    alert(e.message)
  }
})
</script>

<style scoped>
.req-detail { max-width: 900px; }
.page-header { margin-bottom: 18px; }
.page-header h1 { font-size: 22px; font-weight: 700; }
.page-desc { font-size: 12px; color: var(--text-secondary); }
.back-link { font-size: 13px; color: var(--text-secondary); text-decoration: none; background: none; border: none; cursor: pointer; display: block; margin-bottom: 6px; }
.section-title { font-size: 15px; font-weight: 700; margin: 20px 0 10px; }
.panel { border: 1px solid var(--border); background: var(--bg); padding: 16px; margin-bottom: 14px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 18px; }
.kv { display: flex; flex-direction: column; gap: 3px; }
.k { font-size: 11px; color: var(--text-tertiary); }
.v { font-size: 13px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.codeblock { background: var(--bg-secondary); border: 1px solid var(--border); padding: 12px; font-family: var(--font-mono); font-size: 12px; white-space: pre-wrap; }
.flow-step { padding: 8px 12px; border-left: 2px solid var(--border); }
.flow-step.done { border-left-color: var(--success); }
.step-title { font-size: 13px; font-weight: 600; }
.step-desc { font-size: 11px; color: var(--text-secondary); }
.cred-box { border: 1px solid var(--border); background: var(--bg-secondary); padding: 12px; margin-top: 10px; }
.hint { font-size: 11px; color: #d97706; margin-top: 8px; }
.empty-state { padding: 24px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
.tag { font-family: var(--font-mono); font-size: 10px; padding: 2px 8px; background: var(--bg-tertiary); }
.mono { font-family: var(--font-mono); font-size: 12px; }
/* T7 多包审批视图 */
.multi-pkg-detail { margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; }
.multi-pkg-title { display: flex; align-items: center; gap: 8px; font-size: 13px; }
</style>
