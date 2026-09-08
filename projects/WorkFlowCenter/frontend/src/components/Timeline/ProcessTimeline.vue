<template>
  <div class="process-timeline">
    <el-timeline>
      <el-timeline-item
        v-for="item in timeline"
        :key="item.id"
        :timestamp="item.created_at"
        :type="getTimelineType(item.type)"
        :color="getTimelineColor(item.type)"
        :hollow="item.status !== 'running' && item.status !== 'pending'"
        placement="top"
      >
        <div class="timeline-content">
          <div class="timeline-header">
            <span class="timeline-title">{{ item.title }}</span>
            <el-tag
              :type="getTagType(item.status)"
              size="small"
            >
              {{ getStatusLabel(item.status) }}
            </el-tag>
          </div>
          
          <div class="timeline-info">
            <span class="timeline-user">
              <el-icon><User /></el-icon>
              {{ item.user_name || '系统' }}
            </span>
            <span v-if="item.node_name" class="timeline-node">
              <el-icon><Connection /></el-icon>
              {{ item.node_name }}
            </span>
          </div>
          
          <div v-if="item.comment" class="timeline-comment">
            {{ item.comment }}
          </div>
          
          <div v-if="item.duration" class="timeline-duration">
            耗时：{{ formatDuration(item.duration) }}
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
    
    <div v-if="!timeline.length" class="empty-timeline">
      暂无流程记录
    </div>
  </div>
</template>

<script setup>
import { User, Connection } from '@element-plus/icons-vue'

const props = defineProps({
  timeline: {
    type: Array,
    default: () => []
  }
})

// 获取时间线类型
const getTimelineType = (type) => {
  const types = {
    start: 'primary',
    approve: 'success',
    reject: 'danger',
    delegate: 'warning',
    cc: 'info',
    complete: 'success',
    cancel: 'danger',
    auto_task: 'primary'
  }
  return types[type] || 'primary'
}

// 获取时间线颜色
const getTimelineColor = (type) => {
  const colors = {
    start: '#409eff',
    approve: '#67c23a',
    reject: '#f56c6c',
    delegate: '#e6a23c',
    cc: '#909399',
    complete: '#67c23a',
    cancel: '#f56c6c',
    auto_task: '#409eff'
  }
  return colors[type] || '#409eff'
}

// 获取标签类型
const getTagType = (status) => {
  const types = {
    completed: 'success',
    running: '',
    pending: 'warning',
    rejected: 'danger',
    cancelled: 'info',
    abnormal: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    completed: '已完成',
    running: '进行中',
    pending: '待处理',
    rejected: '已拒绝',
    cancelled: '已取消',
    abnormal: '异常'
  }
  return labels[status] || status || ''
}

// 格式化耗时
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}分${secs > 0 ? secs + '秒' : ''}`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes > 0 ? minutes + '分' : ''}`
  }
}
</script>

<style scoped>
.process-timeline {
  padding: 10px 0;
}

.timeline-content {
  padding: 8px 0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.timeline-title {
  font-weight: bold;
  color: #333;
}

.timeline-info {
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 13px;
  margin-bottom: 8px;
}

.timeline-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.timeline-comment {
  color: #666;
  font-size: 13px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-top: 8px;
}

.timeline-duration {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.empty-timeline {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>