<template>
  <div class="cost-page">
    <!-- ========== 头部 ========== -->
    <div class="page-header fade-in">
      <div class="header-content">
        <button class="back-btn" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"></path>
          </svg>
        </button>
        <div>
          <h1 class="page-title">📊 {{ typeLabel }} · {{ name }}</h1>
          <p class="page-subtitle">{{ month }} 账单 · 成本分摊明细与数据溯源</p>
        </div>
      </div>
      <div class="header-actions">
        <a-button type="primary" @click="exportCsv" :loading="exporting">
          📥 导出CSV
        </a-button>
      </div>
    </div>

    <a-spin :spinning="loading">
      <template v-if="summary">
        <!-- ========== 统计卡 ========== -->
        <div class="stat-grid fade-in">
          <div class="stat-card">
            <div class="sc-label">本月总费用</div>
            <div class="sc-value">¥{{ summary.total.toLocaleString() }}</div>
          </div>
          <div class="stat-card">
            <div class="sc-label">覆盖资源数</div>
            <div class="sc-value">{{ summary.count.toLocaleString() }}</div>
          </div>
          <div class="stat-card">
            <div class="sc-label">占全月比例</div>
            <div class="sc-value">{{ summary.pct }}%</div>
          </div>
          <div class="stat-card">
            <div class="sc-label">日均费用</div>
            <div class="sc-value">¥{{ Math.round(summary.total / 31).toLocaleString() }}</div>
          </div>
        </div>

        <!-- ========== 分布图 ========== -->
        <div class="charts-grid fade-in">
          <div class="chart-card">
            <div class="chart-title">🧩 资源类型费用分布</div>
            <div class="chart-body" ref="typeChartRef" style="height: 240px"></div>
          </div>
          <div class="chart-card">
            <div class="chart-title">🏆 TOP10 资源费用排行</div>
            <div class="chart-body" ref="topChartRef" style="height: 240px"></div>
          </div>
        </div>

        <!-- ========== 明细表 ========== -->
        <div class="table-card fade-in">
          <div class="card-header">
            <h3 class="card-title">📋 费用明细</h3>
            <span class="card-hint">共 {{ total }} 条费用记录</span>
          </div>
          <a-table
            :data-source="items"
            :columns="columns"
            :pagination="pagination"
            :loading="tableLoading"
            size="middle"
            row-key="id"
            @change="onTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'cost'">
                <span class="cost-text">¥{{ Number(record.cost).toLocaleString() }}</span>
              </template>
              <template v-if="column.key === 'resource_type'">
                <a-tag>{{ record.resource_type || '-' }}</a-tag>
              </template>
              <template v-if="column.key === 'application_name'">
                <a-tag :color="record.application_name === '未归属' ? 'orange' : 'blue'">
                  {{ record.application_name }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </div>

        <!-- ========== 数据链路说明（可折叠） ========== -->
        <a-collapse class="linkage-collapse fade-in" :bordered="false" expand-icon-position="end">
          <a-collapse-panel key="1">
            <template #header>
              <span class="linkage-title">🔗 数据来源与分摊链路（架构说明 · 真实场景 vs 本系统模拟）</span>
            </template>

            <div class="linkage-body">
              <!-- 链路示意 -->
              <div class="lk-section">
                <div class="lk-heading">① 数据链路总览</div>
                <div class="pipeline">
                  <div class="p-node">
                    <div class="pn-title">业务定义</div>
                    <div class="pn-sub">部门 / 应用<br/>成本中心</div>
                  </div>
                  <div class="p-arrow">申请时自动打标</div>
                  <div class="p-node">
                    <div class="pn-title">云资源</div>
                    <div class="pn-sub">实例 / DB / MQ<br/>+ Tag 标签</div>
                  </div>
                  <div class="p-arrow">采集器同步标签</div>
                  <div class="p-node">
                    <div class="pn-title">CMDB 归属</div>
                    <div class="pn-sub">Resource<br/>department / application</div>
                  </div>
                  <div class="p-arrow">账单带分摊标签</div>
                  <div class="p-node">
                    <div class="pn-title">账单明细</div>
                    <div class="pn-sub">CostItem<br/>department / application</div>
                  </div>
                  <div class="p-arrow">按标签聚合</div>
                  <div class="p-node">
                    <div class="pn-title">分摊视图</div>
                    <div class="pn-sub">部门分摊<br/>应用分摊</div>
                  </div>
                </div>
              </div>

              <!-- 真实 vs 模拟 -->
              <div class="lk-section">
                <div class="lk-heading">② 真实云环境 vs 本系统模拟实现</div>
                <div class="lk-table-wrap">
                  <table class="lk-table">
                    <thead>
                      <tr>
                        <th style="width: 160px">环节</th>
                        <th>真实云环境</th>
                        <th>本系统模拟</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>资源归属部门/应用</td>
                        <td>申请资源时选择服务 + 部门 → 云平台自动打 Tag（如 <code>Department</code> / <code>Service</code>）→ 采集器拉取并解析标签写入 CMDB</td>
                        <td><code>Resource.department / application</code>：seed 按业务设定直接赋值，模拟"标签已解析入库"</td>
                      </tr>
                      <tr>
                        <td>账单分摊标签</td>
                        <td>云账单激活 Cost Allocation Tag，每行费用明细自带部门/应用标签（独立于资源归属标签）</td>
                        <td><code>CostItem.department / application</code>：seed 生成账单时随机分配（部门 5 选 1、应用约 70% 归属），模拟"账单标签已解析"</td>
                      </tr>
                      <tr>
                        <td>成本分摊聚合</td>
                        <td>FinOps 分摊引擎按账单标签把费用归集到部门/应用，输出分摊报表</td>
                        <td><code>by_department</code> / <code>by_application</code> 接口按 <code>CostItem</code> 字段聚合，输出分摊图 + 本明细页</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 字段溯源 -->
              <div class="lk-section">
                <div class="lk-heading">③ 字段溯源（为什么两套标签要分开）</div>
                <div class="lk-table-wrap">
                  <table class="lk-table">
                    <thead>
                      <tr>
                        <th style="width: 200px">字段</th>
                        <th style="width: 260px">真实来源</th>
                        <th>说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><code>cmdb.Resource.department</code></td>
                        <td>云上资源标签 <code>Department</code> → 采集器映射</td>
                        <td>描述"资源归哪个部门管"（资产视角）</td>
                      </tr>
                      <tr>
                        <td><code>cmdb.Resource.application</code></td>
                        <td>云上资源标签 <code>Service</code> → 采集器映射</td>
                        <td>描述"资源属于哪个应用/服务"（业务视角）</td>
                      </tr>
                      <tr>
                        <td><code>cost.CostItem.department</code></td>
                        <td>云账单 Cost Allocation Tag → 账单导入解析</td>
                        <td>描述"这笔费用摊到哪个部门"（财务视角）</td>
                      </tr>
                      <tr>
                        <td><code>cost.CostItem.application</code></td>
                        <td>云账单 Cost Allocation Tag → 账单导入解析</td>
                        <td>描述"这笔费用摊到哪个应用"（财务视角）</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div class="lk-note">
                  💡 资源归属标签与账单分摊标签通常一致，但建模上必须分开维护：
                  资源可能调整归属（迁移/改属）而不影响历史账单；账单标签也可能按财务口径重映射。
                  分离后，任一变化只改一侧，互不污染。
                </div>
              </div>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import { costApi } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const tableLoading = ref(false)
const exporting = ref(false)
const summary = ref<any>(null)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const type = computed(() => (route.query.type as string) || 'department')
const name = computed(() => (route.query.name as string) || '')
const month = computed(() => (route.query.month as string) || new Date().toISOString().slice(0, 7))

const typeLabel = computed(() => (type.value === 'application' ? '应用分摊' : '部门分摊'))
const dimLabel = computed(() => (type.value === 'application' ? '分摊应用' : '分摊部门'))

const COLORS = ['#7C3AED', '#0EA5E9', '#F97316', '#10B981', '#EF4444', '#F59E0B', '#8B5CF6']

const typeChartRef = ref<HTMLElement>()
const topChartRef = ref<HTMLElement>()
let typeChart: echarts.ECharts | null = null
let topChart: echarts.ECharts | null = null

const columns = [
  { title: '资源名称', key: 'resource_name', dataIndex: 'resource_name', width: 180, ellipsis: true },
  { title: '资源ID', key: 'resource_id', dataIndex: 'resource_id', width: 150, ellipsis: true },
  { title: '资源类型', key: 'resource_type', dataIndex: 'resource_type', width: 110 },
  { title: '区域', key: 'region', dataIndex: 'region', width: 110 },
  { title: '费用日期', key: 'cost_date', dataIndex: 'cost_date', width: 110 },
  { title: '费用', key: 'cost', dataIndex: 'cost', width: 110, align: 'right' },
  { title: '分摊部门', key: 'department_name', dataIndex: 'department_name', width: 100 },
  { title: '分摊应用', key: 'application_name', dataIndex: 'application_name', width: 110 },
]

const pagination = computed(() => ({
  current: page.value,
  pageSize,
  total: total.value,
  showSizeChanger: false,
  showTotal: (t: number) => `共 ${t} 条`,
}))

async function load() {
  loading.value = true
  try {
    const [sumRes, itemsRes] = await Promise.all([
      costApi.shareSummary({ type: type.value, name: name.value, month: month.value }),
      costApi.shareItems({ type: type.value, name: name.value, month: month.value, page: page.value, page_size: pageSize }),
    ])
    summary.value = sumRes.data
    items.value = itemsRes.data.results
    total.value = itemsRes.data.count
    await nextTick()
    renderCharts()
  } catch { message.error('加载分摊明细失败') } finally { loading.value = false }
}

async function loadPage(p: number) {
  tableLoading.value = true
  try {
    const { data } = await costApi.shareItems({ type: type.value, name: name.value, month: month.value, page: p, page_size: pageSize })
    items.value = data.results
    total.value = data.count
    page.value = p
  } catch { message.error('加载失败') } finally { tableLoading.value = false }
}

function onTableChange(pag: any) {
  loadPage(pag.current)
}

function renderCharts() {
  if (!summary.value) return
  if (typeChartRef.value) {
    typeChart?.dispose()
    typeChart = echarts.init(typeChartRef.value)
    const data = (summary.value.by_resource_type || []).map((d: any, i: number) => ({
      name: d.type, value: d.total,
      itemStyle: { color: COLORS[i % COLORS.length] },
    }))
    typeChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (ps: any) => `${ps[0].name}: ¥${Number(ps[0].value).toLocaleString()}` },
      grid: { left: 10, right: 20, top: 20, bottom: 10, containLabel: true },
      xAxis: { type: 'category', data: data.map((d: any) => d.name), axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      series: [{ type: 'bar', data, barWidth: 22, label: { show: true, position: 'top', formatter: (p: any) => '¥' + p.value.toLocaleString(), color: '#6B7280', fontSize: 10 } }],
    })
  }
  if (topChartRef.value) {
    topChart?.dispose()
    topChart = echarts.init(topChartRef.value)
    const data = (summary.value.top_resources || []).map((d: any, i: number) => ({
      name: d.resource_name, value: d.total,
      itemStyle: { color: COLORS[i % COLORS.length] },
    })).reverse()
    topChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (ps: any) => `${ps[0].name}: ¥${Number(ps[0].value).toLocaleString()}` },
      grid: { left: 10, right: 50, top: 10, bottom: 10, containLabel: true },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F3F4F6' } }, axisLabel: { color: '#9CA3AF' } },
      yAxis: { type: 'category', data: data.map((d: any) => d.name), axisLine: { show: false }, axisLabel: { color: '#6B7280' } },
      series: [{ type: 'bar', data, barWidth: 14, label: { show: true, position: 'right', formatter: (p: any) => '¥' + p.value.toLocaleString(), color: '#6B7280', fontSize: 10 } }],
    })
  }
}

