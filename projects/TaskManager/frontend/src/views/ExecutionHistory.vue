<template>
  <div class="history">
    <div class="fl">
      <select v-model="filterModule" class="fl-s">
        <option value="">全部模块</option>
        <option value="AWS">☁️ AWS</option>
        <option value="内部">🔌 内部系统</option>
        <option value="巡检">🔍 巡检</option>
        <option value="测试">🧪 测试</option>
      </select>
      <select v-model="filterPeriod" class="fl-s">
        <option value="24h">最近 24 小时</option>
        <option value="7d">最近 7 天</option>
        <option value="30d">最近 30 天</option>
      </select>
      <input v-model="filterSearch" class="fl-inp" placeholder="搜索任务 ID 或名称...">
      <span style="font-size:10px;color:var(--t2);margin-left:auto">共 {{ filteredRecords.length }} 条记录 · 总计 {{ totalRecords }}</span>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px;color:var(--t2)">⏳ 正在加载执行历史...</div>
    <div v-else-if="loadError" style="text-align:center;padding:12px;font-size:11px;color:var(--coral);border:1px solid rgba(239,68,68,.2);border-radius:8px;background:rgba(239,68,68,.05)">⚠️ {{ loadError }}</div>

    <div class="tw">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>模块</th>
            <th>任务</th>
            <th>目标</th>
            <th>粒度</th>
            <th>触发方式</th>
            <th>状态</th>
            <th>开始</th>
            <th>耗时</th>
            <th style="width:70px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in filteredRecords" :key="i" class="ex-tr" @click="goDetail(r)">
            <td style="font-family:'SF Mono',monospace;font-size:10px">{{ r.id }}</td>
            <td><span class="tag" :class="r.modCls">{{ r.mod }}</span></td>
            <td style="font-weight:500">{{ r.task }}</td>
            <td style="font-size:10px">{{ r.target }}</td>
            <td><span class="tag" :class="scopeCls(r.scope)">{{ r.scopeLabel }}</span></td>
            <td style="font-size:10px;color:var(--t2)">{{ r.trig }}</td>
            <td><span class="sb" :class="statusClass(r.st)">{{ statusLabel(r.st) }}</span></td>
            <td style="font-size:10px">{{ r.start }}</td>
            <td style="font-weight:500">{{ r.dur }}</td>
            <td>
              <button class="btn-t btn-3" @click.stop="goDetail(r)">详情 →</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

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
  </div>
</template>

<script>
import { fetchHistory, previewTestFile } from '../api/index.js'

const moduleClsMap = { 'AWS': 'b', '内部': 'p', '巡检': 'o', '测试': 'g' }
const moduleIconMap = { 'AWS': '☁️', '内部': '🔌', '巡检': '🔍', '测试': '🧪' }

