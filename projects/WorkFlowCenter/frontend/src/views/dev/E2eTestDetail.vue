<template>
  <div class="e2e-detail">
    <div class="page-header">
      <div class="page-header-left">
        <el-button class="back-btn" circle @click="goBack"><el-icon><ArrowLeft /></el-icon></el-button>
        <div>
          <h1>{{ current?.name || '流程测试详情' }}</h1>
          <p class="page-desc">
            <span class="mono">{{ current?.key }}</span>
            <el-tag v-if="current" size="small" effect="plain">{{ current.rules_count }} 条业务规则</el-tag>
          </p>
        </div>
      </div>
    </div>

    <div v-loading="metaLoading" class="detail-body">
      <template v-if="current">
        <!-- 测试场景 -->
        <div class="card">
          <div class="card-head">
            <span class="card-title"><el-icon><Collection /></el-icon> 测试场景</span>
            <span class="card-hint">不同场景对应不同的预设表单与流程走向</span>
          </div>
          <div class="card-body">
            <div class="scenario-list">
              <div
                v-for="s in current.scenarios"
                :key="s.key"
                class="scenario-card"
                :class="{ 'is-active': resultScenarioKey === s.key }"
              >
                <div class="scenario-card__main">
                  <div class="scenario-card__head">
                    <span class="scenario-badge" :class="'scenario-badge--' + s.mode">
                      <span class="scenario-badge__dot"></span>{{ modeMeta(s.mode).label }}
                    </span>
                    <span class="scenario-card__name">{{ s.name }}</span>
                  </div>
                  <p class="scenario-card__desc">{{ s.desc }}</p>
                </div>
                <div class="scenario-card__actions">
                  <el-button size="small" @click="showForm(s)">
                    <el-icon><Document /></el-icon> 查看预设表单
                  </el-button>
                  <el-button size="small" type="primary" :loading="runningKey === s.key" @click="runScenario(s)">
                    <el-icon><Promotion /></el-icon> 开始测试
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 测试结果 -->
        <div v-if="result" class="card">
          <div class="card-head">
            <span class="card-title"><el-icon><VideoPlay /></el-icon> 测试结果</span>
            <div class="card-meta">
              <el-tag size="small" effect="plain">{{ result.scenario?.name }}</el-tag>
              <el-tag v-if="result.instance" size="small" :type="instanceTagType(result.instance.status)">
                {{ result.instance.instance_no }} · {{ result.instance.status_display }}
              </el-tag>
              <el-tag size="small" :type="result.ok ? 'success' : 'warning'">
                {{ result.ok ? '✓ 场景执行成功' : '✕ 未达预期终态' }}
              </el-tag>
            </div>
          </div>
          <div class="card-body">
            <div class="step-list">
              <div v-for="s in result.steps" :key="s.step" class="step-window" :class="{ 'is-fail': !s.ok }">
                <div class="step-window__bar">
                  <span class="step-seq">{{ s.step }}</span>
                  <span class="step-mark" :class="s.ok ? 'ok' : 'fail'">{{ s.ok ? '✓' : '✕' }}</span>
                  <span class="step-action">{{ s.action }}</span>
                  <span class="step-user" v-if="s.user">@{{ s.user }}</span>
                  <span class="step-note" v-if="s.note">{{ s.note }}</span>
                </div>
                <div class="step-window__api">{{ s.method }} {{ s.api }}</div>
                <div class="step-window__cols">
                  <div class="step-col">
                    <div class="step-col__title">请求</div>
                    <pre class="step-json">{{ prettyJson(s.request) }}</pre>
                  </div>
                  <div class="step-col">
                    <div class="step-col__title">响应</div>
                    <pre class="step-json">{{ prettyJson(s.response) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 测试记录 -->
        <div class="card">
          <div class="card-head">
            <span class="card-title"><el-icon><Clock /></el-icon> 测试记录</span>
            <div class="card-head-right">
              <el-radio-group v-model="historyFilter" size="small" @change="loadHistory">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button v-for="s in current.scenarios" :key="s.key" :value="s.key">{{ s.name }}</el-radio-button>
              </el-radio-group>
              <el-button size="small" @click="loadHistory">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>
          <div class="card-body">
            <el-table v-loading="historyLoading" :data="history" empty-text="暂无测试记录，点击上方「开始测试」" style="width: 100%">
              <el-table-column prop="scenario_name" label="场景" min-width="200">
                <template #default="{ row }">
                  <span class="scenario-badge" :class="'scenario-badge--' + row.scenario_mode">
                    <span class="scenario-badge__dot"></span>{{ row.scenario_mode_display }}
                  </span>
                  <span class="hist-scenario-name">{{ row.scenario_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="instance_no" label="实例" min-width="160">
                <template #default="{ row }">
                  <span class="mono">{{ row.instance_no || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="instance_status_display" label="流程状态" width="100" align="center">
                <template #default="{ row }">
                  <span class="status-tag" :class="'status-tag--' + row.instance_status">
                    <span class="status-tag__dot"></span>{{ row.instance_status_display }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="ok" label="结果" width="120" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.ok ? 'success' : 'danger'">{{ row.ok ? '✓ 符合预期' : '✕ 未达预期' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="耗时" width="90" align="center">
                <template #default="{ row }">{{ row.duration_ms ? row.duration_ms + ' ms' : '-' }}</template>
              </el-table-column>
              <el-table-column prop="started_at" label="时间" width="160">
                <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="130" align="center">
                <template #default="{ row }">
                  <el-button v-if="row.instance_id" type="primary" link @click="goInstance(row)">
                    <el-icon><View /></el-icon> 查看详情
                  </el-button>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 预设表单弹窗 -->
        <el-dialog v-model="formDialog" :title="'预设表单 · ' + (formDialogScenario?.name || '')" width="620px">
          <div class="form-dialog-body">
            <p class="form-dialog-desc">{{ formDialogScenario?.desc }}</p>
            <FormRenderer
              v-if="current?.form_schema?.rules?.length"
              v-model="formData"
              :rules="current.form_schema.rules"
              :options="current.form_schema.options || {}"
              :readonly="true"
            />
            <pre v-else class="preset-json">{{ prettyJson(formDialogScenario?.preset_form) }}</pre>
          </div>
        </el-dialog>
      </template>
      <el-empty v-else-if="!metaLoading" description="未找到该流程" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Promotion, Document, VideoPlay, Clock, Refresh, View, Collection } from '@element-plus/icons-vue'
import { getE2eMeta, runE2e, getE2eHistory } from '@/api/modules/process'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'

const MODE_META = {
  completed: { label: '正常完成', tag: 'success' },
  running: { label: '进行中', tag: 'primary' },
  abnormal: { label: '异常', tag: 'danger' },
  rejected: { label: '驳回', tag: 'warning' },
}

const route = useRoute()
const router = useRouter()

const flows = ref([])
const metaLoading = ref(false)
const runningKey = ref('')
const result = ref(null)
const resultScenarioKey = ref('')
const history = ref([])
const historyLoading = ref(false)
const historyFilter = ref('')
const formDialog = ref(false)
const formDialogScenario = ref(null)
const formData = ref({})

const current = computed(() => flows.value.find(f => f.key === route.params.key))

const modeMeta = (mode) => MODE_META[mode] || { label: mode, tag: 'info' }

const instanceTagType = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'running') return 'primary'
  return 'warning'
}

const prettyJson = (obj) => {
  try {
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return String(obj)
  }
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const goBack = () => router.push('/dev/e2e-test')
const goInstance = (row) => router.push(`/my/applications/${row.instance_id}`)

const loadMeta = async () => {
  metaLoading.value = true
  try {
    const response = await getE2eMeta()
    flows.value = response?.data ?? response ?? []
  } catch (error) {
    console.error('获取测试流程失败:', error)
    ElMessage.error('获取测试流程失败')
  } finally {
    metaLoading.value = false
  }
}

const runScenario = async (scenario) => {
  if (!current.value) return
  runningKey.value = scenario.key
  try {
    const response = await runE2e({ definition_id: current.value.id, scenario_key: scenario.key })
    const data = response?.data ?? response
    result.value = data
    resultScenarioKey.value = scenario.key
    if (data?.ok) {
      ElMessage.success(`「${scenario.name}」执行成功（实例 ${data.instance?.instance_no || ''} · ${data.instance?.status_display || ''}）`)
    } else {
      ElMessage.warning(`「${scenario.name}」执行完成，但未达到预期终态`)
    }
    loadHistory()
  } catch (error) {
    console.error('场景测试失败:', error)
    ElMessage.error('场景测试调用失败')
  } finally {
    runningKey.value = ''
  }
}

const showForm = (scenario) => {
  formDialogScenario.value = scenario
  formData.value = JSON.parse(JSON.stringify(scenario.preset_form || {}))
  formDialog.value = true
}

const loadHistory = async () => {
  if (!current.value) return
  historyLoading.value = true
  try {
    const params = { definition_id: current.value.id }
    if (historyFilter.value) params.scenario_key = historyFilter.value
    const response = await getE2eHistory(params)
    const data = response?.data ?? response
    history.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取测试记录失败:', error)
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  await loadMeta()
  loadHistory()
})
</script>

<style scoped>
.e2e-detail { padding: 24px; background: #f7f8fa; min-height: 100%; max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.page-header h1 { margin: 0 0 4px; font-size: 20px; color: #1d2129; }
.back-btn { flex-shrink: 0; }
.page-desc { margin: 0; display: flex; align-items: center; gap: 8px; }
.mono { font-family: ui-monospace, monospace; font-size: 12px; color: #86909c; }

.detail-body { display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border: 1px solid #e5e6eb; border-radius: 12px; overflow: hidden; }
.card-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid #f2f3f5; gap: 10px; flex-wrap: wrap; }
.card-title { font-size: 15px; font-weight: 600; color: #1d2129; display: flex; align-items: center; gap: 6px; }
.card-hint { font-size: 12px; color: #86909c; }
.card-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.card-head-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.card-body { padding: 18px; }
.preset-json { font-size: 12px; background: #f7f8fa; border-radius: 6px; padding: 12px; color: #4e5969; line-height: 1.6; white-space: pre-wrap; word-break: break-all; margin: 0; }

/* 测试场景卡片 */
.scenario-list { display: flex; flex-direction: column; gap: 12px; }
.scenario-card { display: flex; justify-content: space-between; align-items: center; gap: 16px; border: 1px solid #e5e6eb; border-radius: 10px; padding: 14px 16px; background: #fbfbfc; transition: all .2s; flex-wrap: wrap; }
.scenario-card.is-active { border-color: #409eff; background: #f0f7ff; box-shadow: 0 0 0 3px rgba(64,158,255,.1); }
.scenario-card__main { flex: 1; min-width: 240px; }
.scenario-card__head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.scenario-card__name { font-size: 15px; font-weight: 600; color: #1d2129; }
.scenario-card__desc { margin: 0; font-size: 12px; color: #86909c; line-height: 1.6; }
.scenario-card__actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }

.scenario-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; padding: 2px 9px; border-radius: 6px; border: 1px solid #e5e6eb; background: #f7f8fa; color: #4e5969; flex-shrink: 0; }
.scenario-badge__dot { width: 6px; height: 6px; border-radius: 50%; background: #c9cdd4; }
.scenario-badge--completed { color: #00b42a; border-color: #b7eb8f; background: #f2fdf5; }
.scenario-badge--completed .scenario-badge__dot { background: #00b42a; }
.scenario-badge--running { color: #165dff; border-color: #a0cfff; background: #f0f7ff; }
.scenario-badge--running .scenario-badge__dot { background: #165dff; }
.scenario-badge--abnormal { color: #f53f3f; border-color: #f3c1c1; background: #fff4f4; }
.scenario-badge--abnormal .scenario-badge__dot { background: #f53f3f; }
.scenario-badge--rejected { color: #ff7d00; border-color: #ffd091; background: #fff9ef; }
.scenario-badge--rejected .scenario-badge__dot { background: #ff7d00; }
.hist-scenario-name { font-size: 13px; color: #1d2129; margin-left: 8px; }

.step-list { display: flex; flex-direction: column; gap: 12px; }
.step-window { border: 1px solid #e5e6eb; border-radius: 8px; background: #fbfbfc; overflow: hidden; }
.step-window.is-fail { border-color: #f3c1c1; background: #fffbfa; }
.step-window__bar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f7f8fa; border-bottom: 1px solid #f2f3f5; flex-wrap: wrap; }
.step-seq { width: 22px; height: 22px; border-radius: 50%; background: #409eff; color: #fff; font-size: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-mark.ok { color: #00b42a; font-weight: 700; }
.step-mark.fail { color: #f53f3f; font-weight: 700; }
.step-action { font-weight: 600; font-size: 13px; color: #1d2129; }
.step-user { font-size: 12px; color: #722ed1; background: #f4f0ff; border-radius: 4px; padding: 1px 6px; }
.step-note { font-size: 12px; color: #86909c; }
.step-window__api { font-family: ui-monospace, monospace; font-size: 12px; color: #165dff; padding: 8px 12px; background: #f2f7ff; }
.step-window__cols { display: flex; gap: 0; }
.step-col { flex: 1; min-width: 0; padding: 10px 12px; border-right: 1px solid #f2f3f5; }
.step-col:last-child { border-right: none; }
.step-col__title { font-size: 12px; color: #86909c; margin-bottom: 6px; font-weight: 600; }
.step-json { font-size: 11px; color: #4e5969; background: #fff; border-radius: 4px; padding: 8px; max-height: 200px; overflow: auto; line-height: 1.5; white-space: pre-wrap; word-break: break-all; margin: 0; }

.status-tag { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; }
.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; background: #c9cdd4; }
.status-tag--running .status-tag__dot { background: #409eff; }
.status-tag--completed .status-tag__dot { background: #00b42a; }
.status-tag--terminated .status-tag__dot { background: #f53f3f; }
.status-tag--suspended .status-tag__dot { background: #ff7d00; }
.status-tag--running { color: #409eff; }
.status-tag--completed { color: #00b42a; }
.status-tag--terminated { color: #f53f3f; }
.status-tag--suspended { color: #ff7d00; }

.form-dialog-body { padding: 4px 2px; }
.form-dialog-desc { margin: 0 0 14px; font-size: 13px; color: #86909c; line-height: 1.6; }
</style>
