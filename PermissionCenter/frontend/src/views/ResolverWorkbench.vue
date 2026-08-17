<template>
  <div class="resolver-page">
    <header class="page-header">
      <h1>PEP 解析工作台</h1>
      <span class="page-desc">输入请求 method/path/身份，逐步展示「请求 → 权限点」的完整解析过程（字面优先 → 通用模板）</span>
    </header>

    <div class="request-form panel">
      <div class="form-row">
        <select v-model="form.method" class="select">
          <option>GET</option><option>POST</option><option>PATCH</option><option>DELETE</option>
        </select>
        <input v-model="form.path" class="path-input" placeholder="/api/v1/hosts 或 /api/v1/host（单数走通用模板）或 /api/v1/entities" />
        <input v-model="form.user" class="input" placeholder="用户：alice / client:cloud-mgmt" />
        <input v-model="form.x_resource_type" class="input" placeholder="X-Resource-Type（统一查询入口用）" />
        <button class="btn btn-primary" @click="resolve" :disabled="loading">{{ loading ? '解析中…' : '解析' }}</button>
      </div>
      <div class="hint">快速用例：
        <a @click="fill('GET', '/api/v1/hosts', 'alice', '')">字面匹配</a> ·
        <a @click="fill('GET', '/api/v1/host', 'alice', '')">通用模板（单数）</a> ·
        <a @click="fill('GET', '/api/v1/entities', 'alice', 'host')">统一查询入口</a> ·
        <a @click="fill('POST', '/api/v1/certs', 'alice', '')">写操作无法落资源</a>
      </div>
    </div>

    <div v-if="result" class="result-grid">
      <!-- 解析结果卡片 -->
      <div class="panel">
        <div class="panel-title">解析结果</div>
        <div class="result-big" :class="result.trace?.action ? 'ok' : 'fail'">
          <template v-if="result.trace?.action">
            <div class="res-code mono">{{ result.trace.action.code }}</div>
            <div class="res-meta">
              <span class="tag" :class="matchClass(result.trace.match_mode)">{{ matchModeLabel(result.trace.match_mode) }}</span>
              <span class="mono text-secondary">{{ result.trace.path_pattern }}</span>
              <span v-if="result.trace.resolved_resource" class="mono text-secondary">→ 资源 {{ result.trace.resolved_resource }}</span>
            </div>
          </template>
          <template v-else>
            <div class="res-code fail-text">无法解析 → deny-by-default</div>
            <div class="res-meta">未注册路径或通用接口无法落具体资源类型</div>
          </template>
        </div>
        <div v-if="result.decision" class="decision-box">
          <span class="tag" :class="result.decision.decision ? 'tag-success' : 'tag-danger'">
            {{ result.decision.decision ? 'ALLOW' : 'DENY' }}
          </span>
          <span v-if="!result.decision.decision" class="mono text-secondary">{{ result.decision.code }} · {{ result.decision.reason }}</span>
        </div>
      </div>

      <!-- 解析步骤时间线 -->
      <div class="panel">
        <div class="panel-title">解析步骤（{{ result.trace?.steps?.length || 0 }} 步）</div>
        <div class="steps">
          <div v-for="(s, i) in result.trace?.steps || []" :key="s.step + i" class="step">
            <div class="step-line">
              <span class="step-dot" :class="{ ok: s.ok }"></span>
              <div class="step-content">
                <div class="step-head">
                  <span class="mono step-id">{{ s.step }}</span>
                  <span class="step-label">{{ s.label }}</span>
                  <span class="mono" :class="s.ok ? 'ok-text' : 'fail-text'">{{ s.ok ? '✓' : '✗' }}</span>
                </div>
                <div v-if="s.detail && Object.keys(s.detail).length" class="step-detail mono">
                  <span v-for="(v, k) in s.detail" :key="k" class="detail-item">
                    <span class="text-secondary">{{ k }}:</span> {{ formatDetail(v) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

const form = reactive({ method: 'GET', path: '/api/v1/hosts', user: 'alice', x_resource_type: '' })
const result = ref<any>(null)
const loading = ref(false)

async function resolve() {
  loading.value = true
  try {
    result.value = await api.debugResolve({
      method: form.method, path: form.path, user: form.user, x_resource_type: form.x_resource_type,
    })
  } catch (e: any) {
    result.value = { error: e.message }
  } finally {
    loading.value = false
  }
}

function fill(method: string, path: string, user: string, rt: string) {
  form.method = method
  form.path = path
  form.user = user
  form.x_resource_type = rt
}

function matchModeLabel(m: string): string {
  return { literal: '字面匹配', template: '路径模板解析', header: 'X-Resource-Type', none: '未解析' }[m] || m
}
function matchClass(m: string): string {
  return { literal: 'tag-success', template: 'tag-have', header: 'tag-selected', none: 'tag-danger' }[m] || ''
}
function formatDetail(v: any): string {
  if (Array.isArray(v)) return v.join('、')
  if (typeof v === 'object' && v !== null) return JSON.stringify(v)
  return String(v)
}
</script>

<style scoped>
.resolver-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.panel { border: 1px solid var(--border); background: var(--bg); }
.panel-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); padding: 12px 16px; border-bottom: 1px solid var(--border); font-family: var(--font-mono); }

.request-form { padding: 14px 16px; margin-bottom: 16px; }
.form-row { display: flex; gap: 8px; align-items: center; }
.select, .input, .path-input {
  padding: 8px 12px; font-size: 13px; font-family: var(--font-mono);
  border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none;
}
.select { width: 90px; }
.path-input { flex: 2; }
.input { flex: 1; }
.select:focus, .input:focus, .path-input:focus { border-color: var(--accent); }
.hint { margin-top: 10px; font-size: 12px; color: var(--text-secondary); }
.hint a { color: var(--accent-text); cursor: pointer; text-decoration: underline; margin: 0 2px; }

.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border); border: 1px solid var(--border); }

.result-big { padding: 20px; text-align: center; }
.res-code { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; }
.res-code.ok { color: #22c55e; }
.res-code.fail-text { color: #ef4444; font-size: 16px; }
.res-meta { display: flex; justify-content: center; align-items: center; gap: 8px; font-size: 12px; }
.decision-box { border-top: 1px solid var(--border); padding: 12px 16px; display: flex; align-items: center; gap: 10px; }

.steps { padding: 8px 0; }
.step { padding: 8px 16px; border-bottom: 1px solid var(--border); }
.step:last-child { border-bottom: none; }
.step-line { display: flex; gap: 10px; }
.step-dot { width: 10px; height: 10px; border-radius: 50%; background: #ef4444; margin-top: 4px; flex-shrink: 0; }
.step-dot.ok { background: #22c55e; }
.step-content { flex: 1; }
.step-head { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.step-id { color: var(--text-tertiary); font-size: 11px; min-width: 110px; }
.step-label { flex: 1; }
.step-detail { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 4px; font-size: 11px; }
.detail-item { background: var(--bg-tertiary); padding: 2px 8px; }

.btn { padding: 8px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-family: var(--font-mono); white-space: nowrap; }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn:disabled { opacity: 0.5; }

.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-have { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-selected { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.tag-danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.ok-text { color: #22c55e; }
.fail-text { color: #ef4444; }
</style>