export default {
  name: 'ExecutionHistory',
  data() {
    return {
      filterPeriod: '24h',
      filterModule: '',
      filterSearch: '',
      loading: true,
      loadError: '',
      records: [],
      totalRecords: 0,
      previewVisible: false,
      previewPath: '',
      previewContent: '',
    }
  },
  computed: {
    filteredRecords() {
      return this.records.filter(r => {
        if (this.filterModule && !r.mod.includes(this.filterModule)) return false
        if (this.filterSearch && !r.id.includes(this.filterSearch) && !r.task.includes(this.filterSearch)) return false
        return true
      })
    },
  },
  mounted() {
    if (this.$route.query.task) {
      const taskName = this.$route.query.task
      if (taskName.includes('数据完整性') || taskName.includes('安全组') || taskName.includes('证书') || taskName.includes('标签') || taskName.includes('成本') || taskName.includes('闲置')) {
        this.filterModule = '巡检'
      }
    }
    this.loadData()
  },
  methods: {
    goDetail(r) {
      // r.id 形如 "#00053" → 提取数字跳转详情页
      const id = String(r.id).replace('#', '')
      this.$router.push(`/history/${id}`)
    },
    async previewFile(filePath) {
      try {
        const res = await previewTestFile(filePath)
        this.previewContent = res.data?.content || '(空文件)'
        this.previewPath = filePath
        this.previewVisible = true
      } catch (e) {
        this.previewContent = '⚠️ 预览失败: ' + (e.message || e)
        this.previewPath = filePath
        this.previewVisible = true
      }
    },
    async loadData() {
      this.loading = true
      this.loadError = ''
      try {
        const res = await fetchHistory()
        const data = res.data || {}
        this.records = (data.records || []).map(r => ({
          id: r.id,
          mod: moduleIconMap[r.module] ? `${moduleIconMap[r.module]} ${r.module}` : r.module,
          modCls: moduleClsMap[r.module] || 'p',
          task: r.task,
          target: r.target,
          trig: r.trigger,
          scope: r.scope || 'region',
          scopeLabel: r.scope_label || r.scope || '区域级',
          st: r.status,
          start: r.start,
          dur: r.duration,
          err: r.error,
          det: r.detail,
          rawResult: r.result,
          logs: (r.result && r.result.logs) || [],
          lifecycle: r.lifecycle_events || [],
        }))
        this.totalRecords = data.total ?? this.records.length
      } catch (e) {
        console.error('加载执行历史失败:', e)
        this.loadError = '加载数据失败，当前展示本地演示数据'
        this.records = [
          { id:'#10342', mod:'☁️ AWS', modCls:'b', task:'生产-apne1 全量', target:'生产 / apne1', trig:'Cron', st:'success', start:'15:26', dur:'2m34s', det:'EC2↑5✏️3↓1, VPC不变', rawResult: { results: { EC2: { added: 5, updated: 3, deleted: 1, unchanged: 42 }, SecurityGroup: { added: 0, updated: 0, deleted: 0, unchanged: 18 }, NetworkInterface: { added: 2, updated: 1, deleted: 0, unchanged: 12 } } }, lifecycle: [
            { ts_ms:'15:26:01.000', event:'created', label:'📥 任务创建', detail:'account: 生产, region: apne1, mode: full', color:'var(--blue)' },
            { ts_ms:'15:26:01.012', event:'dispatched', label:'🚀 任务派发', detail:'celery_task_id: a1b2c3d4e5', color:'var(--purple)' },
            { ts_ms:'15:26:02.340', event:'received', label:'🏃 Worker 接收', detail:'task: resource_modules.ec2.celery_tasks.sync_ec2_compute', color:'var(--teal)' },
            { ts_ms:'15:28:34.890', event:'completed', label:'✅ 执行完成', detail:'', color:'var(--teal)' },
          ] },
          { id:'#10341', mod:'🔌 内部', modCls:'p', task:'钉钉审批增量', target:'钉钉 OAPI', trig:'定时(15min)', st:'success', start:'15:30', dur:'45s', det:'审批实例↑3✏️8', rawResult: { summary: '审批实例↑3✏️8', duration: '45s' }, lifecycle: [
            { ts_ms:'15:30:00.000', event:'created', label:'📥 任务创建', detail:'account: 内部, trigger: 定时(15min)', color:'var(--blue)' },
            { ts_ms:'15:30:00.005', event:'dispatched', label:'🚀 任务派发', detail:'celery_task_id: f6e7d8c9b0', color:'var(--purple)' },
            { ts_ms:'15:30:01.200', event:'received', label:'🏃 Worker 接收', detail:'task: connector.dingtalk_sync', color:'var(--teal)' },
            { ts_ms:'15:30:45.100', event:'completed', label:'✅ 执行完成', detail:'', color:'var(--teal)' },
          ] },
          { id:'#10340', mod:'🔌 内部', modCls:'p', task:'Sentinel 告警', target:'Sentinel API', trig:'定时(5min)', st:'success', start:'15:35', dur:'6s', det:'2 活跃告警同步', rawResult: { summary: '2 活跃告警同步', duration: '6s' }, lifecycle: [
            { ts_ms:'15:35:00.000', event:'created', label:'📥 任务创建', detail:'account: 内部, trigger: 定时(5min)', color:'var(--blue)' },
            { ts_ms:'15:35:00.003', event:'dispatched', label:'🚀 任务派发', detail:'celery_task_id: a1b2c3d4e6', color:'var(--purple)' },
            { ts_ms:'15:35:00.800', event:'received', label:'🏃 Worker 接收', detail:'task: connector.sentinel_alert', color:'var(--teal)' },
            { ts_ms:'15:35:06.200', event:'completed', label:'✅ 执行完成', detail:'', color:'var(--teal)' },
          ] },
          { id:'#10339', mod:'☁️ AWS', modCls:'b', task:'生产-apse1 全量', target:'生产 / apse1', trig:'Cron', st:'running', start:'15:29', dur:'-', det:'运行中', rawResult: null, lifecycle: [
            { ts_ms:'15:29:00.000', event:'created', label:'📥 任务创建', detail:'account: 生产, region: apse1, mode: full', color:'var(--blue)' },
            { ts_ms:'15:29:00.010', event:'dispatched', label:'🚀 任务派发', detail:'celery_task_id: x9y8z7w6v5', color:'var(--purple)' },
            { ts_ms:'15:29:01.500', event:'received', label:'🏃 Worker 接收', detail:'task: resource_modules.vpc.celery_tasks.sync_vpc', color:'var(--teal)' },
            { ts_ms:'15:29:02.100', event:'running', label:'⚙️ 开始执行', detail:'full sync', color:'var(--blue)' },
          ] },
          { id:'#10338', mod:'☁️ AWS', modCls:'b', task:'生产-IAM 增量', target:'生产 / global', trig:'人工', st:'failed', start:'15:20', dur:'1m12s', err:'AssumeRole 凭据过期', det:'IAM 全量同步失败', rawResult: null, lifecycle: [
            { ts_ms:'15:20:00.000', event:'created', label:'📥 任务创建', detail:'account: 生产, region: global, mode: incremental', color:'var(--blue)' },
            { ts_ms:'15:20:00.008', event:'dispatched', label:'🚀 任务派发', detail:'celery_task_id: m3n4o5p6q7', color:'var(--purple)' },
            { ts_ms:'15:20:02.000', event:'received', label:'🏃 Worker 接收', detail:'task: resource_modules.iam.celery_tasks.sync_iam', color:'var(--teal)' },
            { ts_ms:'15:20:05.000', event:'retrying', label:'⚠️ 自动重试 (attempt 1)', detail:'ConnectionError: AssumeRole failed', color:'var(--orange)' },
            { ts_ms:'15:21:05.500', event:'retrying', label:'⚠️ 自动重试 (attempt 2)', detail:'ConnectionError: AssumeRole failed', color:'var(--orange)' },
            { ts_ms:'15:21:12.000', event:'failed', label:'❌ 执行失败', detail:'AssumeRole 凭据过期', color:'#c0392b' },
          ] },
        ]
        this.totalRecords = 5
      } finally {
        this.loading = false
      }
    },
    statusClass(st) {
      return { success: 'sb-o', failed: 'sb-f', partial: 'sb-w', running: 'sb-w' }[st] || 'sb-s'
    },
    statusLabel(st) {
      return { success: '✅ 成功', failed: '❌ 失败', partial: '⚠️ 部分失败', running: '⏳ 运行中' }[st] || st
    },
    scopeCls(scope) {
      return { region: 'b', group: 'g', resource: 'o', relation: 'p', test: 'g' }[scope] || 'p'
    },
  },
}
</script>

