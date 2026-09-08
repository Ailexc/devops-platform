<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { graphApi } from '@/api'
import type { AppSummary, Environment } from '@/types'

const route = useRoute()
const router = useRouter()
const app = ref<AppSummary | null>(null)
const envs = ref<Environment[]>([])
const loading = ref(false)

const envTypeColor: Record<string, string> = {
  dev: 'green',
  test: 'blue',
  staging: 'orange',
  prod: 'red',
}

async function loadApp() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const [{ data: apps }, { data: envList }] = await Promise.all([
      graphApi.applications(),
      graphApi.applicationEnvs(id),
    ])
    app.value = apps.find((a) => a.id === id) || null
    envs.value = envList
  } catch {
    message.error('加载应用详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadApp)
</script>

<template>
  <div>
    <a-page-header title="应用详情" @back="router.push('/applications')" />

    <a-spin :spinning="loading">
      <a-card v-if="app" style="margin-bottom: 16px">
        <a-descriptions :column="3" bordered size="small">
          <a-descriptions-item label="应用名称">{{ app.name }}</a-descriptions-item>
          <a-descriptions-item label="所属组织">{{ app.department }}</a-descriptions-item>
          <a-descriptions-item label="负责人">{{ app.owner }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="3">{{ app.description || '-' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card title="🧪 应用环境" size="small">
        <a-row :gutter="[16, 16]">
          <a-col v-for="env in envs" :key="env.id" :xs="24" :sm="12" :lg="8">
            <a-card hoverable @click="router.push(`/environments/${env.id}`)">
              <a-card-meta :title="env.name">
                <template #title>
                  <span>{{ env.name }}</span>
                  <a-tag :color="envTypeColor[env.env_type] || 'default'" style="margin-left: 8px">
                    {{ env.env_type_display }}
                  </a-tag>
                </template>
                <template #description>
                  <p style="min-height: 36px; color: #666">{{ env.description || '暂无描述' }}</p>
                </template>
              </a-card-meta>
              <div style="margin-top: 8px">
                <a-tag>{{ env.account_name || '未绑定账号' }}</a-tag>
                <a-tag>{{ env.region || '-' }}</a-tag>
                <a-tag color="blue">{{ env.services_count }} 服务</a-tag>
              </div>
              <div style="margin-top: 10px; color: #999; font-size: 12px">
                点击查看该环境的资源依赖与上下游
              </div>
            </a-card>
          </a-col>
        </a-row>
        <a-empty v-if="!envs.length" description="该应用暂无环境" />
      </a-card>
    </a-spin>
  </div>
</template>
