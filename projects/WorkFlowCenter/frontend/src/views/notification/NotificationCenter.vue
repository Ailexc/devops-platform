<template>
  <div class="notification-center">
    <div class="page-header">
      <h2>通知中心</h2>
      <div class="header-actions">
        <el-button v-if="hasUnread" @click="markAllRead">
          <el-icon><Check /></el-icon>
          全部已读
        </el-button>
      </div>
    </div>

    <!-- 类型筛选 -->
    <el-tabs v-model="activeType" @tab-change="fetchData">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="未读" name="unread" />
      <el-tab-pane label="任务通知" name="task" />
      <el-tab-pane label="工单通知" name="ticket" />
      <el-tab-pane label="审批通知" name="approval" />
      <el-tab-pane label="系统通知" name="system" />
    </el-tabs>

    <!-- 列表 -->
    <el-card>
      <!-- 即将支持的功能提示 -->
      <el-alert
        title="邮件 / IM 通知"
        description="邮件通知（SMTP）和企业微信/钉钉/飞书 IM 推送即将上线。届时可在此配置通知渠道，实现审批提醒自动推送。当前版本仅支持站内通知。"
        type="info"
        show-icon
        :closable="true"
        style="margin-bottom: 16px;"
      />
      <div v-loading="loading" class="notification-list">
        <div
          v-for="item in tableData"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="markRead(item)"
        >
          <el-icon class="notify-icon" :class="typeClass(item.type)">
            <component :is="typeIcon(item.type)" />
          </el-icon>
          <div class="notify-content">
            <div class="notify-title">
              {{ item.title }}
              <el-tag v-if="!item.is_read" size="small" type="danger" effect="light" class="unread-tag">未读</el-tag>
            </div>
            <div class="notify-text">{{ item.content }}</div>
            <div class="notify-time">{{ item.created_at }}</div>
          </div>
        </div>

        <el-empty v-if="!loading && tableData.length === 0" description="暂无通知" />
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Bell, Tickets, Finished, Setting, ChatDotRound } from '@element-plus/icons-vue'
import {
  getNotifications, markNotificationRead, markAllNotificationsRead
} from '@/api/modules/notifications'

const loading = ref(false)
const tableData = ref([])
const activeType = ref('all')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const hasUnread = computed(() => tableData.value.some(n => !n.is_read))

const fetchData = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (activeType.value === 'unread') {
      params.is_read = 'false'
    } else if (activeType.value !== 'all') {
      params.type = activeType.value
    }
    const response = await getNotifications(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取通知失败:', error)
  } finally {
    loading.value = false
  }
}

const markRead = async (item) => {
  if (item.is_read) return
  try {
    await markNotificationRead(item.id)
    item.is_read = true
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const markAllRead = async () => {
  try {
    await markAllNotificationsRead()
    tableData.value.forEach(n => { n.is_read = true })
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('标记失败:', error)
  }
}

const typeIcon = (type) => {
  const icons = {
    task: Finished,
    ticket: Tickets,
    approval: ChatDotRound,
    system: Setting
  }
  return icons[type] || Bell
}

const typeClass = (type) => {
  const classes = {
    task: 'type-task',
    ticket: 'type-ticket',
    approval: 'type-approval',
    system: 'type-system'
  }
  return classes[type] || 'type-default'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.notification-center {
  padding: 20px;
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h2 {
    margin: 0;
    color: var(--text-primary, #1D2129);
    font-size: 20px;
  }
}

.page-header-icon {
  width: 40px; height: 40px; border-radius: 8px;
  background: linear-gradient(135deg, #409EFF, #66B1FF);
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px;
}
.page-header h1 {
  font-size: 22px; font-weight: 700; color: var(--text-primary, #1D2129); margin: 0;
}
.page-header-desc {
  font-size: 13px; color: var(--text-secondary, #86909C); margin: 2px 0 0;
}

.notification-list {
  min-height: 300px;

  .notification-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 16px;
    border-bottom: 1px solid #f0f2f5;
    cursor: pointer;
    transition: background 0.2s;
    border-radius: 8px;

    &:hover {
      background: #f5f7fa;
    }

    &.unread {
      background: #f0f7ff;

      &:hover {
        background: #e6f2ff;
      }
    }

    .notify-icon {
      font-size: 22px;
      margin-top: 2px;

      &.type-task {
        color: #409eff;
      }

      &.type-ticket {
        color: #67c23a;
      }

      &.type-approval {
        color: #e6a23c;
      }

      &.type-system {
        color: #909399;
      }

      &.type-default {
        color: #909399;
      }
    }

    .notify-content {
      flex: 1;

      .notify-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .notify-text {
        font-size: 13px;
        color: #606266;
        margin-bottom: 4px;
        line-height: 1.5;
      }

      .notify-time {
        font-size: 12px;
        color: #c0c4cc;
      }
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
