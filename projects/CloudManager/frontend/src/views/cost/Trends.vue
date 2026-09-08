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
          <h1 class="page-title">成本趋势</h1>
          <p class="page-subtitle">分析和监控云资源成本</p>
        </div>
      </div>
    </div>

    <CostGlobalFilter />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 图表区域 -->
    <div v-else class="charts-grid fade-in delay-1">
      <!-- 月度趋势 -->
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            月度趋势
          </h3>
        </div>
        <div class="card-body">
          <div ref="chartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 部门分摊 -->
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            部门分摊
          </h3>
        </div>
        <div class="card-body">
          <div ref="deptChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 按应用分摊 -->
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7" rx="1"></rect>
              <rect x="14" y="3" width="7" height="7" rx="1"></rect>
              <rect x="3" y="14" width="7" height="7" rx="1"></rect>
              <rect x="14" y="14" width="7" height="7" rx="1"></rect>
            </svg>
            按应用分摊
          </h3>
        </div>
        <div class="card-body">
          <div ref="appChartRef" class="chart-container"></div>
        </div>
      </div>
    </div>

    <!-- 账单明细 -->
    <div class="table-card fade-in delay-2">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path>
            <path d="M14 2v6h6"></path>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          账单明细
        </h3>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>月份</th>
              <th>云账号</th>
              <th>总费用</th>
              <th>币种</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in bills" :key="record.id">
              <td>{{ record.bill_month }}</td>
              <td>{{ record.account_name }}</td>
              <td>
                <span class="cost-value">¥{{ record.total_cost }}</span>
              </td>
              <td>{{ record.currency }}</td>
              <td>{{ record.created_at }}</td>
            </tr>
            <tr v-if="!bills.length">
              <td colspan="5">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path>
                  </svg>
                  <span>暂无账单数据</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { costApi } from '@/api'
import { useCostFilterStore } from '@/stores/costFilter'
import CostGlobalFilter from '@/components/cost/CostGlobalFilter.vue'
import * as echarts from 'echarts'

const costFilterStore = useCostFilterStore()
const loading = ref(false)
const chartRef = ref<HTMLElement>()
const deptChartRef = ref<HTMLElement>()
const appChartRef = ref<HTMLElement>()
const bills = ref<any[]>([])
const deptData = ref<any[]>([])
const appData = ref<any[]>([])
const charts: echarts.ECharts[] = []