<style scoped>
.fl { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; align-items: center; }
.fl-s { padding: 4px 10px; border: 1px solid var(--border); border-radius: 5px; font-size: 11px; background: var(--card); }
.fl-inp { padding: 4px 10px; border: 1px solid var(--border); border-radius: 5px; font-size: 11px; background: var(--card); min-width: 160px; }
.tw { overflow-x: auto; border: 1px solid var(--border); border-radius: var(--rs); }
table { width: 100%; border-collapse: collapse; font-size: 11px; }
th, td { padding: 7px 9px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
th { background: var(--bg); font-size: 9px; font-weight: 600; color: var(--t2); text-transform: uppercase; letter-spacing: .3px; }
.ex-tr { cursor: pointer; }
.ex-tr .ex-ar { font-size: 8px; transition: transform .15s; display: inline-block; margin-right: 4px; color: var(--t2); }
.ex-tr.op .ex-ar { transform: rotate(90deg); }
.ex-det { display: none; }
.ex-det.op { display: table-row; }
.ex-det-in { padding: 12px 16px; font-size: 12px; line-height: 1.7; background: var(--bg); }
.sb { font-size: 9px; padding: 1px 7px; border-radius: 5px; font-weight: 600; display: inline-block; }
.sb-o { background: var(--tl); color: #1a7a6e; }
.sb-f { background: var(--cl); color: #c0392b; }
.sb-w { background: var(--al); color: #a67c00; }
.tag { display: inline-block; font-size: 9px; padding: 1px 8px; border-radius: 4px; font-weight: 500; }
.tag.b { background: var(--bl); color: var(--blue); }
.tag.p { background: var(--pl); color: var(--purple); }
.tag.o { background: var(--ol); color: var(--orange); }
.tag.g { background: var(--tl); color: var(--teal); }
.btn-t { font-size: 9px; padding: 3px 10px; border-radius: 4px; font-weight: 600; border: none; cursor: pointer; }
.btn-3 { background: var(--border); color: var(--text); }
.empty-hint { font-size: 11px; color: var(--t2); padding: 8px 0; }

/* ── Dropdown menu ── */
.op-wrap { position: relative; display: inline-block; }
.op-menu { position: absolute; top: 100%; right: 0; margin-top: 2px; background: var(--card); border: 1px solid var(--border); border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); z-index: 100; min-width: 80px; }
.op-item { padding: 5px 12px; font-size: 10px; cursor: pointer; white-space: nowrap; color: var(--text); }
.op-item:hover { background: var(--bg); color: var(--blue); }

/* ── Lifecycle timeline ── */
.lc-timeline { margin-bottom: 4px; }
.lc-title { font-size: 10px; font-weight: 600; color: var(--t2); text-transform: uppercase; letter-spacing: .3px; margin-bottom: 8px; }
.lc-steps { position: relative; padding-left: 16px; }
.lc-step { position: relative; padding-bottom: 10px; display: flex; align-items: flex-start; }
.lc-step:last-child { padding-bottom: 0; }
.lc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; position: relative; z-index: 1; }
.lc-line { position: absolute; left: 3px; top: 11px; bottom: -1px; width: 2px; background: var(--border); }
.lc-content { margin-left: 10px; font-size: 11px; line-height: 1.5; }
.lc-label { font-weight: 500; color: var(--text); }
.lc-ts { font-family: 'SF Mono', monospace; font-size: 9px; color: var(--t2); margin-left: 6px; }
.lc-detail { display: block; font-size: 10px; color: var(--t2); margin-top: 1px; }

/* ── Log panel ── */
.log-content { font-size: 11px; color: var(--text); line-height: 1.6; white-space: pre-wrap; word-break: break-all; }
.log-lines { font-size: 10px; font-family: 'SF Mono', monospace; line-height: 1.8; }
.log-line { display: flex; gap: 8px; }
.log-ts { color: var(--t2); flex-shrink: 0; min-width: 60px; }
.log-msg { color: var(--text); }

/* ── Result panel ── */
.result-card { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; }
.result-summary { font-size: 12px; font-weight: 500; color: var(--text); margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.result-fields { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 8px; }
.result-field { display: flex; flex-direction: column; gap: 2px; }
.rf-label { font-size: 9px; font-weight: 600; color: var(--t2); text-transform: uppercase; letter-spacing: .3px; }
.rf-value { font-size: 11px; font-weight: 500; color: var(--text); }
.result-artifact { margin-top: 6px; padding-top: 8px; border-top: 1px solid var(--border); }
.artifact-row { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.artifact-name { font-family: 'SF Mono', monospace; font-size: 10px; color: var(--text); }
.result-chips { display: flex; gap: 4px; }
.chip { font-size: 9px; padding: 1px 6px; border-radius: 3px; font-weight: 600; font-family: 'SF Mono', monospace; }
.chip-add { background: var(--tl); color: #1a7a6e; }
.chip-upd { background: var(--al); color: #a67c00; }
.chip-del { background: var(--cl); color: #c0392b; }
.chip-unch { background: var(--border); color: var(--t2); }

/* ── File preview modal ── */
.preview-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.preview-modal { background: var(--card); border: 1px solid var(--border); border-radius: 8px; width: 70vw; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; }
.preview-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid var(--border); }
.preview-title { font-size: 12px; font-weight: 600; color: var(--text); }
.preview-close { background: none; border: none; font-size: 14px; cursor: pointer; color: var(--t2); padding: 2px 6px; border-radius: 4px; }
.preview-close:hover { background: var(--border); }
.preview-body { flex: 1; overflow: auto; padding: 12px 16px; font-size: 10px; font-family: 'SF Mono', monospace; line-height: 1.6; margin: 0; white-space: pre-wrap; word-break: break-all; }
</style>
