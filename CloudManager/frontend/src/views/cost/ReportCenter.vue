<template>
  <div class="cost-page">
    <!-- ========== 列表视图 ========== -->
    <template v-if="!detail">
      <div class="page-header fade-in">
        <div class="header-content">
          <button class="back-btn" @click="$router.back()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"></path>
            </svg>
          </button>
          <div>
            <h1 class="page-title">📊 分析报告</h1>
            <p class="page-subtitle">历史检测记录 · 支持下钻查看明细与导出</p>
          </div>
        </div>
      </div>

      <a-spin :spinning="loading">
        <a-empty v-if="!loading && reports.length === 0" description="暂无分析报告，请先在「规则配置」执行检测" style="padding: 60px" />
        <div v-else class="report-list fade-in">
          <div v-for="report in reports" :key="report.id" class="report-card">
            <div class="report-row">
              <div class="report-icon">📄</div>
              <div class="report-info">
                <div class="report-title"><span class="report-no">{{ report.report_no }}</span>{{ report.title }}</div>
                <div class="report-meta">
                  {{ report.executed_at }} · 执行人: {{ report.operator }} · 触发: {{ report.trigger_display }}
                </div>
              </div>
              <div class="report-stats">
                <div class="rs"><div class="v purple">{{ report.cloud_count }}</div><div class="l">云厂商</div></div>
                <div class="rs"><div class="v orange">{{ report.total_rules }}</div><div class="l">规则</div></div>
                <div class="rs"><div class="v blue">{{ report.total_matched }}</div><div class="l">资源</div></div>
                <div class="rs"><div class="v green">¥{{ report.total_saving.toLocaleString() }}</div><div class="l">月节省</div></div>
              </div>
              <div class="report-actions">
                <a-button type="primary" size="small" @click="openDetail(report)">查看详情</a-button>
                <a-button size="small" @click="exportReport(report)">📥 导出Excel</a-button>
              </div>
            </div>
          </div>
        </div>
      </a-spin>
    </template>

    <!-- ========== 详情视图 ========== -->
    <template v-else>
      <div class="detail-page fade-in">
        <div class="detail-head">
          <a-button size="small" class="back-btn-sm" @click="closeDetail">← 返回</a-button>
          <div class="detail-title">
            <div class="detail-title-text">📄 <span class="report-no">{{ detail.report_no }}</span> {{ detail.title }}</div>
            <div class="detail-meta">
              {{ detail.executed_at }} · 执行人: {{ detail.operator }} · 触发: {{ detail.trigger_display }}
              · 覆盖 {{ detail.cloud_count }} 个云厂商 · {{ detail.total_matched }} 个资源 · 预估节省 ¥{{ detail.total_saving.toLocaleString() }}/月
            </div>
          </div>
          <a-button type="primary" size="small" @click="exportReport(detail)">📥 导出Excel</a-button>
        </div>

        <div class="detail-body">
          <!-- 左侧维度树 -->
          <div class="detail-nav">
            <div class="nav-title">维度导航</div>
            <div class="tree-node">
              <div class="tree-row" :class="{ active: isActive({}) }" @click="selectNode({})">
                <span class="arrow"></span>
                <span class="tree-ico">🌐</span>
                <span class="tn-name">全部资源</span>
                <span class="tn-count">{{ detail.total_matched }}</span>
                <span class="tn-saving">¥{{ detail.total_saving.toLocaleString() }}</span>
              </div>
            </div>
            <div v-for="cloud in cloudNodes" :key="cloud.cloud" class="tree-node">
              <div class="tree-row" :class="{ active: isActive({ cloud: cloud.cloud }) }" @click="selectNode({ cloud: cloud.cloud })">
                <span class="arrow" :class="{ open: cloud._open }" @click.stop="cloud._open = !cloud._open">▶</span>
                <span class="tree-ico">{{ cloudIcon(cloud.cloud) }}</span>
                <span class="tn-name">{{ cloudName(cloud.cloud) }}</span>
                <span class="tn-count">{{ cloud.matched }}</span>
                <span class="tn-saving">¥{{ cloud.saving.toLocaleString() }}</span>
              </div>
              <div v-if="cloud._open" class="tree-children">
                <div v-for="acc in cloud.accounts" :key="acc.account" class="tree-node">
                  <div class="tree-row" :class="{ active: isActive({ cloud: cloud.cloud, account: acc.account }) }" @click="selectNode({ cloud: cloud.cloud, account: acc.account })">
                    <span class="arrow" :class="{ open: acc._open }" @click.stop="acc._open = !acc._open">▶</span>
                    <span class="tree-ico">🔑</span>
                    <span class="tn-name">{{ acc.account }}</span>
                    <span class="tn-count">{{ acc.matched }}</span>
                    <span class="tn-saving">¥{{ acc.saving.toLocaleString() }}</span>
                  </div>
                  <div v-if="acc._open" class="tree-children">
                    <div v-for="reg in acc.regions" :key="reg.region" class="tree-node">
                      <div class="tree-row" :class="{ active: isActive({ cloud: cloud.cloud, account: acc.account, region: reg.region }) }" @click="selectNode({ cloud: cloud.cloud, account: acc.account, region: reg.region })">
                        <span class="arrow" :class="{ open: reg._open }" @click.stop="reg._open = !reg._open">▶</span>
                        <span class="tree-ico">📍</span>
                        <span class="tn-name">{{ reg.region }}</span>
                        <span class="tn-count">{{ reg.matched }}</span>
                        <span class="tn-saving">¥{{ reg.saving.toLocaleString() }}</span>
                      </div>
                      <div v-if="reg._open" class="tree-children">
                        <div v-for="type in reg.types" :key="type.type_name" class="tree-node">
                          <div class="tree-row" :class="{ active: isActive({ cloud: cloud.cloud, account: acc.account, region: reg.region, type: type.type_name }) }" @click="selectNode({ cloud: cloud.cloud, account: acc.account, region: reg.region, type: type.type_name })">
                            <span class="arrow"></span>
                            <span class="tree-ico">📦</span>
                            <span class="tn-name">{{ type.type_name }}</span>
                            <span class="tn-count">{{ type.matched }}</span>
                            <span class="tn-saving">¥{{ type.saving.toLocaleString() }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧明细 -->
          <div class="detail-main">
            <div class="sum-bar">
              <div class="sum-item"><div class="sl">当前视图</div><div class="sv view-label">{{ selLabel }}</div></div>
              <div class="sum-item"><div class="sl">匹配资源</div><div class="sv blue">{{ filteredItems.length }}</div></div>
              <div class="sum-item"><div class="sl">预估节省</div><div class="sv green">¥{{ filteredSaving.toLocaleString() }}/月</div></div>
              <div class="sum-item"><div class="sl">节省占比</div><div class="sv orange">{{ filteredPct }}%</div></div>
            </div>

            <div class="filter-tabs">
              <a-tag :color="typeFilter === '' ? 'purple' : 'default'" style="cursor: pointer" @click="typeFilter = ''">全部类型</a-tag>
              <a-tag v-for="t in typeOptions" :key="t" :color="typeFilter === t ? 'purple' : 'default'" style="cursor: pointer" @click="typeFilter = t">{{ t }}</a-tag>
            </div>

            <a-table
              :data-source="filteredItems"
              :columns="detailColumns"
              :pagination="{ pageSize: 10, showSizeChanger: false }"
              size="small"
              :row-key="(r: any) => r.resource_id + r.suggestion_type"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'"><a-tag>{{ typeLabel(record.suggestion_type) }}</a-tag></template>
                <template v-if="column.key === 'severity'"><a-tag :color="sevColor(record.severity)">{{ sevLabel(record.severity) }}</a-tag></template>
                <template v-if="column.key === 'saving'">
                  <span v-if="record.estimated_saving > 0" class="saving-text">¥{{ Number(record.estimated_saving).toLocaleString() }}/月</span>
                  <span v-else class="muted">-</span>
                </template>
                <template v-if="column.key === 'resolved'">
                  <a-tag :color="record.is_resolved ? 'green' : 'orange'">{{ record.is_resolved ? '已处理' : '待处理' }}</a-tag>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onActivated } from 'vue'