async function loadData() {
  loading.value = true
  try {
    charts.forEach(c => c.dispose())
    charts.length = 0
    const p = costFilterStore.params()
    const [summaryRes, deptRes, appRes, billsRes] = await Promise.all([
      costApi.summary(6, p),
      costApi.byDepartment(p),
      costApi.byApplication(p),
      costApi.bills({ page_size: 12 }),
    ])
    bills.value = billsRes.data.results
    deptData.value = deptRes.data
    appData.value = appRes.data

    // 渲染趋势图
    if (chartRef.value && summaryRes.data.length) {
      const chart = echarts.init(chartRef.value)
      charts.push(chart)
      chart.setOption({
        tooltip: { 
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#E5E7EB',
          textStyle: { color: '#1F2937' }
        },
        grid: { top: 20, right: 20, bottom: 30, left: 60 },
        xAxis: { 
          type: 'category', 
          data: summaryRes.data.map((d: any) => d.bill_month),
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          axisLabel: { color: '#6B7280' }
        },
        yAxis: { 
          type: 'value', 
          name: '费用 (元)',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: '#F3F4F6' } },
          axisLabel: { color: '#6B7280' }
        },
        series: [{
          type: 'line',
          data: summaryRes.data.map((d: any) => parseFloat(d.total)),
          smooth: true,
          lineStyle: { color: '#8B5CF6', width: 3 },
          itemStyle: { color: '#8B5CF6' },
          areaStyle: { 
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
              { offset: 1, color: 'rgba(139, 92, 246, 0.05)' }
            ])
          },
          symbol: 'circle',
          symbolSize: 8
        }],
      })
    }

    // 渲染部门分摊饼图
    if (deptChartRef.value && deptRes.data.length) {
      const colors = ['#8B5CF6', '#F97316', '#10B981', '#3B82F6', '#EF4444', '#F59E0B']
      const chart = echarts.init(deptChartRef.value)
      charts.push(chart)
      chart.setOption({
        tooltip: { 
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#E5E7EB',
          textStyle: { color: '#1F2937' }
        },
        legend: {
          bottom: 10,
          textStyle: { color: '#6B7280' }
        },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: { 
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 3
          },
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' }
          },
          data: deptRes.data.map((d: any, i: number) => ({
            name: d.department__name || '未分配',
            value: parseFloat(d.total),
            itemStyle: { color: colors[i % colors.length] }
          })),
        }],
      })
    }

    // 渲染按应用分摊饼图
    if (appChartRef.value && appRes.data.length) {
      const colors = ['#7C3AED', '#0EA5E9', '#F97316', '#10B981', '#EF4444', '#F59E0B', '#8B5CF6']
      const chart = echarts.init(appChartRef.value)
      charts.push(chart)
      chart.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#E5E7EB',
          textStyle: { color: '#1F2937' },
        },
        legend: {
          bottom: 10,
          textStyle: { color: '#6B7280' },
        },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 3,
          },
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' },
          },
          data: appRes.data.map((d: any, i: number) => ({
            name: d.application__name || '未归属',
            value: parseFloat(d.total),
            itemStyle: { color: colors[i % colors.length] },
          })),
        }],
      })
    }
  } catch { /* 静默 */ } finally { loading.value = false }
}

// 全局筛选联动
watch(
  () => ({ ...costFilterStore.filter }),
  () => loadData(),
  { deep: true },
)

onMounted(loadData)
</script>

<style scoped>
.cost-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid var(--cm-border-default);
  border-radius: var(--cm-radius-md);
  color: var(--cm-text-primary);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.back-btn:hover {
  border-color: var(--cm-border-hover);
  background: var(--cm-bg-tertiary);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: var(--cm-text-3xl);
  font-weight: var(--cm-font-bold);
  color: var(--cm-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--cm-text-base);
  color: var(--cm-text-secondary);
  margin: 4px 0 0;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  gap: 16px;
  color: var(--cm-text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--cm-color-gray-200);
  border-top-color: var(--cm-color-primary-600);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 图表网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

/* 图表卡片 */
.chart-card {
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  border: 1px solid var(--cm-glass-border);
  border-radius: var(--cm-radius-xl);
  box-shadow: var(--cm-shadow-glass);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(124, 58, 237, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-primary);
  margin: 0;
}

.card-title svg {
  width: 22px;
  height: 22px;
  color: var(--cm-color-primary-600);
}

.card-body {
  padding: 24px;
}

.chart-container {
  height: 320px;
}

/* 表格卡片 */
.table-card {
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  border: 1px solid var(--cm-glass-border);
  border-radius: var(--cm-radius-xl);
  box-shadow: var(--cm-shadow-glass);
  overflow: hidden;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(124, 58, 237, 0.03);
  border-bottom: 1px solid var(--cm-border-default);
}

.data-table td {
  padding: 14px 16px;
  font-size: var(--cm-text-sm);
  color: var(--cm-text-primary);
  border-bottom: 1px solid rgba(124, 58, 237, 0.05);
}

.data-table tbody tr {
  transition: background var(--cm-transition-fast);
}

.data-table tbody tr:hover {
  background: rgba(124, 58, 237, 0.02);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.cost-value {
  font-weight: var(--cm-font-bold);
  color: var(--cm-color-error);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--cm-text-tertiary);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

/* 动画 */
.fade-in {
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }

/* 响应式 */
@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .back-btn {
    width: 36px;
    height: 36px;
  }
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  .back-btn {
    background: var(--cm-bg-tertiary);
    border-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
