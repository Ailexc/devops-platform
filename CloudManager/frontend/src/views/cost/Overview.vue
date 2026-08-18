<template>
  <div class="cost-page">
    <!-- 页面标题 -->
    <div class="page-header fade-in">
      <div class="header-content">
        <button class="back-btn" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"></path>
          </svg>
        </button>
        <div>
          <h1 class="page-title">💡 成本优化总览</h1>
          <p class="page-subtitle">多云资源优化机会一览 · 基于可配置规则引擎检测结果</p>
        </div>
      </div>
    </div>

    <!-- 数据权限说明 -->
    <div class="perm-card fade-in">
      <div class="perm-head">
        <div class="perm-head-left">
          <span class="perm-avatar">{{ (userStore.user?.display_name || userStore.user?.username || '?')[0] }}</span>
          <div>
            <div class="perm-user">{{ userStore.user?.display_name || userStore.user?.username }}</div>
            <div class="perm-sub">{{ roleText }} · {{ userStore.user?.department_name || '未分配部门' }}</div>
          </div>
        </div>
        <div class="perm-right">
          <span class="perm-scope" :class="isAdminScope ? 'scope-all' : 'scope-dept'">
            {{ isAdminScope ? '数据范围：全部' : '数据范围：本部门' }}
          </span>
        </div>
      </div>
      <a-collapse :bordered="false" class="perm-collapse">
        <a-collapse-panel key="1">
          <template #header>
            <span class="perm-collapse-title">📖 真实业务机制 & 本系统简化实现（点击展开）</span>
          </template>
          <div class="perm-body">
            <div class="perm-section">
              <div class="perm-heading">真实业务：权限中心 · 注册制 + 能力包</div>
              <div class="perm-text">
                企业一般会建设统一的「权限中心」：各系统把自己的能力（操作点 + 数据维度）注册进去，
                用户在权限中心申请对应的「能力包」（如成本分析-全量 / 部门级 / 只读），
                审批通过后即获得对应的操作权限与数据范围。本系统 Demo 暂未与权限中心打通，做了简化。
              </div>
              <div class="perm-table-wrap">
                <table class="perm-table">
                  <thead>
                    <tr><th>能力包</th><th>数据范围</th><th>可执行操作</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>成本分析-全量</td><td>全部云 / 账号 / 区域 / 部门 / 应用</td><td>查看 + 导出 + 执行检测 + 配置规则</td></tr>
                    <tr><td>成本分析-部门级</td><td>仅本部门组织树</td><td>查看 + 导出（限本部门）</td></tr>
                    <tr><td>成本分析-只读</td><td>仅本部门</td><td>仅查看</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="perm-section">
              <div class="perm-heading">本系统简化实现</div>
              <div class="perm-note">
                后端按当前用户强制过滤数据范围：<b>超级管理员（admin）→ 全部</b>；
                <b>其他用户 → 仅可见自己部门（user.department）</b> 的成本分摊数据（账单 / 分摊 / 明细 / 导出均受限）。
                可切换账号体验：用 <b>admin</b> 看全量，或用 <b>readonly</b>（研发组，密码 admin123）看仅研发组的数据。
              </div>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </div>

    <CostGlobalFilter />

    <a-spin :spinning="loading">
      <!-- 空态 -->
      <div v-if="!loading && overview && overview.stats.total === 0" class="empty-card fade-in">
        <div class="empty-icon">📊</div>
        <p class="empty-title">暂无优化建议数据</p>
        <p class="empty-desc">请前往「规则配置」页点击「立即检测」生成优化建议</p>
        <a-button type="primary" @click="$router.push('/cost/rules')">去规则配置</a-button>
      </div>

      <template v-else-if="overview">
        <!-- 统计卡 -->
        <div class="stats-row fade-in">
          <div class="stat-card">
            <div class="stat-label">⚠️ 待处理建议</div>
            <div class="stat-value red">{{ overview.stats.pending }}</div>
            <div class="stat-sub">共 {{ overview.stats.total }} 条建议</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">💰 预估月节省</div>
            <div class="stat-value green">¥{{ overview.stats.total_saving.toLocaleString() }}</div>
            <div class="stat-sub">优化后预计节省</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">🌐 覆盖云厂商</div>
            <div class="stat-value blue">{{ overview.stats.cloud_count }}</div>
            <div class="stat-sub">纳管云账号资源</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">✅ 已处理</div>
            <div class="stat-value purple">{{ overview.stats.resolved }}</div>
            <div class="stat-sub">历史已优化项</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">📈 环比节省</div>
            <div class="stat-value orange" style="font-size: 22px">{{ momSavingText }}</div>
            <div class="stat-sub">较上月新增节省</div>
          </div>
        </div>

        <!-- 图表区 -->
        <div class="charts-grid fade-in">
          <div class="chart-card">
            <div class="chart-title">🌐 按云厂商节省分布</div>
            <div class="chart-body" ref="cloudChartRef" style="height: 220px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">📦 按资源类型建议分布</div>
            <div class="chart-body" ref="typeChartRef" style="height: 220px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">📍 按区域成本分布</div>
            <div class="chart-body" ref="regionChartRef" style="height: 220px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">📈 近6月优化节省趋势</div>
            <div class="chart-body" ref="trendChartRef" style="height: 220px"></div>
          </div>
        </div>

        <!-- 成本分摊（账单视角） -->
        <div class="cost-split-grid fade-in">
          <div class="chart-card span-2">
            <div class="chart-title">💰 月度成本趋势</div>
            <div class="chart-body" ref="billTrendChartRef" style="height: 220px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">
              <span>🏢 部门分摊</span>
              <a class="detail-link" @click="goShare('department', '')">查看明细 →</a>
            </div>
            <div class="chart-body" ref="deptChartRef" style="height: 220px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">
              <span>📱 应用分摊</span>
              <a class="detail-link" @click="goShare('application', '')">查看明细 →</a>
            </div>
            <div class="chart-body" ref="appChartRef" style="height: 220px"></div>
          </div>
        </div>

        <!-- 建议明细 -->
        <div class="table-card fade-in">
          <div class="card-header">
            <h3 class="card-title">📋 优化建议明细</h3>
            <span class="card-hint">点击行查看详情 · 支持标记处理</span>
          </div>
          <a-table
            :data-source="overview.suggestions"
            :columns="sugColumns"
            :pagination="{ pageSize: 10, showSizeChanger: false }"
            size="middle"
            row-key="id"
            :loading="loading"
            @row-click="openSugDetail"
            :row-class-name="() => 'clickable-row'"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'cloud'">
                <span class="cloud-pill">{{ providerLabel(record.provider_type) }}</span>
              </template>
              <template v-if="column.key === 'severity'">
                <a-tag :color="sevColor(record.severity)">{{ sevLabel(record.severity) }}</a-tag>
              </template>
              <template v-if="column.key === 'type'">
                <a-tag>{{ typeLabel(record.suggestion_type) }}</a-tag>
              </template>
              <template v-if="column.key === 'saving'">
                <span v-if="record.estimated_saving > 0" class="saving-text">
                  ¥{{ Number(record.estimated_saving).toLocaleString() }}/月
                </span>
                <span v-else class="muted">-</span>
              </template>
              <template v-if="column.key === 'resolved'">
                <a-tag :color="record.is_resolved ? 'green' : 'orange'">
                  {{ record.is_resolved ? '已处理' : '待处理' }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </div>
      </template>
    </a-spin>

    <!-- 建议详情 -->
    <a-modal
      v-model:open="detailVisible"
      title="💡 优化建议详情"
      :footer="null"
      width="680px"
    >
      <template v-if="sugDetail">
        <div class="sug-detail-head">
          <div class="sug-title">{{ sugDetail.title }}</div>
          <div class="sug-desc">{{ sugDetail.description }}</div>
        </div>
        <a-descriptions :column="3" size="small" bordered style="margin-top: 16px">
          <a-descriptions-item label="所属云">{{ providerLabel(sugDetail.provider_type) }}</a-descriptions-item>
          <a-descriptions-item label="云账号">{{ sugDetail.account_name || '-' }}</a-descriptions-item>
          <a-descriptions-item label="区域">{{ sugDetail.region || '-' }}</a-descriptions-item>
          <a-descriptions-item label="资源名称">{{ sugDetail.resource_name || '-' }}</a-descriptions-item>
          <a-descriptions-item label="资源ID">{{ sugDetail.resource_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="命中规则">{{ sugDetail.rule_name || '-' }}</a-descriptions-item>
          <a-descriptions-item label="建议类型">{{ typeLabel(sugDetail.suggestion_type) }}</a-descriptions-item>
          <a-descriptions-item label="优先级">{{ sevLabel(sugDetail.severity) }}</a-descriptions-item>
          <a-descriptions-item label="预估月节省">
            <span class="saving-text">¥{{ Number(sugDetail.estimated_saving).toLocaleString() }}</span>
          </a-descriptions-item>
        </a-descriptions>
        <div class="detail-actions">
          <a-button v-if="!sugDetail.is_resolved" type="primary" @click="resolveSug(sugDetail)">
            ✓ 标记为已处理
          </a-button>
          <a-tag v-else color="green" style="font-size: 13px; padding: 6px 14px">✅ 已处理</a-tag>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import { costApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { useCostFilterStore } from '@/stores/costFilter'
import CostGlobalFilter from '@/components/cost/CostGlobalFilter.vue'
import type { CostOverview, OptimizationSuggestion } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const costFilterStore = useCostFilterStore()

const isAdminScope = computed(() => {
  const u = userStore.user
  return !!u && (u.username === 'admin' || u.roles?.some((r: any) => r.code === 'super_admin'))
})
const roleText = computed(() => {
  const u = userStore.user
  if (!u) return ''
  if (u.username === 'admin' || u.roles?.some((r: any) => r.code === 'super_admin')) return '超级管理员'
  const names = (u.roles || []).map((r: any) => r.name).filter(Boolean)
  return names.length ? names.join(' / ') : '普通用户'
})

function goShare(type: string, name: string) {
  router.push({ path: '/cost/share', query: { type, name } })
}

const loading = ref(false)
const overview = ref<CostOverview | null>(null)
const detailVisible = ref(false)
const sugDetail = ref<OptimizationSuggestion | null>(null)

const cloudChartRef = ref<HTMLElement>()
const typeChartRef = ref<HTMLElement>()
const regionChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()
const billTrendChartRef = ref<HTMLElement>()
const deptChartRef = ref<HTMLElement>()
const appChartRef = ref<HTMLElement>()
const charts: echarts.ECharts[] = []

// 成本分摊数据
const billTrend = ref<any[]>([])
const deptData = ref<any[]>([])
const appData = ref<any[]>([])
const splitCharts: echarts.ECharts[] = []

const COLORS = ['#7C3AED', '#0EA5E9', '#F97316', '#10B981', '#EF4444', '#F59E0B', '#8B5CF6']

const providerMap: Record<string, string> = { aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', mock: 'Mock' }
const typeMap: Record<string, string> = {
  idle: '闲置资源', downsize: '建议降配', unused: '未使用', budget: '预算告警',
  trend: '趋势异常', reserved: '付费优化', storage: '存储优化',
}
function providerLabel(p: string) { return providerMap[p] || p || '全部' }
function typeLabel(t: string) { return typeMap[t] || t }
function sevLabel(s: string) { return { high: '高', medium: '中', low: '低' }[s] || s }
function sevColor(s: string) { return { high: 'red', medium: 'orange', low: 'green' }[s] || 'default' }

const sugColumns = [
  { title: '云', key: 'cloud', dataIndex: 'provider_type', width: 90 },
  { title: '优先级', key: 'severity', dataIndex: 'severity', width: 80 },
  { title: '类型', key: 'type', dataIndex: 'suggestion_type', width: 100 },
  { title: '建议内容', key: 'title', dataIndex: 'title', ellipsis: true },
  { title: '关联资源', key: 'resource_name', dataIndex: 'resource_name', width: 150, ellipsis: true },
  { title: '预估月节省', key: 'saving', dataIndex: 'estimated_saving', width: 130 },
  { title: '状态', key: 'resolved', dataIndex: 'is_resolved', width: 90 },
]

const momSavingText = computed(() => {
  const trend = overview.value?.trend || []
  if (trend.length < 2) return '--'
  const cur = trend[trend.length - 1]?.saving || 0
  const prev = trend[trend.length - 2]?.saving || 0
  if (prev <= 0) return '--'
  const mom = Math.round((cur - prev) / prev * 100)
  return `${mom >= 0 ? '+' : ''}${mom}%`
})

function renderCharts() {
  if (!overview.value) return
  const ov = overview.value
  // 清理旧实例
  charts.forEach(c => c.dispose())
  charts.length = 0

  // 1. 按云节省
  if (cloudChartRef.value) {
    const chart = echarts.init(cloudChartRef.value)
    charts.push(chart)
    const data = ov.by_cloud.map((c, i) => ({
      name: providerLabel(c.provider_type),
      value: Number(c.total),
      itemStyle: { color: COLORS[i % COLORS.length] },
    }))
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      yAxis: { type: 'category', data: data.map(d => d.name), axisLine: { show: false }, axisLabel: { color: '#6B7280' } },
      series: [{
        type: 'bar', data, barWidth: 18,
        label: { show: true, position: 'right', formatter: (p: any) => '¥' + p.value.toLocaleString(), color: '#6B7280' },
      }],
    })
  }

  // 2. 按类型环形
  if (typeChartRef.value) {
    const chart = echarts.init(typeChartRef.value)
    charts.push(chart)
    const data = ov.by_type.map((t, i) => ({
      name: typeLabel(t.suggestion_type), value: t.cnt,
      itemStyle: { color: COLORS[i % COLORS.length] },
    }))
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
      legend: { bottom: 0, textStyle: { color: '#6B7280' } },
      series: [{
        type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data,
      }],
    })
  }

  // 3. 按区域柱状
  if (regionChartRef.value) {
    const chart = echarts.init(regionChartRef.value)
    charts.push(chart)
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 20, top: 20, bottom: 10, containLabel: true },
      xAxis: {
        type: 'category',
        data: ov.by_region.map(r => r.region || '-'),
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisLabel: { color: '#6B7280' },
      },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      series: [{
        type: 'bar',
        data: ov.by_region.map((r, i) => ({
          value: Number(r.total),
          itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [6, 6, 0, 0] },
        })),
        barWidth: 32,
        label: { show: true, position: 'top', formatter: (p: any) => '¥' + p.value.toLocaleString(), color: '#9CA3AF', fontSize: 10 },
      }],
    })
  }

  // 4. 趋势折线
  if (trendChartRef.value) {
    const chart = echarts.init(trendChartRef.value)
    charts.push(chart)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 10, right: 20, top: 20, bottom: 10, containLabel: true },
      xAxis: { type: 'category', data: ov.trend.map(t => t.label), axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      series: [{
        type: 'line',
        data: ov.trend.map(t => t.saving),
        smooth: true,
        lineStyle: { color: '#10B981', width: 3 },
        itemStyle: { color: '#10B981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.25)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
          ]),
        },
        symbol: 'circle', symbolSize: 7,
      }],
    })
  }
}

