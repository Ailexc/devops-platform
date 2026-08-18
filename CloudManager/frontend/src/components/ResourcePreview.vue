<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { resourceApi, graphApi } from '@/api'
import type { Resource } from '@/types'

const props = defineProps<{
  resourceId: number
}>()

const emit = defineEmits<{ (e: 'close'): void }>()
const router = useRouter()
const resource = ref<Resource | null>(null)
const relationCount = ref(0)
const loading = ref(false)

async function loadPreview() {
  if (!props.resourceId) return
  loading.value = true
  try {
    const [res, nb] = await Promise.all([
      resourceApi.get(props.resourceId),
      graphApi.neighbors(props.resourceId),
    ])
    resource.value = res.data
    relationCount.value = nb.data.edges.length
  } catch {
    message.error('加载资源预览失败')
  } finally {
    loading.value = false
  }
}

function openDetail() {
  router.push(`/resources/${props.resourceId}`)
}

watch(() => props.resourceId, loadPreview)
onMounted(loadPreview)
</script>

<template>
  <a-card size="small" style="margin-top: 12px; border-left: 3px solid #10B981">
    <template #title>
      <span>🔍 资源预览：{{ resource?.resource_name || '加载中...' }}</span>
    </template>
    <template #extra>
      <a-space>
        <a-button size="small" type="primary" @click="openDetail">查看完整详情</a-button>
        <a-button size="small" @click="emit('close')">关闭</a-button>
      </a-space>
    </template>
    <a-spin :spinning="loading">
      <a-descriptions v-if="resource" :column="4" size="small">
        <a-descriptions-item label="资源ID">{{ resource.cloud_resource_id }}</a-descriptions-item>
        <a-descriptions-item label="类型">{{ resource.resource_type_display }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="resource.status === 'running' ? 'green' : resource.status === 'stopped' ? 'red' : 'blue'">
            {{ resource.status }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="关联关系">{{ relationCount }} 条</a-descriptions-item>
        <a-descriptions-item label="规格">{{ resource.spec || '-' }}</a-descriptions-item>
        <a-descriptions-item label="地域">{{ resource.region }}</a-descriptions-item>
        <a-descriptions-item label="云账号">{{ resource.account_name }}</a-descriptions-item>
        <a-descriptions-item label="所属环境">{{ resource.environment_name || '-' }}</a-descriptions-item>
      </a-descriptions>
    </a-spin>
  </a-card>
</template>
