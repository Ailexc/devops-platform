<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { graphApi, scenarioApi } from '@/api'
import type { Environment, Scenario } from '@/types'
import TopologyCompose from '@/components/topo/TopologyCompose.vue'

const route = useRoute()
const router = useRouter()
const env = ref<Environment | null>(null)
const loading = ref(false)

const scenarioModalVisible = ref(false)
const scenarios = ref<Scenario[]>([])
const submitting = ref(false)
const applyForm = reactive({
  scenario_id: undefined as number | undefined,
  name: '',
  spec: 't3.large',
})

async function loadEnv() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const { data } = await graphApi.envDetail(id)
    env.value = data
  } catch {
    message.error('加载环境详情失败')
  } finally {
    loading.value = false
  }
}

async function openScenario() {
  try {
    const { data } = await scenarioApi.list({ page_size: 50 })
    scenarios.value = data.results || data
    scenarioModalVisible.value = true
  } catch {
    message.error('加载场景模板失败')
  }
}

async function submitScenario() {
  if (!env.value) return
  if (!applyForm.scenario_id || !applyForm.name) {
    message.warning('请选择场景并填写资源名称')
    return
  }
  submitting.value = true
  try {
    const { data } = await scenarioApi.apply(applyForm.scenario_id, {
      title: `${env.value.application_name} ${env.value.name}环境 - ${applyForm.name}`,
      request_content: {
        application_id: env.value.application,
        environment_id: env.value.id,
        name: applyForm.name,
        region: env.value.region,
        spec: applyForm.spec,
      },
    })
    message.success(`场景工单已提交：${data.ticket_no}`)
    scenarioModalVisible.value = false
    router.push(`/ticket/detail/${data.ticket_id}`)
  } catch {
    message.error('提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadEnv)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/applications')
}
</script>

<template>
  <div>
    <a-page-header :title="env ? `${env.application_name} · ${env.name} 环境` : '环境详情'" @back="goBack">
      <template #extra>
        <a-button type="primary" @click="openScenario">🚀 发起业务场景</a-button>
        <a-button @click="loadEnv">🔄 刷新</a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-card v-if="env" style="margin-bottom: 16px">
        <a-descriptions :column="4" bordered size="small">
          <a-descriptions-item label="环境类型">
            <a-tag :color="env.env_type === 'prod' ? 'red' : env.env_type === 'staging' ? 'orange' : env.env_type === 'test' ? 'blue' : 'green'">
              {{ env.env_type_display }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="云账号">{{ env.account_name || '-' }}</a-descriptions-item>
          <a-descriptions-item label="地域">{{ env.region || '-' }}</a-descriptions-item>
          <a-descriptions-item label="服务数">{{ env.services_count }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="4">{{ env.description || '-' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <TopologyCompose :env-id="env?.id" />
    </a-spin>

    <a-modal v-model:open="scenarioModalVisible" title="🚀 发起业务场景" :confirm-loading="submitting" @ok="submitScenario">
      <a-form layout="vertical">
        <a-form-item label="场景模板" required>
          <a-select v-model:value="applyForm.scenario_id" placeholder="选择场景">
            <a-select-option v-for="s in scenarios" :key="s.id" :value="s.id">
              {{ s.icon }} {{ s.name }}（{{ s.step_count }} 步）
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="资源名称" required>
          <a-input v-model:value="applyForm.name" placeholder="如：订单扩容-01" />
        </a-form-item>
        <a-form-item label="规格">
          <a-select v-model:value="applyForm.spec">
            <a-select-option v-for="s in ['t3.medium', 't3.large', 't3.xlarge', 'ecs.g6.2xlarge']" :key="s" :value="s">{{ s }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <a-alert type="info" show-icon :message="`将自动带入「${env?.application_name || ''} / ${env?.name || ''}」环境上下文，提交后进入工单审批`" />
    </a-modal>
  </div>
</template>
