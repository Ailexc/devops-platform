<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { scenarioApi } from '@/api'
import type { Scenario } from '@/types'

const router = useRouter()
const scenarios = ref<Scenario[]>([])
const loading = ref(false)

async function loadScenarios() {
  loading.value = true
  try {
    const { data } = await scenarioApi.list({ page_size: 50 })
    scenarios.value = data.results || data
  } catch {
    message.error('加载场景列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadScenarios)
</script>

<template>
  <div>
    <a-page-header title="🧩 场景中心" sub-title="将多个原子操作组合为场景，一键发起、编排执行、标准化审批" />

    <a-spin :spinning="loading">
      <a-row :gutter="[16, 16]">
        <a-col v-for="sc in scenarios" :key="sc.id" :xs="24" :sm="12" :lg="8">
          <a-card hoverable @click="router.push(`/scenarios/${sc.id}`)">
            <a-card-meta>
              <template #title>
                <span style="font-size: 16px">{{ sc.icon }} {{ sc.name }}</span>
                <a-tag color="purple" style="margin-left: 8px">{{ sc.version }}</a-tag>
              </template>
              <template #description>
                <p style="min-height: 44px; color: #666">{{ sc.description || '暂无描述' }}</p>
              </template>
            </a-card-meta>
            <a-space style="margin-top: 12px">
              <a-tag color="blue">共 {{ sc.step_count }} 个步骤</a-tag>
              <a-tag :color="sc.need_approval ? 'orange' : 'green'">
                {{ sc.need_approval ? '需审批' : '免审批' }}
              </a-tag>
              <a-tag :color="sc.enabled ? 'green' : 'default'">{{ sc.enabled ? '启用中' : '已停用' }}</a-tag>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="!loading && !scenarios.length" description="暂无场景" />
    </a-spin>
  </div>
</template>
