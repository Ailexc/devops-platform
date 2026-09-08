<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { TopoEdge } from './types'

const props = defineProps<{
  open: boolean
  edge: TopoEdge | null
  editMode: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'remove'): void
  (e: 'flip'): void
  (e: 'viewDetail'): void
}>()

const router = useRouter()
</script>

<template>
  <a-drawer :open="open" :width="440" title="🔗 依赖关系" @update:open="emit('update:open', $event)">
    <template v-if="edge">
      <a-descriptions :column="2" bordered size="small">
        <a-descriptions-item label="源">{{ edge.source }}</a-descriptions-item>
        <a-descriptions-item label="目标">{{ edge.target }}</a-descriptions-item>
        <a-descriptions-item label="关系类型">{{ edge.relation_type }}</a-descriptions-item>
        <a-descriptions-item label="强度">
          <a-tag :color="edge.strength === 'hard' ? 'purple' : 'default'">
            {{ edge.strength === 'hard' ? '强制' : '软依赖' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="端口/路径" :span="2">{{ edge.label || '-' }}</a-descriptions-item>
      </a-descriptions>

      <a-alert
        v-if="edge.pending"
        type="warning"
        show-icon
        style="margin-top: 12px"
        :message="`⏳ 未接入 / 审批中${edge.pendingInfo?.ticketNo ? `（${edge.pendingInfo.ticketNo}）` : ''}`"
      >
        <template #action v-if="edge.pendingInfo?.ticketNo">
          <a-button size="small" type="link" @click="router.push(`/ticket/detail/${edge.pendingInfo?.ticketId || edge.pendingInfo?.ticketNo}`)">查看工单</a-button>
        </template>
      </a-alert>

      <!-- 查看详情按钮 -->
      <a-button 
        type="primary" 
        block 
        style="margin-top: 16px"
        @click="emit('viewDetail')"
      >
        📋 查看完整关系详情
      </a-button>

      <template v-if="editMode && !edge.pending">
        <a-divider>编辑模式</a-divider>
        <a-space>
          <a-button danger size="small" @click="emit('remove')">🗑 移除该依赖</a-button>
          <a-button size="small" @click="emit('flip')">⇄ 切换依赖强度</a-button>
        </a-space>
        <p style="color: #999; font-size: 12px; margin-top: 8px">
          变更将进入草稿，提交后生成「关系变更工单」，审批通过才落库
        </p>
      </template>
    </template>
  </a-drawer>
</template>
