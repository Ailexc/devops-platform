<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ticketApi } from '@/api'
import type { TicketOrder } from '@/types'

const loading = ref(false)
const logs = ref<TicketOrder[]>([])
const total = ref(0)
const currentPage = ref(1)

async function fetchLogs() {
  loading.value = true
  try {
    const { data } = await ticketApi.list({
      page: currentPage.value,
      page_size: 20,
    })
    logs.value = data.results
    total.value = data.count
  } catch {
    // handle silently
  } finally {
    loading.value = false
  }
}

const statusColors: Record<string, string> = {
  success: 'green',
  failed: 'red',
  rejected: 'volcano',
  cancelled: 'default',
  pending: 'orange',
  executing: 'blue',
  running: 'processing',
}

onMounted(fetchLogs)
</script>

<template>
  <a-card title="📝 操作记录（提单记录）">
    <a-table
      :columns="[
        { title: '工单号', dataIndex: 'ticket_no', width: 160 },
        { title: '类型', dataIndex: 'ticket_type_display', width: 120 },
        { title: '标题', dataIndex: 'title', ellipsis: true },
        { title: '状态', dataIndex: 'status', width: 100 },
        { title: '申请人', dataIndex: 'applicant', width: 100 },
        { title: '创建时间', dataIndex: 'created_at', width: 170 },
        { title: '完成时间', dataIndex: 'finished_at', width: 170 },
      ]"
      :data-source="logs"
      :loading="loading"
      :pagination="{ current: currentPage, total, onChange: (p: number) => { currentPage = p; fetchLogs() }, showTotal: (t: number) => `共 ${t} 条` }"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'status'">
          <a-tag :color="statusColors[record.status]">{{ record.status_display }}</a-tag>
        </template>
      </template>
    </a-table>
  </a-card>
</template>
