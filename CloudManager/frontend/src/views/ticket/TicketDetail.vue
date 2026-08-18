<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ticketApi } from '@/api'
import type { TicketOrder, TicketApproval, TicketTask } from '@/types'

const route = useRoute()
const router = useRouter()
const ticket = ref<TicketOrder | null>(null)
const approvals = ref<TicketApproval[]>([])
const tasks = ref<TicketTask[]>([])
const loading = ref(false)
const approveModalVisible = ref(false)
const approveAction = ref(1)
const approveComment = ref('')

const statusColors: Record<string, string> = {
  pending: 'orange',
  approving: 'processing',
  executing: 'blue',
  running: 'processing',
  success: 'green',
  failed: 'red',
  rejected: 'volcano',
  cancelled: 'default',
}

async function fetchTicket() {
  loading.value = true
  const id = Number(route.params.id)
  try {
    const [ticketRes, approvalsRes, tasksRes] = await Promise.all([
      ticketApi.get(id),
      ticketApi.getApprovals(id),
      ticketApi.getTasks(id),
    ])
    ticket.value = ticketRes.data
    approvals.value = approvalsRes.data
    tasks.value = tasksRes.data
  } catch {
    message.error('获取工单详情失败')
  } finally {
    loading.value = false
  }
}

function handleApprove(action: number) {
  approveAction.value = action
  approveModalVisible.value = true
}

async function submitApprove() {
  if (!ticket.value) return
  try {
    await ticketApi.approve(ticket.value.id, {
      action: approveAction.value,
      comment: approveComment.value,
    })
    message.success('审批完成')
    approveModalVisible.value = false
    approveComment.value = ''
    fetchTicket()
  } catch {
    message.error('审批失败')
  }
}

async function handleCancel() {
  if (!ticket.value) return
  try {
    await ticketApi.cancel(ticket.value.id)
    message.success('工单已取消')
    fetchTicket()
  } catch {
    message.error('取消失败')
  }
}

onMounted(fetchTicket)
</script>