import { message } from 'ant-design-vue'
import { costApi } from '@/api'
import type { OptimizationReport } from '@/types'

const loading = ref(false)
const reports = ref<OptimizationReport[]>([])
const detail = ref<OptimizationReport | null>(null)
const selFilter = reactive({ cloud: '', account: '', region: '', type: '' })
const typeFilter = ref('')
const cloudNodes = ref<any[]>([])

const providerMap: Record<string, string> = { aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', mock: 'Mock', all: '全部' }
const typeMap: Record<string, string> = {
  idle: '闲置资源', downsize: '建议降配', unused: '未使用', budget: '预算告警',
  trend: '趋势异常', reserved: '付费优化', storage: '存储优化',
}
function cloudName(c: string) { return providerMap[c] || c }
function cloudIcon(c: string) { return c === 'mock' ? '🟠' : c === 'aws' ? '🟧' : c === 'aliyun' ? '🟠' : '🔵' }
function typeLabel(t: string) { return typeMap[t] || t }
function sevLabel(s: string) { return { high: '高', medium: '中', low: '低' }[s] || s }
function sevColor(s: string) { return { high: 'red', medium: 'orange', low: 'green' }[s] || 'default' }

const detailColumns = [
  { title: '资源名称', key: 'resource_name', dataIndex: 'resource_name', width: 150, ellipsis: true },
  { title: '资源ID', key: 'resource_id', dataIndex: 'resource_id', width: 150, ellipsis: true },
  { title: '区域', key: 'region', dataIndex: 'region', width: 110 },
  { title: '规格', key: 'spec', dataIndex: 'spec', width: 130 },
  { title: '建议类型', key: 'type', dataIndex: 'suggestion_type', width: 100 },
  { title: '优先级', key: 'severity', dataIndex: 'severity', width: 80 },
  { title: '预估节省', key: 'saving', dataIndex: 'estimated_saving', width: 120 },
  { title: '状态', key: 'resolved', dataIndex: 'is_resolved', width: 90 },
]

async function load() {
  loading.value = true
  try {
    const { data } = await costApi.reports()
    reports.value = data
  } catch { /* 静默 */ } finally { loading.value = false }
}

function openDetail(report: OptimizationReport) {
  detail.value = report
  selFilter.cloud = ''; selFilter.account = ''; selFilter.region = ''; selFilter.type = ''
  typeFilter.value = ''
  // 初始化维度树（默认展开云层）
  cloudNodes.value = Object.values(report.tree_snapshot || {}).map((c: any) => ({
    ...c,
    _open: true,
    accounts: (c.accounts || []).map((a: any) => ({ ...a, _open: false, regions: (a.regions || []).map((r: any) => ({ ...r, _open: false })) })),
  }))
}
function closeDetail() { detail.value = null }

function isActive(f: any) {
  return selFilter.cloud === (f.cloud || '')
    && selFilter.account === (f.account || '')
    && selFilter.region === (f.region || '')
    && selFilter.type === (f.type || '')
}
function selectNode(f: any) {
  Object.assign(selFilter, f)
  typeFilter.value = ''
}

const filteredItems = computed(() => {
  if (!detail.value) return []
  let list = detail.value.items_snapshot.filter((it: any) => {
    if (selFilter.cloud && it.cloud !== selFilter.cloud) return false
    if (selFilter.account && it.account !== selFilter.account) return false
    if (selFilter.region && it.region !== selFilter.region) return false
    if (selFilter.type && it.resource_type !== selFilter.type) return false
    return true
  })
  if (typeFilter.value) list = list.filter((it: any) => it.resource_type === typeFilter.value)
  return list
})
const filteredSaving = computed(() => filteredItems.value.reduce((s, it: any) => s + Number(it.estimated_saving || 0), 0))
const filteredPct = computed(() => {
  const total = detail.value?.total_saving || 0
  return total > 0 ? Math.round((filteredSaving.value / total) * 100) : 0
})
const selLabel = computed(() => {
  const parts = [cloudName(selFilter.cloud) || '全部云', selFilter.account, selFilter.region, selFilter.type].filter(Boolean)
  return parts.length ? parts.join(' / ') : '全部资源'
})
const typeOptions = computed(() => {
  const s = new Set<string>()
  if (detail.value) detail.value.items_snapshot.forEach((it: any) => { if (it.resource_type) s.add(it.resource_type) })
  return [...s]
})

async function exportReport(report: OptimizationReport) {
  try {
    const { data } = await costApi.exportReport(report.id)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success('已导出 CSV，可用 Excel 打开')
  } catch { message.error('导出失败') }
}

let activatedOnce = false
onMounted(load)
onActivated(() => {
  if (activatedOnce) load()
  activatedOnce = true
})
</script>

<style scoped>
.cost-page { max-width: 1400px; margin: 0 auto; }
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

/* 报告列表 */
.report-card { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); margin-bottom: 12px; box-shadow: var(--cm-shadow-xs); transition: box-shadow var(--cm-transition-base); }
.report-card:hover { box-shadow: var(--cm-shadow-md); }
.report-row { display: flex; align-items: center; gap: 16px; padding: 16px 20px; }
.report-icon { width: 44px; height: 44px; border-radius: var(--cm-radius-md); background: var(--cm-bg-tertiary); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.report-info { flex: 1; min-width: 0; }
.report-title { font-size: var(--cm-text-base); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }.report-no { display: inline-block; font-family: 'SF Mono', Menlo, monospace; font-size: 11px; color: #7C3AED; background: #F3EEFF; border: 1px solid #DDD0FF; border-radius: 4px; padding: 0 6px; margin-right: 8px; vertical-align: 1px; }.report-meta { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); margin-top: 3px; }
.report-stats { display: flex; gap: 24px; flex-shrink: 0; }
.report-stats .rs { text-align: center; }
.report-stats .rs .v { font-size: 18px; font-weight: var(--cm-font-bold); }
.report-stats .rs .l { font-size: 10px; color: var(--cm-text-tertiary); }
.v.purple { color: #7C3AED; } .v.orange { color: #F59E0B; } .v.blue { color: #3B82F6; } .v.green { color: #10B981; }
.report-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* 详情页 */
.detail-page { background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); overflow: hidden; }
.detail-head { padding: 16px 20px; border-bottom: 1px solid var(--cm-border-default); display: flex; align-items: center; gap: 16px; }
.back-btn-sm { flex-shrink: 0; }
.detail-title { flex: 1; min-width: 0; }
.detail-title-text { font-size: var(--cm-text-base); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); }
.detail-meta { font-size: var(--cm-text-xs); color: var(--cm-text-tertiary); margin-top: 3px; }
.detail-body { display: flex; min-height: 520px; }

.detail-nav { width: 300px; border-right: 1px solid var(--cm-border-default); padding: 16px; flex-shrink: 0; overflow-y: auto; max-height: 70vh; }
.nav-title { font-size: var(--cm-text-xs); font-weight: var(--cm-font-semibold); color: var(--cm-text-secondary); margin-bottom: 12px; }
.tree-node { margin-bottom: 2px; }
.tree-row { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: var(--cm-radius-sm); cursor: pointer; font-size: var(--cm-text-xs); transition: background var(--cm-transition-fast); }
.tree-row:hover { background: var(--cm-bg-tertiary); }
.tree-row.active { background: #EDE9FE; color: #7C3AED; font-weight: var(--cm-font-semibold); }
.tree-row .arrow { font-size: 9px; color: var(--cm-text-tertiary); transition: transform var(--cm-transition-fast); width: 12px; flex-shrink: 0; }
.tree-row .arrow.open { transform: rotate(90deg); }
.tree-ico { flex-shrink: 0; }
.tree-row .tn-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-row .tn-count { font-size: 10px; color: var(--cm-text-tertiary); background: var(--cm-bg-tertiary); padding: 0 6px; border-radius: var(--cm-radius-full); }
.tree-row .tn-saving { font-size: 10px; color: #10B981; font-weight: var(--cm-font-semibold); }
.tree-children { padding-left: 16px; }

.detail-main { flex: 1; padding: 16px 20px; min-width: 0; }
.sum-bar { display: grid; grid-template-columns: 1.6fr 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.sum-item { background: var(--cm-bg-tertiary); border-radius: var(--cm-radius-md); padding: 12px 16px; }
.sum-item .sl { font-size: 11px; color: var(--cm-text-tertiary); margin-bottom: 3px; }
.sum-item .sv { font-size: 16px; font-weight: var(--cm-font-bold); }
.sum-item .sv.blue { color: #3B82F6; }
.sum-item .sv.green { color: #10B981; }
.sum-item .sv.orange { color: #F59E0B; }
.sum-item .sv.view-label { font-size: 14px; color: var(--cm-text-primary); }
.filter-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
.saving-text { color: #10B981; font-weight: var(--cm-font-semibold); }
.muted { color: var(--cm-text-tertiary); }

.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