async function loadSplit() {
  const p = costFilterStore.params()
  const [sumRes, deptRes, appRes] = await Promise.all([
    costApi.summary(6, p),
    costApi.byDepartment(p),
    costApi.byApplication(p),
  ])
  billTrend.value = sumRes.data || []
  deptData.value = deptRes.data || []
  appData.value = appRes.data || []
  await nextTick()
  renderBillCharts()
}

async function load() {
  loading.value = true
  try {
    const ovRes = await costApi.overview()
    overview.value = ovRes.data
    await loadSplit()
    renderCharts()
  } catch { /* 静默 */ } finally { loading.value = false }
}

// 全局筛选联动（跨页面 store 变化 → 重新加载分摊图）
watch(
  () => ({ ...costFilterStore.filter }),
  () => {
    splitCharts.forEach(c => c.dispose())
    splitCharts.length = 0
    loadSplit()
  },
  { deep: true },
)

function renderBillCharts() {
  // 月度成本趋势
  if (billTrendChartRef.value) {
    const chart = echarts.init(billTrendChartRef.value)
    splitCharts.push(chart)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 10, right: 20, top: 20, bottom: 10, containLabel: true },
      xAxis: { type: 'category', data: billTrend.value.map((b: any) => b.bill_month), axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      series: [{
        type: 'line',
        data: billTrend.value.map((b: any) => parseFloat(b.total || 0)),
        smooth: true,
        lineStyle: { color: '#7C3AED', width: 3 },
        itemStyle: { color: '#7C3AED' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(124, 58, 237, 0.25)' },
            { offset: 1, color: 'rgba(124, 58, 237, 0.02)' },
          ]),
        },
        symbol: 'circle', symbolSize: 7,
      }],
    })
  }
  // 部门分摊
  if (deptChartRef.value) {
    const chart = echarts.init(deptChartRef.value)
    splitCharts.push(chart)
    const data = deptData.value.map((d: any, i: number) => ({
      name: d.department__name || '未分配',
      value: parseFloat(d.total || 0),
      itemStyle: { color: COLORS[i % COLORS.length] },
    }))
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
      legend: { bottom: 0, textStyle: { color: '#6B7280' } },
      series: [{
        type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data,
      }],
    })
    chart.on('click', (p: any) => {
      if (p.name) router.push({ path: '/cost/share', query: { type: 'department', name: p.name } })
    })
  }
  // 应用分摊（横向条形）
  if (appChartRef.value) {
    const chart = echarts.init(appChartRef.value)
    splitCharts.push(chart)
    const data = appData.value.map((d: any, i: number) => ({
      name: d.application__name || '未归属',
      value: parseFloat(d.total || 0),
      itemStyle: { color: COLORS[i % COLORS.length] },
    }))
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 40, top: 10, bottom: 10, containLabel: true },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      yAxis: { type: 'category', data: data.map(d => d.name), axisLine: { show: false }, axisLabel: { color: '#6B7280' } },
      series: [{
        type: 'bar', data, barWidth: 16,
        label: { show: true, position: 'right', formatter: (p: any) => '¥' + p.value.toLocaleString(), color: '#6B7280', fontSize: 10 },
      }],
    })
    chart.on('click', (p: any) => {
      if (p.name) router.push({ path: '/cost/share', query: { type: 'application', name: p.name } })
    })
  }
}