async function exportCsv() {
  exporting.value = true
  try {
    const { data } = await costApi.shareExport({ type: type.value, name: name.value, month: month.value })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `cost_share_${type.value}_${name.value || 'all'}_${month.value}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success('已导出 CSV，可用 Excel 打开')
  } catch { message.error('导出失败') } finally { exporting.value = false }
}

onMounted(load)
// keep-alive 缓存下，路由参数（type/name/month）变化时重新加载数据
watch(
  () => [route.query.type, route.query.name, route.query.month],
  () => { page.value = 1; load() },
)
onBeforeUnmount(() => {
  typeChart?.dispose()
  topChart?.dispose()
})
</script>

<style scoped>
.cost-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.header-content { display: flex; align-items: center; gap: 16px; }
.back-btn {
  width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
  background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-md);
  cursor: pointer; color: var(--cm-text-secondary); transition: all 0.2s;
}
.back-btn:hover { border-color: var(--cm-border-hover); background: var(--cm-bg-tertiary); }
.back-btn svg { width: 20px; height: 20px; }
.page-title { font-size: var(--cm-text-2xl); font-weight: var(--cm-font-bold); color: var(--cm-text-primary); margin: 0; }
.page-subtitle { font-size: var(--cm-text-sm); color: var(--cm-text-secondary); margin-top: 4px; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card {
  position: relative; background: white; border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-lg); padding: 18px 20px; overflow: hidden;
}
.stat-card::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.stat-card:nth-child(1)::after { background: #7C3AED; }
.stat-card:nth-child(2)::after { background: #0EA5E9; }
.stat-card:nth-child(3)::after { background: #F97316; }
.stat-card:nth-child(4)::after { background: #10B981; }
.sc-label { font-size: var(--cm-text-xs); color: var(--cm-text-secondary); }
.sc-value { font-size: var(--cm-text-xl); font-weight: var(--cm-font-bold); color: var(--cm-text-primary); margin-top: 6px; }

.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.chart-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; }
.chart-title { padding: 14px 18px; font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); border-bottom: 1px solid var(--cm-border-default); }

.table-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; margin-bottom: 16px; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--cm-border-default); display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: var(--cm-text-base); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); margin: 0; }
.card-hint { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); }
.cost-text { color: #7C3AED; font-weight: var(--cm-font-semibold); }

.linkage-collapse { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; }
.linkage-title { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.linkage-body { padding: 8px 4px; }
.lk-section { margin-bottom: 22px; }
.lk-section:last-child { margin-bottom: 4px; }
.lk-heading { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: #7C3AED; margin-bottom: 12px; }

/* 链路管道 */
.pipeline { display: flex; align-items: stretch; gap: 0; flex-wrap: wrap; }
.p-node {
  background: #FAF8FF; border: 1px solid #DDD0FF; border-radius: var(--cm-radius-md);
  padding: 12px 14px; min-width: 120px; text-align: center; flex: 1;
}
.pn-title { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: #7C3AED; }
.pn-sub { font-size: 11px; color: var(--cm-text-secondary); margin-top: 6px; line-height: 1.6; }
.p-arrow {
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--cm-text-tertiary); padding: 0 10px; white-space: nowrap;
}
.p-arrow::after { content: '→'; margin-left: 6px; color: #7C3AED; font-weight: bold; }

.lk-table-wrap { overflow-x: auto; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-md); }
.lk-table { width: 100%; border-collapse: collapse; font-size: var(--cm-text-sm); }
.lk-table th { background: #FAF8FF; color: var(--cm-text-primary); font-weight: var(--cm-font-semibold); text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--cm-border-default); }
.lk-table td { padding: 10px 14px; border-bottom: 1px solid var(--cm-border-default); color: var(--cm-text-secondary); line-height: 1.7; vertical-align: top; }
.lk-table tr:last-child td { border-bottom: none; }
.lk-table code { background: #F3EEFF; color: #7C3AED; padding: 1px 6px; border-radius: 4px; font-size: 12px; }
.lk-note {
  margin-top: 12px; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: var(--cm-radius-md);
  padding: 12px 14px; font-size: var(--cm-text-sm); color: #92400E; line-height: 1.8;
}
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
