<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resourceApi } from '@/api'
import type { Resource } from '@/types'
import { useGlobalStore } from '@/stores/global'

const globalStore = useGlobalStore()
const loading = ref(false)
const resources = ref<Resource[]>([])
const total = ref(0)
const currentPage = ref(1)

async function fetchResources() {
  loading.value = true
  try {
    const { data } = await resourceApi.list({
      resource_type: 'vpc',
      page: currentPage.value,
      page_size: 20,
      region: globalStore.region || undefined,
      account: globalStore.accountId || undefined,
    })
    resources.value = data.results
    total.value = data.count
  } catch {
    // handle silently
  } finally {
    loading.value = false
  }
}

onMounted(fetchResources)
</script>

<template>
  <a-card title="🌐 网络 (VPC)">
    <a-table
      :columns="[
        { title: 'VPC 名称', dataIndex: 'resource_name' },
        { title: 'VPC ID', dataIndex: 'cloud_resource_id' },
        { title: '地域', dataIndex: 'region' },
        { title: '状态', dataIndex: 'status' },
        { title: 'CIDR', key: 'cidr' },
        { title: '云账号', dataIndex: 'account_name' },
      ]"
      :data-source="resources"
      :loading="loading"
      :pagination="{ current: currentPage, total, onChange: (p: number) => { currentPage = p; fetchResources() }, showTotal: (t: number) => `共 ${t} 条` }"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'cidr'">
          {{ record.metadata?.cidr_block || '-' }}
        </template>
        <template v-if="column.dataIndex === 'status'">
          <a-tag color="green">{{ record.status }}</a-tag>
        </template>
      </template>
    </a-table>
  </a-card>
</template>