function openSugDetail(record: OptimizationSuggestion) {
  sugDetail.value = record
  detailVisible.value = true
}

async function resolveSug(sug: OptimizationSuggestion) {
  try {
    await costApi.resolveSuggestion(sug.id)
    message.success('已标记为处理')
    detailVisible.value = false
    load()
  } catch { message.error('操作失败') }
}

onMounted(load)
onBeforeUnmount(() => {
  charts.forEach(c => c.dispose())
  splitCharts.forEach(c => c.dispose())
})
</script>

<style scoped>
.cost-page { max-width: 1400px; margin: 0 auto; }

/* 数据权限说明卡片 */
.perm-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; margin-bottom: 16px; }
.perm-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--cm-border-default); }
.perm-head-left { display: flex; align-items: center; gap: 12px; }
.perm-avatar { width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #7C3AED, #A855F7); color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; }
.perm-user { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.perm-sub { font-size: 12px; color: var(--cm-text-secondary); margin-top: 2px; }
.perm-scope { font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 999px; }
.scope-all { background: #EDE9FE; color: #7C3AED; border: 1px solid #DDD0FF; }
.scope-dept { background: #ECFDF5; color: #10B981; border: 1px solid #A7F3D0; }
.perm-collapse-title { font-size: 13px; color: #7C3AED; font-weight: 600; }
.perm-body { padding: 4px 6px; }
.perm-section { margin-bottom: 16px; }
.perm-section:last-child { margin-bottom: 4px; }
.perm-heading { font-size: 13px; font-weight: 600; color: #7C3AED; margin-bottom: 8px; }
.perm-text { font-size: 13px; color: var(--cm-text-secondary); line-height: 1.8; margin-bottom: 10px; }
.perm-table-wrap { overflow-x: auto; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-md); }
.perm-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.perm-table th { background: #FAF8FF; color: var(--cm-text-primary); font-weight: 600; text-align: left; padding: 8px 14px; border-bottom: 1px solid var(--cm-border-default); }
.perm-table td { padding: 8px 14px; border-bottom: 1px solid var(--cm-border-default); color: var(--cm-text-secondary); }
.perm-table tr:last-child td { border-bottom: none; }
.perm-note { font-size: 13px; color: #92400E; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: var(--cm-radius-md); padding: 10px 14px; line-height: 1.8; }

.page-header { display: flex; align-items: center; margin-bottom: 24px; }
.header-content { display: flex; align-items: center; gap: 16px; }
.back-btn {
  width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
  background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-md);
  color: var(--cm-text-primary); cursor: pointer; transition: all var(--cm-transition-fast);
}
.back-btn:hover { border-color: var(--cm-border-hover); background: var(--cm-bg-tertiary); }
.back-btn svg { width: 20px; height: 20px; }
.page-title { font-size: var(--cm-text-2xl); font-weight: var(--cm-font-bold); color: var(--cm-text-primary); margin: 0; }
.page-subtitle { font-size: var(--cm-text-sm); color: var(--cm-text-secondary); margin-top: 4px; }

.empty-card { text-align: center; padding: 80px 20px; background: white; border-radius: var(--cm-radius-xl); border: 1px solid var(--cm-border-default); }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-title { font-size: var(--cm-text-lg); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.empty-desc { font-size: var(--cm-text-sm); color: var(--cm-text-tertiary); margin: 8px 0 20px; }

.stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card {
  background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg);
  padding: 18px; box-shadow: var(--cm-shadow-xs); position: relative; overflow: hidden;
}
.stat-card::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.stat-card:nth-child(1)::after { background: #EF4444; }
.stat-card:nth-child(2)::after { background: #10B981; }
.stat-card:nth-child(3)::after { background: #3B82F6; }
.stat-card:nth-child(4)::after { background: #7C3AED; }
.stat-card:nth-child(5)::after { background: #F59E0B; }
.stat-label { font-size: var(--cm-text-xs); color: var(--cm-text-secondary); margin-bottom: 6px; }
.stat-value { font-size: 26px; font-weight: var(--cm-font-bold); line-height: 1.1; }
.stat-value.red { color: #EF4444; }
.stat-value.green { color: #10B981; }
.stat-value.blue { color: #3B82F6; }
.stat-value.purple { color: #7C3AED; }
.stat-value.orange { color: #F59E0B; }
.stat-sub { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); margin-top: 5px; }

.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.split-filter { display: flex; align-items: center; gap: 10px; background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); padding: 10px 16px; margin-bottom: 16px; }
.sf-label { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); margin-right: 4px; }
.cost-split-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.cost-split-grid .span-2 { grid-column: span 2; }
.chart-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; }
.chart-title { padding: 14px 18px; font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); border-bottom: 1px solid var(--cm-border-default); }
.chart-title { display: flex; align-items: center; justify-content: space-between; }
.detail-link { font-size: var(--cm-text-xs); color: #7C3AED; cursor: pointer; font-weight: var(--cm-font-medium); }
.detail-link:hover { opacity: 0.8; }
.chart-body { padding: 12px; }

.table-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--cm-border-default); display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: var(--cm-text-base); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); margin: 0; }
.card-hint { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); }

.cloud-pill { padding: 2px 10px; background: var(--cm-bg-tertiary); border-radius: var(--cm-radius-full); font-size: var(--cm-text-xs); font-weight: var(--cm-font-medium); color: var(--cm-text-primary); }
.saving-text { color: #10B981; font-weight: var(--cm-font-semibold); }
.muted { color: var(--cm-text-tertiary); }

.sug-detail-head { background: var(--cm-bg-tertiary); border-radius: var(--cm-radius-md); padding: 12px 16px; }
.sug-title { font-size: var(--cm-text-base); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.sug-desc { font-size: var(--cm-text-sm); color: var(--cm-text-secondary); margin-top: 4px; }
.detail-actions { margin-top: 16px; text-align: right; }

:deep(.clickable-row) { cursor: pointer; }
:deep(.ant-table-row:hover) { background: var(--cm-bg-tertiary) !important; }

.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
