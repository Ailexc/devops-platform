<template>
  <div class="db">
    <!-- Loading / Error -->
    <div v-if="loading" class="card" style="text-align:center;padding:40px;color:var(--t2)">
      <div class="loading-spinner"></div>
      <div style="margin-top:12px;font-size:13px">正在加载大盘数据...</div>
    </div>
    <div v-else-if="loadError" class="card error-banner">
      <span class="error-icon">⚠️</span>
      <div>
        <div style="font-size:12px;color:var(--coral);font-weight:600">{{ loadError }}</div>
        <div style="font-size:10px;color:var(--t2);margin-top:2px">当前展示本地演示数据</div>
      </div>
    </div>

    <!-- Auto-refresh indicator -->
    <div class="refresh-bar" v-if="!loading">
      <span class="refresh-dot" :class="{ active: refreshPulse }"></span>
      <span class="refresh-text">实时监控中</span>
      <span class="refresh-time">上次刷新: {{ lastRefreshTime }}</span>
    </div>

    <!-- ═══ 关键指标卡片 ═══ -->
    <div class="stats-grid">
      <div v-for="(s, i) in stats" :key="s.label" class="stat-card" :class="'stat-' + s.theme" :style="{ animationDelay: i * 60 + 'ms' }">
        <div class="stat-icon-wrap" :class="'bg-' + s.theme">
          <span class="stat-icon">{{ s.icon }}</span>
        </div>
        <div class="stat-body">
          <div class="stat-value" :class="'cl-' + s.theme">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
        <div v-if="s.trend" class="stat-trend" :class="s.trendDir === 'up' ? 'trend-up' : s.trendDir === 'down' ? 'trend-down' : 'trend-flat'">
          {{ s.trendDir === 'up' ? '↑' : s.trendDir === 'down' ? '↓' : '→' }} {{ s.trend }}
        </div>
      </div>
    </div>

      <!-- 7 天趋势 + 模块健康度 -->
    <div class="row-2">
      <!-- 7 天趋势图 -->
      <div class="card trend-card">
        <div class="card-header">
          <div class="card-title">📊 7 天任务趋势</div>
          <div class="card-badge badge-blue">按天</div>
        </div>
        <div class="trend-chart">
          <svg :viewBox="'0 0 ' + trendChartWidth + ' ' + trendChartHeight" class="trend-svg" preserveAspectRatio="none">
            <!-- Grid lines -->
            <line v-for="y in trendGridY" :key="'g'+y" :x1="0" :y1="y" :x2="trendChartWidth" :y2="y" class="grid-line" />
            <!-- Success area fill -->
            <path :d="trendSuccessArea" class="area-success" />
            <!-- Failed area fill -->
            <path :d="trendFailedArea" class="area-failed" />
            <!-- Success line -->
            <polyline :points="trendSuccessPoints" class="line-success" />
            <!-- Failed line -->
            <polyline :points="trendFailedPoints" class="line-failed" />
          </svg>
          <div class="trend-labels">
            <span v-for="h in trendLabels" :key="h">{{ h }}</span>
          </div>
        </div>
        <div class="trend-legend">
          <span class="legend-item"><span class="legend-dot lg-success"></span>成功</span>
          <span class="legend-item"><span class="legend-dot lg-failed"></span>失败</span>
          <span class="legend-item trend-summary">
            总计 <strong>{{ trendTotal }}</strong> 次执行 · 成功率 <strong style="color:var(--teal)">{{ trendSuccessRate }}%</strong>
          </span>
        </div>
      </div>

      <!-- 模块健康度 (环形) -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">💚 模块健康度</div>
          <div class="card-badge badge-green">今日</div>
        </div>
        <div class="health-rings">
          <div v-for="m in modules" :key="m.name" class="ring-item">
            <div class="ring-wrap">
              <svg viewBox="0 0 80 80" class="ring-svg">
                <circle cx="40" cy="40" r="34" class="ring-bg" />
                <circle cx="40" cy="40" r="34" class="ring-fg" :class="'ring-' + m.theme" :stroke-dasharray="2 * Math.PI * 34" :stroke-dashoffset="2 * Math.PI * 34 * (1 - m.rateNum / 100)" />
              </svg>
              <div class="ring-center">
                <div class="ring-pct" :class="'cl-' + m.theme">{{ m.rate }}</div>
              </div>
            </div>
            <div class="ring-info">
              <div class="ring-name">{{ m.icon }} {{ m.name }}</div>
              <div class="ring-detail">
                <span class="ring-ok">{{ m.total - m.failed }} 成功</span>
                <span v-if="m.failed > 0" class="ring-err">{{ m.failed }} 失败</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 任务健康排行 + 当前执行中 ═══ -->
    <div class="row-2">
      <!-- 任务健康度排行 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🏥 任务健康度排行</div>
          <div class="card-badge badge-yellow">近 3 天</div>
        </div>
        <div class="rank-cols">
          <div class="rank-col">
            <div class="rank-col-title" style="color:var(--coral)">❌ 失败 TOP 模块</div>
            <div v-if="(healthRanking.top_failed_modules || []).length" class="rank-list">
              <div v-for="(m, i) in healthRanking.top_failed_modules" :key="i" class="rank-row">
                <span class="rank-idx">{{ i + 1 }}</span>
                <span class="rank-name">{{ m.module }}</span>
                <span class="rank-val">{{ m.count }} 次失败</span>
              </div>
            </div>
            <div v-else class="empty-hint">近 3 天无失败任务 ✅</div>
          </div>
          <div class="rank-col">
            <div class="rank-col-title" style="color:var(--orange)">⏱️ 耗时 TOP 任务</div>
            <div v-if="(healthRanking.top_duration || []).length" class="rank-list">
              <div v-for="(t, i) in healthRanking.top_duration" :key="i" class="rank-row">
                <span class="rank-idx">{{ i + 1 }}</span>
                <span class="rank-name" :title="t.task">{{ t.task }}</span>
                <span class="rank-val">{{ t.duration }}</span>
              </div>
            </div>
            <div v-else class="empty-hint">暂无耗时数据</div>
          </div>
        </div>
      </div>

      <!-- 当前执行中 + 锁 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">⚡ 当前执行中</div>
          <div class="card-badge badge-green">{{ (currentRunning.running || []).length }} 个任务 · {{ (currentRunning.locks || []).length }} 把锁</div>
        </div>
        <div v-if="(currentRunning.running || []).length" class="running-list">
          <div v-for="(r, i) in currentRunning.running" :key="i" class="running-row" @click="goHistory(r)">
            <span class="running-dot"></span>
            <span class="running-name">{{ r.task }}</span>
            <span class="running-meta">{{ r.scope }} · {{ r.trigger }}</span>
            <span class="running-time">{{ r.start }}</span>
          </div>
        </div>
        <div v-else class="empty-hint">当前无执行中任务</div>
        <div v-if="(currentRunning.locks || []).length" class="lock-list">
          <div class="lock-title">🔒 并发锁</div>
          <div v-for="(l, i) in currentRunning.locks" :key="i" class="lock-row">
            <span class="lock-id">{{ l.lock_id }}</span>
            <span class="lock-target">{{ l.account }}/{{ l.region }} · {{ l.scope }} {{ l.target }}</span>
            <span class="lock-cnt">{{ (l.resource_keys || []).length }} 资源</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Worker 状态 + 资源新鲜度 + 资源分布 ═══ -->
    <div class="row-3">
      <!-- Worker 状态 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">⚙️ Worker 状态</div>
          <div class="card-badge badge-green">{{ onlineWorkers }}/{{ (workers || []).length }} 在线</div>
        </div>
        <div v-for="w in workers" :key="w.name" class="worker-row">
          <div class="worker-left">
            <span class="worker-dot" :class="w.status === 'online' ? 'dot-online' : 'dot-offline'"></span>
            <div class="worker-meta">
              <div class="worker-name">{{ w.name }}</div>
              <div class="worker-uptime">运行 {{ w.uptime }}</div>
            </div>
          </div>
          <div class="worker-right">
            <div class="worker-tasks">{{ w.tasks }} <span class="worker-unit">任务</span></div>
            <div class="worker-bar-wrap">
              <div class="worker-bar" :style="{ width: w.loadPct + '%', background: w.status === 'online' ? 'linear-gradient(90deg,var(--teal),var(--blue))' : 'var(--coral)' }"></div>
            </div>
          </div>
        </div>
        <!-- 整体负载 -->
        <div class="load-section">
          <div class="load-header">
            <span>整体负载</span>
            <span class="load-value" :class="loadLevel">{{ overallLoad }}</span>
          </div>
          <div class="load-bar-outer">
            <div class="load-bar-inner" :style="{ width: overallLoad, background: loadGradient }"></div>
          </div>
        </div>
      </div>

      <!-- 数据新鲜度 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🕐 数据新鲜度</div>
          <div class="card-badge">距上次同步</div>
        </div>
        <div class="freshness-list">
          <div v-for="(v, k) in freshness" :key="k" class="fresh-item">
            <div class="fresh-left">
              <span class="fresh-dot" :class="'fresh-' + v.level"></span>
              <span class="fresh-name">{{ k }}</span>
            </div>
            <div class="fresh-right">
              <span class="fresh-time" :class="'cl-' + v.level">{{ v.time }}</span>
              <span class="fresh-label">{{ v.levelLabel }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 资源分布 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">📦 资源分布</div>
          <div class="card-badge">CMDB</div>
        </div>
        <div class="resource-list">
          <div v-for="r in resourceBreakdown" :key="r.name" class="res-item">
            <div class="res-left">
              <span class="res-icon">{{ r.icon }}</span>
              <span class="res-name">{{ r.name }}</span>
            </div>
            <div class="res-right">
              <span class="res-count">{{ (r.count || 0).toLocaleString() }}</span>
              <span class="res-trend" :class="r.trend !== '0' ? 'trend-up' : ''">{{ r.trend !== '0' ? r.trend : '—' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 最近事件 ═══ -->
    <div class="card events-card">
      <div class="card-header">
        <div class="card-title">🔔 最近事件</div>
          <div class="card-badge badge-yellow">{{ (recentEvents || []).length }} 条</div>
      </div>
      <div class="events-list">
        <div v-for="(e, i) in recentEvents" :key="i" class="event-row" :class="'event-' + e.level">
          <span class="event-level-icon">{{ eventIcon(e.level) }}</span>
          <span class="event-time">{{ e.time }}</span>
          <span class="event-source">{{ e.source }}</span>
          <span class="event-msg">{{ e.message }}</span>
          <span class="event-id">{{ e.task_id }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  fetchDashboardStats, fetchWorkers, fetchResourceHealth,
  fetchTaskTrend, fetchRecentEvents, fetchResourceBreakdown,
  fetchHealthRanking, fetchCurrentRunning,
} from '../api/index.js'

const moduleIconMap = { 'AWS': '☁️', '内部系统': '🔌', '巡检': '🔍' }
const moduleThemeMap = { 'AWS': 'blue', '内部系统': 'purple', '巡检': 'orange' }

export default {
  name: 'MonitorDashboard',
  data() {
    return {
      loading: true,
      loadError: '',
      refreshPulse: false,
      lastRefreshTime: '—',
      refreshTimer: null,

      stats: [],
      modules: [],
      workers: [],
      overallLoad: '0%',
      freshness: {},
      trendData: [],
      recentEvents: [],
      resourceBreakdown: [],
      healthRanking: { top_failed_modules: [], top_duration: [] },
      currentRunning: { running: [], locks: [] },

      // chart dimensions
      trendChartWidth: 600,
      trendChartHeight: 120,
    }
  },
  computed: {
    onlineWorkers() {
      return (this.workers || []).filter(w => w.status === 'online').length
    },
    loadLevel() {
      const n = parseInt(this.overallLoad) || 0
      if (n >= 80) return 'load-high'
      if (n >= 50) return 'load-medium'
      return 'load-low'
    },
    loadGradient() {
      const n = parseInt(this.overallLoad) || 0
      if (n >= 80) return 'linear-gradient(90deg,var(--orange),var(--coral))'
      return 'linear-gradient(90deg,var(--teal),var(--blue))'
    },
    trendMax() {
      return Math.max(...this.trendData.map(d => d.total), 1)
    },
    trendGridY() {
      const h = this.trendChartHeight
      return [h * 0.25, h * 0.5, h * 0.75]
    },
    trendSuccessPoints() {
      return this.trendData.map((d, i) => {
        const x = (i / (this.trendData.length - 1 || 1)) * this.trendChartWidth
        const y = this.trendChartHeight - (d.success / this.trendMax) * (this.trendChartHeight * 0.85)
        return `${x},${y}`
      }).join(' ')
    },
    trendFailedPoints() {
      return this.trendData.map((d, i) => {
        const x = (i / (this.trendData.length - 1 || 1)) * this.trendChartWidth
        const y = this.trendChartHeight - (d.failed / this.trendMax) * (this.trendChartHeight * 0.85)
        return `${x},${y}`
      }).join(' ')
    },
    trendSuccessArea() {
      const pts = this.trendData.map((d, i) => {
        const x = (i / (this.trendData.length - 1 || 1)) * this.trendChartWidth
        const y = this.trendChartHeight - (d.success / this.trendMax) * (this.trendChartHeight * 0.85)
        return `${x},${y}`
      })
      if (!pts.length) return ''
      const bottom = this.trendChartHeight
      return `M0,${bottom} ` + pts.map(p => `L${p}`).join(' ') + ` L${this.trendChartWidth},${bottom} Z`
    },
    trendFailedArea() {
      const pts = this.trendData.map((d, i) => {
        const x = (i / (this.trendData.length - 1 || 1)) * this.trendChartWidth
        const y = this.trendChartHeight - (d.failed / this.trendMax) * (this.trendChartHeight * 0.85)
        return `${x},${y}`
      })
      if (!pts.length) return ''
      const bottom = this.trendChartHeight
      return `M0,${bottom} ` + pts.map(p => `L${p}`).join(' ') + ` L${this.trendChartWidth},${bottom} Z`
    },
    trendLabels() {
      // 7 天趋势：显示全部日期
      return this.trendData.map(d => d.date)
    },
    trendTotal() {
      return this.trendData.reduce((s, d) => s + d.total, 0)
    },
    trendSuccessRate() {
      const total = this.trendData.reduce((s, d) => s + d.total, 0)
      const success = this.trendData.reduce((s, d) => s + d.success, 0)
      return total ? ((success / total) * 100).toFixed(1) : '—'
    },
  },
  async mounted() {
    await this.loadData()
    // 60 秒自动刷新
    this.refreshTimer = setInterval(() => this.loadData(), 60000)
  },
  beforeUnmount() {
    if (this.refreshTimer) clearInterval(this.refreshTimer)
  },
  methods: {
    eventIcon(level) {
      const map = { error: '🔴', warning: '🟡', success: '🟢', info: '🔵' }
      return map[level] || '⚪'
    },
    goHistory(r) {
      const id = String(r.id).replace('#', '')
      this.$router.push(`/history/${id}`)
    },
    async loadData() {
      this.refreshPulse = true
      try {
        const [statsRes, workersRes, healthRes, trendRes, eventsRes, resRes, rankRes, currentRes] = await Promise.all([
          fetchDashboardStats(),
          fetchWorkers(),
          fetchResourceHealth(),
          fetchTaskTrend(),
          fetchRecentEvents(),
          fetchResourceBreakdown(),
          fetchHealthRanking(),
          fetchCurrentRunning(),
        ])
        this.applyStats(statsRes.data)
        this.applyWorkers(workersRes.data)
        this.applyHealth(healthRes.data)
        this.trendData = trendRes.data
        // Normalize: Go backend wraps in {events:[...]}, Python returns [...] directly
        const evData = eventsRes.data
        this.recentEvents = Array.isArray(evData) ? evData : (evData.events || [])
        // Normalize: Go backend wraps in {breakdown:[...]}, Python returns [...] directly
        const brData = resRes.data
        this.resourceBreakdown = Array.isArray(brData) ? brData : (brData.breakdown || [])
        this.healthRanking = rankRes.data
        // Normalize: ensure running/locks are always arrays (not null)
        const curData = currentRes.data || {}
        this.currentRunning = {
          running: curData.running || [],
          locks: curData.locks || [],
        }
        this.loadError = ''
      } catch (e) {
        console.error('加载大盘数据失败:', e)
        this.loadError = '加载数据失败，请检查后端服务是否可用'
        this.applyFallback()
      } finally {
        this.loading = false
        this.lastRefreshTime = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        setTimeout(() => { this.refreshPulse = false }, 800)
      }
    },
    applyStats(d) {
      this.stats = [
        { icon: '🔄', value: String(d.today_tasks ?? 0), label: '今日任务执行', theme: 'blue', trend: '', trendDir: 'flat' },
        { icon: '✅', value: d.success_rate_24h ?? '—', label: '今日成功率', theme: 'green', trend: '', trendDir: 'flat' },
        { icon: '📈', value: d.success_rate_7d ?? '—', label: '近 7 天成功率', theme: 'teal', trend: '', trendDir: 'flat' },
        { icon: '📦', value: String(d.cumulative_synced ?? 0), label: '30 天累计同步量', theme: 'blue', trend: '', trendDir: 'flat' },
        { icon: '⚡', value: String(d.running_now ?? 0), label: '当前执行中', theme: 'orange', trend: '', trendDir: 'flat' },
        { icon: '❌', value: String(d.pending_errors ?? 0), label: '今日待处理异常', theme: 'red', trend: '', trendDir: 'flat' },
        { icon: '📊', value: String(d.weekly_total ?? 0), label: '近 7 天任务总数', theme: 'purple', trend: '', trendDir: 'flat' },
        { icon: '🗄️', value: d.total_cmdb_resources ?? '—', label: 'CMDB 总资源数', theme: 'slate', trend: '', trendDir: 'flat' },
      ]
    },
    applyWorkers(d) {
      this.workers = (d.workers || []).map(w => ({
        ...w,
        loadPct: Math.round((w.tasks / 200) * 100),
      }))
      this.overallLoad = d.load || '0%'
    },
    applyHealth(d) {
      this.modules = (d.modules || []).map(m => ({
        icon: moduleIconMap[m.name] || '📦',
        name: m.name,
        theme: moduleThemeMap[m.name] || 'blue',
        rate: m.rate,
        rateNum: parseFloat(m.rate) || 0,
        failed: m.failed,
        total: m.total,
        synced: m.synced ?? 0,
      }))
      const f = d.freshness || {}
      this.freshness = Object.fromEntries(
        Object.entries(f).map(([k, t]) => {
          const num = parseInt(t) || 0
          let level = 'ok'
          let levelLabel = '正常'
          if (t.includes('h') && num > 1) { level = 'warn'; levelLabel = '需关注' }
          if (t.includes('h') && num > 12) { level = 'stale'; levelLabel = '较久' }
          return [k, { time: t, color: 'var(--teal)', level, levelLabel }]
        })
      )
    },
    applyFallback() {
      this.applyStats({
        today_tasks: 342, success_rate_24h: '98.7%', success_rate_7d: '97.4%',
        cumulative_synced: 8612, running_now: 0, pending_errors: 7,
        weekly_total: 334, total_cmdb_resources: '2.4M',
      })
      this.applyWorkers({
        workers: [
          { name: 'worker-aws', tasks: 186, uptime: '6h12m', status: 'online' },
          { name: 'worker-connector', tasks: 94, uptime: '6h12m', status: 'online' },
          { name: 'worker-inspection', tasks: 62, uptime: '6h12m', status: 'online' },
        ],
        load: '52%',
      })
      this.applyHealth({
        modules: [
          { name: 'AWS', rate: '99.1%', failed: 12, total: 186 },
          { name: '内部系统', rate: '97.9%', failed: 2, total: 94 },
          { name: '巡检', rate: '95.2%', failed: 3, total: 62 },
        ],
        freshness: { 'AWS': '2m', 'Lark': '12m', 'Jira': '8m', '钉钉': '3m', '巡检': '22h' },
      })
      this.trendData = [
        {date:'07-27',success:42,failed:4,total:46},{date:'07-28',success:55,failed:3,total:58},
        {date:'07-29',success:49,failed:3,total:52},{date:'07-30',success:56,failed:5,total:61},
        {date:'07-31',success:42,failed:2,total:44},{date:'08-01',success:54,failed:3,total:57},
        {date:'08-02',success:11,failed:1,total:12},
      ]
      this.healthRanking = {
        top_failed_modules: [{ module: 'AWS', count: 3 }],
        top_duration: [
          { task: '生产/ap-northeast-1 区域同步', target: '生产 / ap-northeast-1', duration: '2m34s' },
          { task: '生产/eu-west-1 区域同步', target: '生产 / eu-west-1', duration: '3m12s' },
        ],
      }
      this.currentRunning = { running: [], locks: [] }
      this.recentEvents = [
        { time: '15:35', level: 'error', source: 'AWS IAM', message: 'AssumeRole 凭据过期，IAM 同步失败', task_id: '#10338' },
        { time: '15:29', level: 'warning', source: 'AWS EC2', message: '生产-apse1 同步正在运行中，已耗时 6m+', task_id: '#10339' },
        { time: '15:26', level: 'success', source: 'AWS EC2', message: '生产-apne1 全量同步完成 (2m34s)', task_id: '#10342' },
      ]
      this.resourceBreakdown = [
        { name: 'EC2 实例', count: 1245, icon: '🖥️', trend: '+12' },
        { name: 'RDS 数据库', count: 86, icon: '🗄️', trend: '+2' },
        { name: 'VPC 网络', count: 45, icon: '🌐', trend: '0' },
      ]
    },
  },
}
</script>

<style scoped>
/* ── Health ranking & running ── */
.rank-cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:760px){.rank-cols{grid-template-columns:1fr}}
.rank-col-title{font-size:10px;font-weight:700;margin-bottom:8px}
.rank-list{display:flex;flex-direction:column;gap:4px}
.rank-row{display:flex;align-items:center;gap:8px;font-size:11px;padding:5px 8px;background:#f8f9fa;border-radius:6px}
.rank-idx{width:16px;height:16px;border-radius:4px;background:#e9ecef;color:#6c757d;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.rank-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500}
.rank-val{font-size:10px;color:#6c757d;font-family:'SF Mono',monospace;flex-shrink:0}
.running-list{display:flex;flex-direction:column;gap:5px}
.running-row{display:flex;align-items:center;gap:8px;font-size:11px;padding:6px 8px;background:#f8f9fa;border-radius:6px;cursor:pointer;transition:border-color .15s}
.running-row:hover{border:1px solid var(--blue)}
.running-dot{width:7px;height:7px;border-radius:50%;background:var(--teal);animation:pulse 1.2s infinite;flex-shrink:0}
.running-name{font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.running-meta{font-size:9px;color:#6c757d;flex-shrink:0}
.running-time{font-size:9px;color:#6c757d;font-family:'SF Mono',monospace;flex-shrink:0}
.lock-list{margin-top:12px;border-top:1px dashed #e9ecef;padding-top:10px}
.lock-title{font-size:10px;font-weight:600;color:#6c757d;margin-bottom:6px}
.lock-row{display:flex;align-items:center;gap:8px;font-size:10px;padding:4px 6px;font-family:'SF Mono',monospace}
.lock-id{color:var(--orange);font-weight:600}
.lock-target{flex:1;color:#495057}
.lock-cnt{color:#6c757d}
.empty-hint{font-size:11px;color:#adb5bd;padding:6px 0}

/* ── Variables ── */
.db { --blue: #4361ee; --teal: #2ec4b6; --coral: #ff6b6b; --purple: #7c3aed; --orange: #f97316; --amber: #ffd166; }

/* ── Global card ── */
.card {
  background: #fff; border-radius: 12px; border: 1px solid #e9ecef;
  padding: 18px 20px; transition: box-shadow .2s, transform .15s;
}
.card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.06); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 13px; font-weight: 700; color: #1a1a2e; }
.card-badge { font-size: 10px; padding: 2px 10px; border-radius: 10px; font-weight: 600; background: #f0f2f5; color: #6c757d; }
.badge-blue { background: #eef1ff; color: var(--blue); }
.badge-green { background: #e6faf7; color: #1a7a6e; }
.badge-yellow { background: #fff8e0; color: #b8860b; }

/* ── Loading ── */
.loading-spinner {
  width: 28px; height: 28px; border: 3px solid #e9ecef; border-top-color: var(--blue);
  border-radius: 50%; animation: spin .8s linear infinite; margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-banner { display: flex; align-items: center; gap: 10px; padding: 14px 18px; border-color: rgba(255,107,107,.2); background: rgba(255,107,107,.04); }
.error-icon { font-size: 18px; }

/* ── Refresh bar ── */
.refresh-bar { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; font-size: 10px; color: var(--t2); }
.refresh-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--teal); }
.refresh-dot.active { animation: pulse 1s ease; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(46,196,182,.6)} 100%{box-shadow:0 0 0 8px rgba(46,196,182,0)} }
.refresh-text { font-weight: 600; color: var(--teal); }
.refresh-time { margin-left: auto; }

/* ═══ Stats Grid ═══ */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px;
}
@media (max-width: 960px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .stats-grid { grid-template-columns: 1fr; } }
.stat-card {
  background: #fff; border-radius: 12px; border: 1px solid #e9ecef;
  padding: 14px 16px; display: flex; align-items: center; gap: 12px;
  position: relative; overflow: hidden; animation: fadeUp .4s ease both;
  transition: transform .15s, box-shadow .2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,.07); }
@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.stat-icon-wrap {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-icon { font-size: 16px; }
.bg-blue { background: #eef1ff; }
.bg-green { background: #e6faf7; }
.bg-purple { background: #f0e8ff; }
.bg-orange { background: #fff3e6; }
.bg-red { background: #ffe8e8; }
.bg-teal { background: #e6faf7; }
.bg-slate { background: #f0f2f5; }

.stat-body { flex: 1; min-width: 0; }
.stat-value { font-size: 20px; font-weight: 800; letter-spacing: -.5px; line-height: 1.1; }
.stat-label { font-size: 10px; color: #6c757d; font-weight: 500; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cl-blue { color: var(--blue); }
.cl-green { color: var(--teal); }
.cl-purple { color: var(--purple); }
.cl-orange { color: var(--orange); }
.cl-red { color: var(--coral); }
.cl-teal { color: var(--teal); }
.cl-slate { color: #6c757d; }
.cl-ok { color: var(--teal); }
.cl-warn { color: var(--orange); }
.cl-stale { color: var(--coral); }

.stat-trend { font-size: 10px; font-weight: 600; position: absolute; top: 8px; right: 10px; }
.trend-up { color: var(--teal); }
.trend-down { color: var(--coral); }
.trend-flat { color: #6c757d; }

/* ═══ Row layouts ═══ */
.row-2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 10px; margin-bottom: 12px; }
.row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px; }
@media (max-width: 960px) { .row-2, .row-3 { grid-template-columns: 1fr; } }

/* ═══ Trend chart ═══ */
.trend-card { grid-column: 1 / -1; }
.trend-chart { position: relative; }
.trend-svg { width: 100%; height: 140px; }
.grid-line { stroke: #e9ecef; stroke-width: .5; }
.line-success { fill: none; stroke: var(--teal); stroke-width: 2; stroke-linejoin: round; }
.line-failed { fill: none; stroke: var(--coral); stroke-width: 2; stroke-linejoin: round; stroke-dasharray: 4,3; }
.area-success { fill: url(#grad-success); opacity: .15; }
.area-failed { fill: var(--coral); opacity: .08; }
.trend-labels {
  display: flex; justify-content: space-between; font-size: 9px; color: #6c757d; margin-top: 4px;
}
.trend-legend {
  display: flex; align-items: center; gap: 16px; margin-top: 8px; font-size: 11px; color: #6c757d;
}
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot { width: 8px; height: 3px; border-radius: 2px; }
.lg-success { background: var(--teal); }
.lg-failed { background: var(--coral); }
.trend-summary { margin-left: auto; }
.trend-summary strong { color: #1a1a2e; font-weight: 700; }

/* ═══ Health rings ═══ */
.health-rings { display: flex; flex-direction: column; gap: 16px; }
.ring-item { display: flex; align-items: center; gap: 14px; }
.ring-wrap { position: relative; width: 70px; height: 70px; flex-shrink: 0; }
.ring-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: #f0f2f5; stroke-width: 6; }
.ring-fg { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dashoffset 1s ease; }
.ring-blue { stroke: var(--blue); }
.ring-purple { stroke: var(--purple); }
.ring-orange { stroke: var(--orange); }
.ring-center { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.ring-pct { font-size: 13px; font-weight: 800; }
.ring-info { flex: 1; }
.ring-name { font-size: 12px; font-weight: 600; color: #1a1a2e; }
.ring-detail { font-size: 10px; color: #6c757d; margin-top: 2px; }
.ring-ok { color: var(--teal); }
.ring-err { color: var(--coral); margin-left: 6px; }

/* ═══ Worker status ═══ */
.worker-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid #f0f2f5;
}
.worker-row:last-of-type { border-bottom: none; }
.worker-left { display: flex; align-items: center; gap: 8px; }
.worker-dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-online { background: var(--teal); box-shadow: 0 0 6px rgba(46,196,182,.4); }
.dot-offline { background: var(--coral); }
.worker-meta {}
.worker-name { font-size: 12px; font-weight: 600; color: #1a1a2e; }
.worker-uptime { font-size: 9px; color: #6c757d; }
.worker-right { text-align: right; min-width: 80px; }
.worker-tasks { font-size: 14px; font-weight: 700; color: #1a1a2e; }
.worker-unit { font-size: 9px; font-weight: 400; color: #6c757d; }
.worker-bar-wrap { width: 80px; height: 3px; background: #f0f2f5; border-radius: 2px; margin-top: 4px; overflow: hidden; }
.worker-bar { height: 100%; border-radius: 2px; transition: width .6s ease; }

.load-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f2f5; }
.load-header { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #6c757d; margin-bottom: 6px; }
.load-value { font-weight: 700; font-size: 13px; }
.load-low { color: var(--teal); }
.load-medium { color: var(--orange); }
.load-high { color: var(--coral); }
.load-bar-outer { height: 6px; background: #f0f2f5; border-radius: 3px; overflow: hidden; }
.load-bar-inner { height: 100%; border-radius: 3px; transition: width .6s ease; }

/* ═══ Freshness ═══ */
.freshness-list { display: flex; flex-direction: column; gap: 0; }
.fresh-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid #f0f2f5;
}
.fresh-item:last-child { border-bottom: none; }
.fresh-left { display: flex; align-items: center; gap: 8px; }
.fresh-dot { width: 6px; height: 6px; border-radius: 50%; }
.fresh-ok { background: var(--teal); }
.fresh-warn { background: var(--orange); }
.fresh-stale { background: var(--coral); }
.fresh-name { font-size: 12px; font-weight: 500; color: #1a1a2e; }
.fresh-right { text-align: right; }
.fresh-time { font-size: 13px; font-weight: 700; }
.fresh-label { display: block; font-size: 9px; color: #6c757d; }

/* ═══ Resource breakdown ═══ */
.resource-list { display: flex; flex-direction: column; gap: 0; }
.res-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid #f0f2f5;
}
.res-item:last-child { border-bottom: none; }
.res-left { display: flex; align-items: center; gap: 8px; }
.res-icon { font-size: 14px; }
.res-name { font-size: 12px; font-weight: 500; color: #1a1a2e; }
.res-right { text-align: right; display: flex; align-items: center; gap: 8px; }
.res-count { font-size: 13px; font-weight: 700; color: #1a1a2e; }
.res-trend { font-size: 10px; font-weight: 600; }
.res-trend.trend-up { color: var(--teal); }

/* ═══ Events ═══ */
.events-card { margin-bottom: 12px; }
.events-list { display: flex; flex-direction: column; gap: 0; }
.event-row {
  display: grid; grid-template-columns: 20px 50px 80px 1fr auto;
  align-items: center; gap: 8px; padding: 8px 0;
  border-bottom: 1px solid #f0f2f5; font-size: 11px;
}
.event-row:last-child { border-bottom: none; }
.event-level-icon { font-size: 10px; }
.event-time { font-weight: 600; color: #6c757d; font-family: 'SF Mono', 'Cascadia Code', monospace; font-size: 10px; }
.event-source { font-weight: 600; color: #1a1a2e; }
.event-msg { color: #495057; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-id { font-size: 10px; color: #6c757d; font-family: 'SF Mono', 'Cascadia Code', monospace; }
.event-error .event-msg { color: var(--coral); }
.event-warning .event-msg { color: var(--orange); }
.event-success .event-msg { color: #495057; }
</style>
