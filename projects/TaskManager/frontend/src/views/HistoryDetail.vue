<template>
  <div class="detail">
    <div class="hd-top">
      <button class="btn-t btn-3" @click="$router.push('/history')">← 返回列表</button>
      <div class="hd-title">
        <span class="hd-task">{{ record.task || '加载中...' }}</span>
        <span class="sb" :class="statusClass(record.status)">{{ statusLabel(record.status) }}</span>
      </div>
      <span class="hd-meta">{{ record.scope_label || '' }} · ID {{ record.id }}</span>
      <button v-if="canRetry" class="btn-t btn-retry" :disabled="retrying" @click="retry(record.id)">🔄 {{ retrying ? '重试中...' : '重试任务' }}</button>
    </div>

    <div v-if="loading" style="text-align:center;padding:50px;color:var(--t2)">⏳ 正在加载执行详情...</div>
    <div v-else-if="loadError" style="text-align:center;padding:20px;font-size:11px;color:var(--coral)">⚠️ {{ loadError }}</div>
    <template v-else>
      <!-- ① 任务摘要 -->
      <div class="card">
        <div class="card-t">① 任务摘要</div>
        <div class="sum-grid">
          <div class="sum-item"><span class="sum-k">状态</span><span class="sum-v" :class="statusClass(record.status)">{{ statusLabel(record.status) }}</span></div>
          <div class="sum-item"><span class="sum-k">任务粒度</span><span class="sum-v">{{ record.scope_label }}</span></div>
          <div class="sum-item"><span class="sum-k">触发方式</span><span class="sum-v">{{ record.trigger }}</span></div>
          <div class="sum-item"><span class="sum-k">执行目标</span><span class="sum-v">{{ record.target }}</span></div>
          <div class="sum-item"><span class="sum-k">开始时间</span><span class="sum-v">{{ record.started_at || record.start }}</span></div>
          <div class="sum-item"><span class="sum-k">耗时</span><span class="sum-v">{{ record.duration }}</span></div>
          <div class="sum-item"><span class="sum-k">Celery ID</span><span class="sum-v mono">{{ record.celery_task_id }}</span></div>
        </div>
        <div v-if="record.error" class="hd-err">❌ {{ record.error }}</div>
      </div>

      <!-- ② 执行链路（时间线 + 波次进程，失败可钻取） -->
      <div class="card">
        <div class="card-t">② 执行链路</div>
        <!-- 框架事件时间线 -->
        <div v-if="record.lifecycle_events && record.lifecycle_events.length" class="lc-steps">
          <div v-for="(ev, j) in record.lifecycle_events" :key="j" class="lc-step" :class="'lc-ev-' + ev.event">
            <div class="lc-dot" :style="{ background: ev.color || 'var(--t2)' }"></div>
            <div v-if="j < record.lifecycle_events.length - 1" class="lc-line"></div>
            <div class="lc-content">
              <span class="lc-label">{{ ev.label }}</span>
              <span class="lc-gap">{{ gapOf(record.lifecycle_events, j) }}</span>
              <span class="lc-ts">{{ ev.ts_ms || ev.ts }}</span>
              <span v-if="ev.detail" class="lc-detail">{{ ev.detail }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无生命周期数据</div>

        <!-- 资源波次 -->
        <template v-if="resourceChildren.length">
          <div class="wave-title">🌊 Wave 1 · 资源同步（{{ resourceChildren.length }}）</div>
          <div class="proc-list">
            <div v-for="c in resourceChildren" :key="c.id" class="proc-row"
                 :class="{ failed: c.status === 'failed', open: expandedChild === c.id }"
                 @click="toggleChild(c.id)">
              <span class="proc-dot" :class="'pd-' + c.status"></span>
              <span class="proc-name">{{ c.task_name }}</span>
              <span class="proc-dur">{{ c.duration }}</span>
              <span class="sb" :class="statusClass(c.status)">{{ statusLabel(c.status) }}</span>
              <button v-if="c.status === 'failed'" class="btn-t btn-retry-mini" @click.stop="retry(c.id)">🔄 重试</button>
              <span class="proc-arrow">{{ expandedChild === c.id ? '▲' : '▼' }}</span>
              <div v-if="expandedChild === c.id" class="proc-detail">
                <div v-if="c.error" class="proc-err">❌ {{ c.error }}</div>
                <div v-if="childStats(c).length" class="res-fields">
                  <div v-for="f in childStats(c)" :key="f.key" class="res-field">
                    <span class="rf-k">{{ f.label }}</span><span class="rf-v">{{ f.value }}{{ f.unit }}</span>
                  </div>
                </div>
                <div v-if="childLogs(c).length" class="proc-logs">
                  <div class="proc-logs-t">📋 进程日志</div>
                  <div v-for="(line, j) in childLogs(c)" :key="j" class="log-line">
                    <span class="log-ts">{{ line.split(' ')[0] }}</span>
                    <span class="log-msg">{{ line.substring(line.indexOf(' ') + 1) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 关系波次 -->
        <template v-if="relationChildren.length">
          <div class="wave-title">🌊 Wave 2 · 关系同步（{{ relationChildren.length }}）</div>
          <div class="proc-list">
            <div v-for="c in relationChildren" :key="c.id" class="proc-row"
                 :class="{ failed: c.status === 'failed', open: expandedChild === c.id }"
                 @click="toggleChild(c.id)">
              <span class="proc-dot" :class="'pd-' + c.status"></span>
              <span class="proc-name">{{ c.task_name }}</span>
              <span class="proc-dur">{{ c.duration }}</span>
              <span class="sb" :class="statusClass(c.status)">{{ statusLabel(c.status) }}</span>
              <button v-if="c.status === 'failed'" class="btn-t btn-retry-mini" @click.stop="retry(c.id)">🔄 重试</button>
              <span class="proc-arrow">{{ expandedChild === c.id ? '▲' : '▼' }}</span>
              <div v-if="expandedChild === c.id" class="proc-detail">
                <div v-if="c.error" class="proc-err">❌ {{ c.error }}</div>
                <div v-if="childStats(c).length" class="res-fields">
                  <div v-for="f in childStats(c)" :key="f.key" class="res-field">
                    <span class="rf-k">{{ f.label }}</span><span class="rf-v">{{ f.value }}{{ f.unit }}</span>
                  </div>
                </div>
                <div v-if="childLogs(c).length" class="proc-logs">
                  <div class="proc-logs-t">📋 进程日志</div>
                  <div v-for="(line, j) in childLogs(c)" :key="j" class="log-line">
                    <span class="log-ts">{{ line.split(' ')[0] }}</span>
                    <span class="log-msg">{{ line.substring(line.indexOf(' ') + 1) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ③ 日志 -->
      <div class="card">
        <div class="card-t">③ 日志</div>
        <div v-if="record.error" style="color:#c0392b;font-size:11px;margin-bottom:6px">❌ {{ record.error }}</div>
        <div v-if="logs.length" class="log-lines">
          <div v-for="(line, j) in logs" :key="j" class="log-line">
            <span class="log-ts">{{ line.split(' ')[0] }}</span>
            <span class="log-msg">{{ line.substring(line.indexOf(' ') + 1) }}</span>
          </div>
        </div>
        <div v-else-if="record.detail" class="log-content">{{ record.detail }}</div>
        <div v-else class="empty-hint">暂无日志信息</div>
      </div>

      <!-- ④ 结果（统一结构：summary + stats + artifacts） -->
      <div class="card">
        <div class="card-t">④ 结果</div>
        <template v-if="record.result">
          <div v-if="record.result.summary" class="res-summary">{{ record.result.summary }}</div>
          <div v-if="resultStats.length" class="res-fields">
            <div v-for="f in resultStats" :key="f.key" class="res-field">
              <span class="rf-k">{{ f.label }}</span><span class="rf-v">{{ f.value }}{{ f.unit }}</span>
            </div>
          </div>
          <div v-if="artifacts.length" class="artifacts">
            <div class="artifacts-t">📦 产物</div>
            <div v-for="a in artifacts" :key="a.path" class="artifact-row">
              <span class="artifact-ic">📄</span>
              <span class="artifact-name">{{ a.name }}</span>
              <span class="artifact-size">{{ fmtSize(a.size) }}</span>
              <button class="btn-t btn-3" @click="previewFile(a.path)">👁️ 预览</button>
            </div>
          </div>
          <div v-if="!resultStats.length && !artifacts.length && !record.result.summary" class="empty-hint">暂无结构化结果</div>
        </template>
        <div v-else class="empty-hint">暂无执行结果</div>
      </div>
    </template>

    <!-- 文件预览弹窗 -->
    <div v-if="previewVisible" class="preview-overlay" @click.self="previewVisible = false">
      <div class="preview-modal">
        <div class="preview-header">
          <span class="preview-title">{{ previewPath.split('/').pop() }}</span>
          <button class="preview-close" @click="previewVisible = false">✕</button>
        </div>
        <pre class="preview-body">{{ previewContent }}</pre>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toastMsg" class="toast" :class="toastType">{{ toastMsg }}</div>
    </transition>
  </div>
</template>

<script>
import { fetchHistoryDetail, retryHistory, previewTestFile } from '../api/index.js'

export default {
  name: 'HistoryDetail',
  data() {
    return {
      record: {},
      loading: true,
      loadError: '',
      expandedChild: null,
      previewVisible: false,
      previewPath: '',
      previewContent: '',
      retrying: false,
      toastMsg: '',
      toastTimer: null,
    }
  },
  computed: {
    recordId() {
      return this.$route.params.id
    },
    // 结果指标（统一结构 stats；兼容旧结构平铺 details）
    resultStats() {
      const r = this.record.result
      if (!r) return []
      if (Array.isArray(r.stats) && r.stats.length) return r.stats
      const details = r.details || r
      if (typeof details !== 'object') return []
      const skip = new Set(['children', 'params', 'logs', 'bindings', 'topics', 'top_authors', 'edition_stats', 'results', 'samples', 'preview'])
      return Object.entries(details)
        .filter(([k, v]) => !skip.has(k) && ['number', 'string', 'boolean'].includes(typeof v) && v !== null && v !== undefined)
        .map(([k, v]) => ({ key: k, label: k, value: String(v), unit: '' }))
    },
    // 产物（统一结构 artifacts；兼容旧 file/report_file/data_file）
    artifacts() {
      const r = this.record.result
      if (!r) return []
      if (Array.isArray(r.artifacts) && r.artifacts.length) return r.artifacts
      const list = []
      for (const p of [r.file, r.report_file, r.data_file]) {
        if (p) list.push({ name: String(p).split('/').pop(), path: p, kind: '', size: 0 })
      }
      return list
    },
    logs() {
      return (this.record.result && this.record.result.logs) || []
    },
    children() {
      return this.record.children || []
    },
    resourceChildren() {
      return this.children.filter(c => {
        const d = (c.result && c.result.details) || c.result || {}
        return 'added' in d || 'resource' in d
      })
    },
    relationChildren() {
      return this.children.filter(c => {
        const d = (c.result && c.result.details) || c.result || {}
        return 'bound' in d || ('source' in d && 'target' in d)
      })
    },
    canRetry() {
      return ['failed', 'partial'].includes(this.record.status)
    },
  },
  mounted() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      this.loadError = ''
      try {
        const res = await fetchHistoryDetail(this.recordId)
        this.record = res.data || {}
      } catch (e) {
        console.error('加载执行详情失败:', e)
        this.loadError = '加载失败：' + (e.response?.data?.error || e.message)
      } finally { this.loading = false }
    },
    // 相邻事件时间差：显示 +X.Xs（一眼看出哪一步慢）
    gapOf(events, j) {
      if (j === 0) return ''
      const parse = (s) => {
        if (!s) return null
        const m = String(s).match(/(\d{2}):(\d{2}):(\d{2})(?:\.(\d{3}))?/)
        if (!m) return null
        return (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) + ((+m[4] || 0) / 1000)
      }
      const cur = parse(events[j].ts_ms || events[j].ts)
      const prev = parse(events[j - 1].ts_ms || events[j - 1].ts)
      if (cur === null || prev === null) return ''
      const diff = cur - prev
      if (diff < 0) return ''
      return diff >= 60 ? `+${Math.floor(diff / 60)}m${Math.round(diff % 60)}s` : `+${diff.toFixed(1)}s`
    },
    childStats(c) {
      const r = c.result || {}
      if (Array.isArray(r.stats) && r.stats.length) return r.stats
      const d = r.details || {}
      return Object.entries(d)
        .filter(([k, v]) => !['bindings', 'samples', 'source', 'target', 'key', 'resource', 'added', 'updated', 'deleted', 'unchanged'].includes(k) && ['number', 'string', 'boolean'].includes(typeof v))
        .map(([k, v]) => ({ key: k, label: k, value: String(v), unit: '' }))
    },
    childLogs(c) {
      return (c.result && c.result.logs) || []
    },
    toggleChild(id) {
      this.expandedChild = this.expandedChild === id ? null : id
    },
    async retry(id) {
      this.retrying = true
      try {
        // id 形如 "#00297"，需剥离前缀（否则 # 被当作 URL fragment 截断）
        const numId = String(id).replace(/^#/, '')
        const res = await retryHistory(numId)
        this.toast(`✅ 已重新下发，执行 ID #${res.data.execution_id}`)
        setTimeout(() => this.$router.push(`/history/${res.data.execution_id}`), 600)
      } catch (e) {
        this.toast(`❌ ${e.response?.data?.error || e.message}`, 'err')
      } finally { this.retrying = false }
    },
    async previewFile(path) {
      try {
        const res = await previewTestFile(path)
        this.previewContent = res.data?.content || '(空文件)'
        this.previewPath = path
        this.previewVisible = true
      } catch (e) {
        this.previewContent = '⚠️ 预览失败: ' + (e.message || e)
        this.previewPath = path
        this.previewVisible = true
      }
    },
    fmtSize(size) {
      if (!size) return ''
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / 1024 / 1024).toFixed(1) + ' MB'
    },
    toast(msg, type = 'ok') {
      this.toastMsg = msg
      this.toastType = type
      clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => { this.toastMsg = '' }, 3200)
    },
    statusClass(st) {
      return { success: 'sb-o', failed: 'sb-f', partial: 'sb-w', running: 'sb-w' }[st] || 'sb-s'
    },
    statusLabel(st) {
      return { success: '✅ 成功', failed: '❌ 失败', partial: '⚠️ 部分失败', running: '⏳ 运行中' }[st] || st
    },
  },
}
</script>

<style scoped>
/* 注意：根类不能用 .hd —— 与 App.vue 全局 .hd（顶部 header 深色渐变+flex）冲突 */
.detail{max-width:1100px;margin:0 auto}
.hd-top{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.hd-title{display:flex;align-items:center;gap:10px;flex:1;min-width:0}
.hd-task{font-size:16px;font-weight:700;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hd-meta{font-size:10px;color:var(--t2)}
.btn-t{font-size:10px;padding:5px 12px;border-radius:5px;font-weight:600;border:none;cursor:pointer;white-space:nowrap}
.btn-3{background:var(--border);color:var(--text)}
.btn-retry{background:var(--cl);color:#c0392b}
.btn-retry-mini{background:var(--cl);color:#c0392b;font-size:9px;padding:2px 8px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin-bottom:12px}
.card-t{font-size:11px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.sum-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.sum-item{display:flex;flex-direction:column;gap:3px}
.sum-k{font-size:9px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.3px}
.sum-v{font-size:12px;font-weight:500;color:var(--text)}
.mono{font-family:'SF Mono',monospace;font-size:10px;color:var(--blue);word-break:break-all}
.hd-err{margin-top:10px;font-size:11px;color:#c0392b;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.2);border-radius:6px;padding:8px 10px}
.sb{font-size:9px;padding:2px 9px;border-radius:5px;font-weight:600;display:inline-block}
.sb-o{background:var(--tl);color:#1a7a6e}
.sb-f{background:var(--cl);color:#c0392b}
.sb-w{background:var(--al);color:#a67c00}
.sb-s{background:var(--border);color:var(--t2)}
.empty-hint{font-size:11px;color:var(--t2);padding:6px 0}

/* 框架事件时间线 */
.lc-steps{position:relative;padding-left:16px;margin-bottom:6px}
.lc-step{position:relative;padding-bottom:10px;display:flex;align-items:flex-start}
.lc-step:last-child{padding-bottom:0}
.lc-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:3px;position:relative;z-index:1}
.lc-line{position:absolute;left:3px;top:11px;bottom:-1px;width:2px;background:var(--border)}
.lc-content{margin-left:10px;font-size:11px;line-height:1.5}
.lc-label{font-weight:500;color:var(--text)}
.lc-gap{font-family:'SF Mono',monospace;font-size:9px;color:var(--blue);margin-left:6px}
.lc-ts{font-family:'SF Mono',monospace;font-size:9px;color:var(--t2);margin-left:6px}
.lc-detail{display:block;font-size:10px;color:var(--t2);margin-top:1px}

/* 波次进程列表 */
.wave-title{font-size:11px;font-weight:700;color:var(--blue);margin:14px 0 8px;padding:6px 10px;background:var(--bl);border-radius:6px}
.proc-list{display:flex;flex-direction:column;gap:5px;margin-bottom:4px}
.proc-row{display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--card);border:1px solid var(--border);border-radius:8px;font-size:11px;cursor:pointer;transition:border-color .15s;flex-wrap:wrap}
.proc-row:hover{border-color:var(--blue)}
.proc-row.failed{border-color:var(--coral);background:rgba(239,68,68,.03)}
.proc-row.open{border-color:var(--blue)}
.proc-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.pd-success{background:var(--teal)}
.pd-failed{background:var(--coral)}
.pd-running{background:var(--orange);animation:pulse 1.2s infinite}
.pd-partial{background:var(--orange)}
@keyframes pulse{50%{opacity:.3}}
.proc-name{font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.proc-dur{font-size:10px;color:var(--t2);font-family:'SF Mono',monospace}
.proc-arrow{font-size:9px;color:var(--t2);flex-shrink:0}
.proc-detail{flex-basis:100%;border-top:1px dashed var(--border);margin-top:8px;padding-top:8px}
.proc-err{font-size:11px;color:#c0392b;margin-bottom:8px;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:6px;padding:6px 10px}
.proc-logs{margin-top:8px}
.proc-logs-t{font-size:9px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px}

/* 结果 */
.res-summary{font-size:12px;font-weight:500;color:var(--text);margin-bottom:10px}
.res-fields{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.res-field{display:flex;flex-direction:column;gap:2px;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px 12px}
.rf-k{font-size:9px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.3px}
.rf-v{font-size:13px;font-weight:600;color:var(--text);word-break:break-all}
.artifacts{margin-top:12px;border-top:1px dashed var(--border);padding-top:10px}
.artifacts-t{font-size:10px;font-weight:600;color:var(--t2);margin-bottom:6px}
.artifact-row{display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--bg);border:1px solid var(--border);border-radius:8px;margin-bottom:5px;font-size:11px}
.artifact-ic{font-size:14px}
.artifact-name{font-family:'SF Mono',monospace;font-size:10px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text)}
.artifact-size{font-size:9px;color:var(--t2);flex-shrink:0}

/* 日志 */
.log-content{font-size:11px;color:var(--text);line-height:1.6;white-space:pre-wrap;word-break:break-all}
.log-lines{font-size:10px;font-family:'SF Mono',monospace;line-height:1.8}
.log-line{display:flex;gap:8px}
.log-ts{color:var(--t2);flex-shrink:0;min-width:60px}
.log-msg{color:var(--text)}

/* 文件预览 */
.preview-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;display:flex;align-items:center;justify-content:center}
.preview-modal{background:var(--card);border:1px solid var(--border);border-radius:8px;width:70vw;max-height:80vh;display:flex;flex-direction:column;overflow:hidden}
.preview-header{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-bottom:1px solid var(--border)}
.preview-title{font-size:12px;font-weight:600;color:var(--text)}
.preview-close{background:none;border:none;font-size:14px;cursor:pointer;color:var(--t2);padding:2px 6px;border-radius:4px}
.preview-close:hover{background:var(--border)}
.preview-body{flex:1;overflow:auto;padding:12px 16px;font-size:10px;font-family:'SF Mono',monospace;line-height:1.6;margin:0;white-space:pre-wrap;word-break:break-all}

/* Toast */
.toast{position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:1200;padding:9px 18px;border-radius:8px;font-size:12px;font-weight:600;box-shadow:0 6px 24px rgba(0,0,0,.18);max-width:80vw}
.toast.ok{background:#0f766e;color:#fff}
.toast.err{background:#c0392b;color:#fff}
.toast-enter-active,.toast-leave-active{transition:all .25s}
.toast-enter-from,.toast-leave-to{opacity:0;transform:translateX(-50%) translateY(-8px)}
</style>
