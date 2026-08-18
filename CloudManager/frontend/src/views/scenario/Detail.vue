<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { scenarioApi, graphApi } from '@/api'
import type { Scenario, AppSummary, Environment } from '@/types'

const route = useRoute()
const router = useRouter()
const scenario = ref<Scenario | null>(null)
const apps = ref<AppSummary[]>([])
const appEnvs = ref<Environment[]>([])
const loading = ref(false)
const applyVisible = ref(false)
const submitting = ref(false)

const applyForm = reactive({
  application_id: undefined as number | undefined,
  environment_id: undefined as number | undefined,
  name: '',
  region: 'cn-hangzhou',
  spec: 't3.large',
})

async function loadScenario() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const [sc, appRes] = await Promise.all([
      scenarioApi.get(id),
      graphApi.applications(),
    ])
    scenario.value = sc.data
    apps.value = appRes.data
    const first = apps.value[0]
    if (first) applyForm.application_id = first.id
    await loadEnvs()
  } catch {
    message.error('加载场景详情失败')
  } finally {
    loading.value = false
  }
}

async function loadEnvs() {
  if (!applyForm.application_id) {
    appEnvs.value = []
    return
  }
  try {
    const { data } = await graphApi.applicationEnvs(applyForm.application_id)
    appEnvs.value = data
    const first = data[0]
    if (first) {
      applyForm.environment_id = first.id
      applyForm.region = first.region || applyForm.region
    }
  } catch {
    appEnvs.value = []
  }
}

watch(() => applyForm.application_id, loadEnvs)

function openApply() {
  applyVisible.value = true
}

async function submitApply() {
  if (!scenario.value) return
  if (!applyForm.application_id || !applyForm.environment_id || !applyForm.name) {
    message.warning('请填写应用、环境与资源名称')
    return
  }
  submitting.value = true
  try {
    const { data } = await scenarioApi.apply(scenario.value.id, {
      title: `${scenario.value.name} - ${applyForm.name}`,
      request_content: { ...applyForm },
    })
    message.success(`场景工单已提交：${data.ticket_no}`)
    applyVisible.value = false
    router.push(`/ticket/detail/${data.ticket_id}`)
  } catch {
    message.error('提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadScenario)
</script>

<template>
  <div>
    <a-page-header title="场景详情" @back="router.push('/scenarios')">
      <template #extra>
        <a-button v-if="scenario?.enabled" type="primary" @click="openApply">🚀 发起场景</a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-card v-if="scenario" style="margin-bottom: 16px">
        <a-descriptions :column="3" bordered size="small">
          <a-descriptions-item label="场景名称">{{ scenario.icon }} {{ scenario.name }}</a-descriptions-item>
          <a-descriptions-item label="编码">{{ scenario.code }}</a-descriptions-item>
          <a-descriptions-item label="版本">{{ scenario.version }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ scenario.description || '-' }}</a-descriptions-item>
          <a-descriptions-item label="审批">
            <a-tag :color="scenario.need_approval ? 'orange' : 'green'">
              {{ scenario.need_approval ? '需要审批' : '免审批' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card title="⚙️ 场景步骤编排">
        <a-steps v-if="scenario" :current="scenario.steps.length - 1" direction="vertical" size="small">
          <a-step
            v-for="step in scenario.steps"
            :key="step.id"
            :title="`${step.step_no}. ${step.name}`"
            :description="`操作: ${step.action_type}${step.depends_on?.length ? ' | 依赖步骤: ' + step.depends_on.join(', ') : ''}${step.need_approval ? ' | 步骤需审批' : ''} | 重试上限: ${step.retry_max}`"
            :status="'finish'"
          />
        </a-steps>
      </a-card>
    </a-spin>

    <a-modal v-model:open="applyVisible" :title="`发起 ${scenario?.name || ''}`" :confirm-loading="submitting" @ok="submitApply">
      <a-form layout="vertical">
        <a-form-item label="目标应用" required>
          <a-select v-model:value="applyForm.application_id" placeholder="选择应用">
            <a-select-option v-for="a in apps" :key="a.id" :value="a.id">{{ a.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="目标环境" required>
          <a-select v-model:value="applyForm.environment_id" placeholder="选择环境">
            <a-select-option v-for="e in appEnvs" :key="e.id" :value="e.id">
              {{ e.name }}（{{ e.env_type_display }} · {{ e.region || '-' }}）
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="资源名称" required>
          <a-input v-model:value="applyForm.name" placeholder="如：订单服务扩容-01" />
        </a-form-item>
        <a-form-item label="地域">
          <a-select v-model:value="applyForm.region">
            <a-select-option v-for="r in ['cn-hangzhou', 'cn-shanghai', 'cn-beijing', 'us-east-1']" :key="r" :value="r">{{ r }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="规格">
          <a-select v-model:value="applyForm.spec">
            <a-select-option v-for="s in ['t3.medium', 't3.large', 't3.xlarge', 'ecs.g6.2xlarge']" :key="s" :value="s">{{ s }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <a-alert type="info" show-icon message="提交后将进入标准化审批流程，审批通过后按步骤自动编排执行" />
    </a-modal>
  </div>
</template>