<template>
  <div>
    <a-page-header title="工单详情" @back="router.push('/ticket/list')" />

    <a-spin :spinning="loading">
      <a-card v-if="ticket" style="margin-bottom: 16px">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="工单号">{{ ticket.ticket_no }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="statusColors[ticket.status]">{{ ticket.status_display }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="类型">{{ ticket.ticket_type_display }}</a-descriptions-item>
          <a-descriptions-item label="申请人">{{ ticket.applicant }}</a-descriptions-item>
          <a-descriptions-item label="标题" :span="2">{{ ticket.title }}</a-descriptions-item>
          <a-descriptions-item label="目标资源">{{ ticket.resource_name || ticket.resource_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="云类型">{{ ticket.provider_type || '-' }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ ticket.created_at }}</a-descriptions-item>
          <a-descriptions-item label="完成时间">{{ ticket.finished_at || '-' }}</a-descriptions-item>
          <a-descriptions-item label="失败原因" :span="2" v-if="ticket.fail_reason">
            <span style="color: #ff4d4f">{{ ticket.fail_reason }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="申请内容" :span="2">
            <pre style="margin: 0; font-size: 12px">{{ JSON.stringify(ticket.request_content, null, 2) }}</pre>
          </a-descriptions-item>
          <a-descriptions-item label="执行结果" :span="2" v-if="ticket.result_content && Object.keys(ticket.result_content).length">
            <pre style="margin: 0; font-size: 12px">{{ JSON.stringify(ticket.result_content, null, 2) }}</pre>
          </a-descriptions-item>
        </a-descriptions>

        <!-- 影响面分析（审批参考） -->
        <a-card
          v-if="ticket?.request_content?.impact_analysis"
          size="small"
          title="⚠️ 变更影响面分析"
          style="margin-top: 16px; border-left: 3px solid #f97316"
        >
          <a-space style="margin-bottom: 8px">
            <a-tag color="red">强影响 {{ ticket.request_content.impact_analysis.summary.high }}</a-tag>
            <a-tag color="orange">中影响 {{ ticket.request_content.impact_analysis.summary.medium }}</a-tag>
            <a-tag color="blue">间接影响 {{ ticket.request_content.impact_analysis.summary.low }}</a-tag>
            <a-tag v-if="ticket.request_content.impact_analysis.summary.spof.length" color="purple">
              单点依赖: {{ ticket.request_content.impact_analysis.summary.spof.join('、') }}
            </a-tag>
          </a-space>
          <a-table
            :columns="[
              { title: '受影响资源', dataIndex: 'name' },
              { title: '关系', dataIndex: 'relation_type' },
              { title: '强度', dataIndex: 'strength' },
              { title: '级别', dataIndex: 'severity' },
            ]"
            :data-source="ticket.request_content.impact_analysis.nodes.slice(0, 10)"
            row-key="id"
            size="small"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'strength'">
                <a-tag :color="record.strength === 'hard' ? 'purple' : 'default'">{{ record.strength === 'hard' ? '强制' : '软' }}</a-tag>
              </template>
              <template v-if="column.dataIndex === 'severity'">
                <a-tag :color="record.severity === 'high' ? 'red' : record.severity === 'medium' ? 'orange' : 'blue'">{{ record.severity }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-card>

        <!-- 操作按钮 -->
        <div style="margin-top: 16px" v-if="['pending', 'approving'].includes(ticket.status)">
          <a-space>
            <a-button type="primary" @click="handleApprove(1)">✅ 同意</a-button>
            <a-button danger @click="handleApprove(2)">❌ 驳回</a-button>
            <a-button @click="handleCancel">取消工单</a-button>
          </a-space>
        </div>
      </a-card>

      <!-- 审批记录 -->
      <a-card title="📝 审批记录" style="margin-bottom: 16px">
        <a-timeline v-if="approvals.length">
          <a-timeline-item
            v-for="item in approvals"
            :key="item.id"
            :color="item.action === 1 ? 'green' : 'red'"
          >
            <p><strong>{{ item.approver }}</strong> - {{ item.action === 1 ? '同意' : '驳回' }}</p>
            <p v-if="item.comment" style="color: #666">{{ item.comment }}</p>
            <p style="color: #999; font-size: 12px">{{ item.approved_at }}</p>
          </a-timeline-item>
        </a-timeline>
        <a-empty v-else description="暂无审批记录" />
      </a-card>

      <!-- 执行任务 -->
      <a-card title="⚙️ 执行任务">
        <a-table
          :columns="[
            { title: '任务类型', dataIndex: 'task_type' },
            { title: '云类型', dataIndex: 'provider_type' },
            { title: '状态', dataIndex: 'status' },
            { title: '重试次数', dataIndex: 'retry_count' },
            { title: '请求ID', dataIndex: 'request_id', ellipsis: true },
            { title: '执行日志', dataIndex: 'exec_log', ellipsis: true },
          ]"
          :data-source="tasks"
          row-key="id"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="statusColors[record.status]">{{ record.status_display }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 场景执行步骤 -->
      <a-card
        v-if="ticket?.ticket_type === 'scenario' && ticket?.result_content?.steps"
        title="🚀 场景执行步骤"
        style="margin-top: 16px"
      >
        <a-timeline>
          <a-timeline-item
            v-for="step in ticket.result_content.steps"
            :key="step.step_no"
            :color="step.status === 'success' ? 'green' : step.status === 'skipped' ? 'blue' : 'red'"
          >
            <p>
              <strong>{{ step.step_no }}. {{ step.name }}</strong>
              <a-tag :color="step.status === 'success' ? 'green' : step.status === 'skipped' ? 'blue' : 'red'" style="margin-left: 8px">
                {{ step.status }}
              </a-tag>
            </p>
            <p v-if="step.result?.message" style="color: #666; font-size: 12px">{{ step.result.message }}</p>
          </a-timeline-item>
        </a-timeline>
      </a-card>

      <!-- 关系变更明细 -->
      <a-card
        v-if="ticket?.ticket_type === 'relation_change'"
        title="🔗 关系变更明细"
        style="margin-top: 16px"
      >
        <a-table
          :columns="[
            { title: '操作', dataIndex: 'action' },
            { title: '源', dataIndex: 'sourceName' },
            { title: '目标', dataIndex: 'targetName' },
            { title: '关系类型', dataIndex: 'relation_type' },
            { title: '强度', dataIndex: 'strength' },
          ]"
          :data-source="(ticket?.request_content?.changes || []).map((c: any, i: number) => ({ ...c, key: i }))"
          row-key="key"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'action'">
              <a-tag :color="record.action === 'add' ? 'green' : record.action === 'remove' ? 'red' : 'blue'">
                {{ record.action === 'add' ? '新增' : record.action === 'remove' ? '移除' : '变更' }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'strength'">
              <a-tag :color="record.strength === 'hard' ? 'purple' : 'default'">{{ record.strength }}</a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'sourceName'">{{ record.source_id }}</template>
            <template v-else-if="column.dataIndex === 'targetName'">{{ record.target_id }}</template>
            <template v-else>{{ record[column.dataIndex] }}</template>
          </template>
        </a-table>
        <a-alert
          v-if="ticket?.result_content?.changes"
          type="success"
          show-icon
          style="margin-top: 12px"
          :message="`执行结果：${ticket.result_content.changes.filter((c: any) => c.ok).length}/${ticket.result_content.changes.length} 项成功`"
        />
      </a-card>
    </a-spin>

    <!-- 审批弹窗 -->
    <a-modal v-model:open="approveModalVisible" :title="approveAction === 1 ? '审批通过' : '审批驳回'" @ok="submitApprove">
      <a-form layout="vertical">
        <a-form-item label="审批意见">
          <a-textarea v-model:value="approveComment" :rows="3" placeholder="请输入审批意见..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
