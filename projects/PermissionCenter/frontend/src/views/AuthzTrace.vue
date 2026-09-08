<template>
  <div class="trace-page">
    <header class="page-header">
      <h1>鉴权链路追踪</h1>
      <span class="page-desc">一次请求从 网关PEP → action解析 → 动作级Casbin → 数据级OpenFGA 的完整链路</span>
    </header>

    <!-- TraceID 搜索 -->
    <div class="search-bar">
      <input v-model="searchTrace" class="search-input" placeholder="输入 TraceID 查看完整链路（如输入为空则显示最近决策）" />
      <button class="btn btn-primary" @click="loadList">查询</button>
    </div>

    <!-- 最近决策列表 -->
    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>TRACE</th><th>用户</th><th>应用</th><th>权限点</th>
            <th>决策</th><th>渠道</th><th>耗时</th><th>引擎</th><th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in logs" :key="d.id" class="clickable" @click="openTrace(d.trace_id)">
            <td class="mono">{{ (d.trace_id || '—').slice(0, 12) }}</td>
            <td class="mono">{{ d.user_id || '—' }}</td>
            <td class="mono">{{ d.app_id || '—' }}</td>
            <td class="mono">{{ d.action }}</td>
            <td><span class="tag" :class="d.decision === 1 ? 'tag-success' : 'tag-danger'">{{ d.decision === 1 ? 'ALLOW' : 'DENY' }}</span></td>
            <td><span class="tag">{{ d.channel === 1 ? 'remote' : 'local' }}</span></td>
            <td class="mono">{{ d.latency_ms }}ms</td>
            <td class="mono">{{ d.pep?.engine || 'action' }}</td>
            <td class="mono text-secondary" style="white-space: nowrap;">{{ fmtTime(d.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="logs.length === 0" class="empty-state">暂无决策记录（先通过网关/鉴权 API 发起请求）</div>
    </div>

    <!-- 链路详情抽屉 -->
    <el-drawer v-model="showTrace" :title="`链路追踪：${traceId || ''}`" size="640">
      <div v-if="traceLogs.length === 0" class="empty-state">该 TraceID 无记录</div>
      <div v-for="(d, idx) in traceLogs" :key="d.id" class="trace-step" :class="{ 'allow': d.decision === 1 }">
        <div class="step-head">
          <span class="step-index">{{ idx + 1 }}</span>
          <span class="step-title">{{ stepTitle(d) }}</span>
          <span class="tag" :class="d.decision === 1 ? 'tag-success' : 'tag-danger'">{{ d.decision === 1 ? 'ALLOW' : 'DENY' }}</span>
        </div>
        <div class="step-body">
          <div class="kv"><span class="k">权限点</span><span class="mono">{{ d.action }}</span></div>
          <div class="kv"><span class="k">原因</span><span>{{ d.reason || '—' }}</span></div>
          <div class="kv"><span class="k">耗时</span><span class="mono">{{ d.latency_ms }}ms</span></div>
          <!-- PEP 解析信息 -->
          <template v-if="d.pep">
            <div class="kv" v-if="d.pep.method"><span class="k">请求</span><span class="mono">{{ d.pep.method }} {{ d.pep.path }}</span></div>
            <div class="kv" v-if="d.pep.match_mode"><span class="k">匹配方式</span><span class="mono">{{ matchModeLabel(d.pep.match_mode) }}</span></div>
            <div class="kv" v-if="d.pep.pattern"><span class="k">路径模式</span><span class="mono">{{ d.pep.pattern }}</span></div>
            <div class="kv" v-if="d.pep.resolved_resource"><span class="k">解析资源</span><span class="mono">{{ d.pep.resolved_resource }}</span></div>
            <div class="kv" v-if="d.pep.model"><span class="k">数据模型</span><span class="mono">{{ d.pep.model }}</span></div>
            <div class="kv" v-if="d.pep.instance"><span class="k">实例</span><span class="mono">{{ d.pep.instance }}</span></div>
            <div class="kv" v-if="d.pep.visible_instances !== undefined"><span class="k">可见实例数</span><span class="mono">{{ d.pep.visible_instances }}</span></div>
            <div class="kv" v-if="d.pep.matched_policy_count !== undefined"><span class="k">命中策略数</span><span class="mono">{{ d.pep.matched_policy_count }}</span></div>
            <!-- PEP 解析步骤 -->
            <div v-if="d.pep.steps?.length" class="steps-box">
              <div class="steps-title">PEP 解析步骤</div>
              <div v-for="s in d.pep.steps" :key="s.step" class="mini-step">
                <span class="step-dot" :class="{ ok: s.ok }"></span>
                <span class="mono" style="font-size: 11px; min-width: 90px;">{{ s.step }}</span>
                <span style="flex: 1;">{{ s.label }}</span>
                <span class="mono text-secondary" style="font-size: 11px;">{{ s.ok ? '✓' : '✗' }}</span>
              </div>
            </div>
          </template>
          <!-- 数据级明细 -->
          <template v-if="d.pep?.engine === 'data'">
            <div class="kv" v-if="d.pep.operation"><span class="k">数据操作</span><span class="mono">{{ d.pep.operation }}</span></div>
            <div class="kv" v-if="d.pep.instance_ids"><span class="k">允许实例</span><span class="mono">{{ (d.pep.instance_ids || []).join('、') }}</span></div>
          </template>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const logs = ref<any[]>([])
const traceLogs = ref<any[]>([])
const showTrace = ref(false)
const traceId = ref('')
const searchTrace = ref('')

async function loadList() {
  const trace = searchTrace.value.trim()
  const data = await api.decisionLogs(trace || undefined)
  logs.value = (data as any).items || []
}

async function openTrace(id: string) {
  if (!id) return
  traceId.value = id
  const data = await api.decisionLogs(id)
  traceLogs.value = (data as any).items || []
  showTrace.value = true
}

function stepTitle(d: any): string {
  if (d.pep?.engine === 'data') return '数据级 · ' + (d.pep.model || '') + ' · ' + (d.pep.operation || d.pep.op || '')
  if (d.pep?.match_mode) return '网关 PEP · ' + (d.pep.method || '') + ' ' + (d.pep.path || '')
  return '动作级 · Casbin'
}

function matchModeLabel(m: string): string {
  return { literal: '字面匹配', template: '路径模板解析', header: 'X-Resource-Type', none: '未解析' }[m] || m
}

function fmtTime(t: string): string {
  if (!t) return '—'
  try { return new Date(t).toLocaleString('zh-CN') } catch { return t }
}

onMounted(loadList)
</script>

<style scoped>
.trace-page { max-width: 1400px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
.search-input {
  flex: 1; padding: 8px 12px; font-size: 13px; font-family: var(--font-mono);
  border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none;
}
.search-input:focus { border-color: var(--accent); }

.panel { border: 1px solid var(--border); background: var(--bg); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 14px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); }
.data-table tr.clickable { cursor: pointer; }
.data-table tr.clickable:hover td { background: var(--bg-hover); }

.btn { padding: 8px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-family: var(--font-mono); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }

.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }

/* 链路步骤 */
.trace-step { border: 1px solid var(--border); margin-bottom: 10px; }
.trace-step.allow { border-left: 3px solid #22c55e; }
.trace-step:not(.allow) { border-left: 3px solid #ef4444; }
.step-head { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.step-index { font-family: var(--font-mono); font-weight: 700; color: var(--text-tertiary); }
.step-title { font-size: 13px; font-weight: 600; flex: 1; }
.step-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.kv { display: flex; gap: 12px; font-size: 13px; }
.kv .k { min-width: 72px; color: var(--text-secondary); font-size: 12px; }
.steps-box { border: 1px dashed var(--border); padding: 10px; margin-top: 6px; background: var(--bg-secondary); }
.steps-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); margin-bottom: 6px; font-family: var(--font-mono); }
.mini-step { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 12px; }
.step-dot { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; }
.step-dot.ok { background: #22c55e; }
</style>
