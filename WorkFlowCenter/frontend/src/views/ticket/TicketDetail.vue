<template>
  <div class="ticket-detail">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </div>
        <div>
          <h1>{{ ticket.title || '工单详情' }}</h1>
          <p class="page-header-desc">
            {{ ticket.ticket_no }} · {{ ticket.definition_name }}
          </p>
        </div>
      </div>
    </div>

    <!-- 状态条 -->
    <div class="status-bar">
      <div class="status-bar-left">
        <span class="status-tag" :class="'status-tag--' + ticket.status">
          <span class="status-tag__dot"></span>
          {{ getStatusLabel(ticket.status) }}
        </span>
        <template v-if="ticket.priority">
          <span class="priority-bar" :class="'priority-bar--' + ticket.priority"></span>
          <span class="priority-text" :class="'priority-text--' + ticket.priority">
            {{ getPriorityLabel(ticket.priority) }}优先级
          </span>
        </template>
      </div>
      <div class="status-bar-meta">
        <span><el-icon><User /></el-icon> {{ ticket.created_by || '-' }}</span>
        <span><el-icon><Clock /></el-icon> {{ formatTime(ticket.created_at) }}</span>
      </div>
      <div class="status-bar-actions" v-if="showActions">
        <el-button type="success" @click="openDrawer('approve')">
          <el-icon><Check /></el-icon> 通过
        </el-button>
        <el-button type="danger" @click="openDrawer('reject')">
          <el-icon><Close /></el-icon> 拒绝
        </el-button>
        <el-button @click="openDrawer('delegate')">
          <el-icon><Switch /></el-icon> 转办
        </el-button>
      </div>
    </div>

    <!-- 两栏布局 -->
    <div class="detail-layout">
      <!-- 左侧：主内容 -->
      <div class="detail-main">
        <div class="card">
          <!-- Tabs -->
          <div class="tabs">
            <div
              class="tab"
              :class="{ active: activeTab === 'basic' }"
              @click="activeTab = 'basic'"
            >
              <el-icon><Document /></el-icon> 基本信息
            </div>
            <div
              class="tab"
              :class="{ active: activeTab === 'timeline' }"
              @click="activeTab = 'timeline'"
            >
              <el-icon><Clock /></el-icon> 流程追踪
            </div>
            <div
              class="tab"
              :class="{ active: activeTab === 'comments' }"
              @click="activeTab = 'comments'"
            >
              <el-icon><ChatDotRound /></el-icon> 评论
              <span v-if="comments.length" class="tab-badge">{{ comments.length }}</span>
            </div>
          </div>

          <!-- Tab: 基本信息 -->
          <div v-show="activeTab === 'basic'" class="tab-content">
            <div class="card-body">
              <div class="desc-grid">
                <div class="desc-item desc-item--full">
                  <span class="desc-label">工单标题</span>
                  <span class="desc-value">{{ ticket.title }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">流程模版</span>
                  <span class="desc-value">{{ ticket.definition_name }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">工单编号</span>
                  <span class="desc-value desc-value--mono">{{ ticket.ticket_no }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">优先级</span>
                  <span class="desc-value">
                    <span class="priority-bar" :class="'priority-bar--' + ticket.priority"></span>
                    {{ getPriorityLabel(ticket.priority) }}
                  </span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">创建人</span>
                  <span class="desc-value">{{ ticket.created_by }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">创建时间</span>
                  <span class="desc-value">{{ ticket.created_at }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">更新时间</span>
                  <span class="desc-value">{{ ticket.updated_at }}</span>
                </div>
              </div>
            </div>

            <!-- 表单数据 -->
            <div v-if="ticket.form_data && Object.keys(ticket.form_data).length" class="card-body card-body--bordered">
              <div class="section-title">
                <span class="section-title__bar"></span>
                表单数据
              </div>
              <FormRenderer
                v-model="ticket.form_data"
                :rules="ticket.form_schema?.rules || []"
                :options="ticket.form_schema?.options || {}"
                :readonly="true"
              />
            </div>
          </div>

          <!-- Tab: 流程追踪 -->
          <div v-show="activeTab === 'timeline'" class="tab-content">
            <div class="card-body">
              <FlowNodeStatus :instance-id="route.params.id" />
            </div>
          </div>

          <!-- Tab: 评论 -->
          <div v-show="activeTab === 'comments'" class="tab-content">
            <div class="card-body">
              <div v-if="comments.length === 0" class="empty-comments">
                <div class="empty-comments__icon">
                  <el-icon :size="40"><ChatDotRound /></el-icon>
                </div>
                <p>暂无评论</p>
                <p class="empty-comments__hint">输入你的评论开始讨论</p>
              </div>
              <div v-else class="comment-list">
                <div
                  v-for="comment in comments"
                  :key="comment.id"
                  class="comment-bubble"
                  :class="{ 'comment-bubble--self': isCurrentUser(comment.created_by) }"
                >
                  <div class="comment-avatar" :class="'comment-avatar--' + getAvatarColor(comment.created_by)">
                    {{ (comment.created_by || '?').charAt(0) }}
                  </div>
                  <div class="comment-bubble-content">
                    <div class="comment-bubble-meta">
                      <span class="comment-bubble-name">{{ comment.created_by }}</span>
                      <span class="comment-bubble-time">{{ formatTime(comment.created_at) }}</span>
                    </div>
                    <div class="comment-bubble-box">
                      {{ comment.content }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="comment-input-area">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="2"
                placeholder="输入评论内容..."
                resize="none"
              />
              <el-button
                type="primary"
                @click="addComment"
                :loading="commentLoading"
                :disabled="!newComment.trim()"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：侧边信息 -->
      <div class="detail-aside">
        <!-- 操作历史 -->
        <div class="card aside-card">
          <div class="card-header">
            <span><el-icon><List /></el-icon> 操作历史</span>
          </div>
          <div class="card-body card-body--compact">
            <div class="mini-timeline">
              <div
                v-for="(item, index) in operationHistory"
                :key="index"
                class="mini-timeline-item"
              >
                <div class="mini-timeline-dot" :class="'mini-timeline-dot--' + (item.type || 'default')">
                  <el-icon :size="12"><component :is="item.icon" /></el-icon>
                </div>
                <div class="mini-timeline-content">
                  <div class="mini-timeline-title">{{ item.title }}</div>
                  <div class="mini-timeline-time">{{ item.time }}</div>
                </div>
              </div>
              <div v-if="!operationHistory.length" class="empty-tip">暂无操作记录</div>
            </div>
          </div>
        </div>

        <!-- 参与人 -->
        <div class="card aside-card">
          <div class="card-header">
            <span><el-icon><User /></el-icon> 参与人</span>
          </div>
          <div class="card-body card-body--compact">
            <div class="participant-list">
              <div class="participant-item">
                <div class="participant-avatar participant-avatar--green">
                  {{ (ticket.created_by || '?').charAt(0) }}
                </div>
                <div class="participant-info">
                  <div class="participant-name">{{ ticket.created_by }}</div>
                  <div class="participant-role">发起人</div>
                </div>
              </div>
              <div v-for="p in participants" :key="p.name" class="participant-item">
                <div class="participant-avatar" :class="'participant-avatar--' + p.color">
                  {{ p.name.charAt(0) }}
                </div>
                <div class="participant-info">
                  <div class="participant-name">{{ p.name }}</div>
                  <div class="participant-role">{{ p.role }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerConfig.title"
      direction="rtl"
      size="420px"
      :before-close="closeDrawer"
    >
      <div class="drawer-content">
        <!-- 确认提示 -->
        <div class="action-confirm" :class="'action-confirm--' + drawerConfig.type">
          <div class="action-confirm-icon" :class="'action-confirm-icon--' + drawerConfig.type">
            <el-icon :size="20"><component :is="drawerConfig.icon" /></el-icon>
          </div>
          <div>
            <div class="action-confirm-title">{{ drawerConfig.confirmTitle }}</div>
            <div class="action-confirm-desc">{{ drawerConfig.confirmDesc }}</div>
          </div>
        </div>

        <!-- 处理意见 -->
        <div class="drawer-form-group">
          <label class="drawer-form-label">
            处理意见 <span class="required">*</span>
          </label>
          <el-input
            v-model="actionForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="drawerConfig.commentPlaceholder"
            resize="none"
          />
        </div>

        <!-- 转办人（仅转办时显示） -->
        <div v-if="drawerConfig.type === 'delegate'" class="drawer-form-group">
          <label class="drawer-form-label">
            转办给 <span class="required">*</span>
          </label>
          <el-select v-model="actionForm.assignee" placeholder="请选择转办人" style="width: 100%">
            <el-option label="王五 — IT 部门" value="wangwu" />
            <el-option label="赵六 — 运维组" value="zhaoliu" />
            <el-option label="钱七 — 架构组" value="qianqi" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="closeDrawer">取消</el-button>
          <el-button
            :type="drawerConfig.buttonType"
            :loading="drawerLoading"
            @click="submitAction"
          >
            {{ drawerConfig.buttonText }}
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTicketDetail, addComment as addCommentApi } from '@/api/modules/ticket'
import { getTimeline } from '@/api/modules/process'
import { completeTask, rejectTask, delegateTask } from '@/api/modules/task'
import FlowNodeStatus from '@/components/ticket/FlowNodeStatus.vue'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'
import {
  ArrowLeft, User, Clock, Document, ChatDotRound, List,
  Check, Close, Switch, Plus
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const ticket = ref({})
const timeline = ref([])
const comments = ref([])
const newComment = ref('')
const commentLoading = ref(false)
const activeTab = ref('basic')

// 操作抽屉
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const currentAction = ref('')

const drawerConfig = computed(() => {
  const configs = {
    approve: {
      type: 'approve',
      title: '审批通过',
      icon: 'Check',
      confirmTitle: '确认通过此工单？',
      confirmDesc: '通过后将流转至下一步骤',
      commentPlaceholder: '请输入通过意见（选填）...',
      buttonText: '确认通过',
      buttonType: 'success',
      buttonIcon: 'Check'
    },
    reject: {
      type: 'reject',
      title: '拒绝工单',
      icon: 'Close',
      confirmTitle: '确认拒绝此工单？',
      confirmDesc: '拒绝后工单将终止，发起人可重新提交',
      commentPlaceholder: '请输入拒绝理由（必填）...',
      buttonText: '确认拒绝',
      buttonType: 'danger',
      buttonIcon: 'Close'
    },
    delegate: {
      type: 'delegate',
      title: '转办工单',
      icon: 'Switch',
      confirmTitle: '将此工单转办给他人？',
      confirmDesc: '转办后审批权将转移给指定人员',
      commentPlaceholder: '请输入转办说明（选填）...',
      buttonText: '确认转办',
      buttonType: 'warning',
      buttonIcon: 'Switch'
    }
  }
  return configs[currentAction.value] || configs.approve
})

const actionForm = reactive({
  comment: '',
  assignee: ''
})

// 操作历史
const operationHistory = computed(() => {
  const list = []
  if (ticket.value.created_by) {
    list.push({
      title: `${ticket.value.created_by} 发起工单`,
      time: formatTime(ticket.value.created_at),
      type: 'green',
      icon: 'Plus'
    })
  }
  timeline.value.forEach(item => {
    list.push({
      title: item.title || item.description || '流程流转',
      time: formatTime(item.created_at || item.time),
      type: item.status === 'completed' ? 'green' : item.status === 'current' ? 'blue' : 'gray',
      icon: item.status === 'completed' ? 'Check' : item.status === 'current' ? 'Clock' : 'More'
    })
  })
  return list
})

// 参与人
const participants = computed(() => {
  const list = []
  const assignees = ticket.value.assignees || []
  const colors = ['blue', 'orange', 'red', 'green']
  assignees.forEach((name, i) => {
    list.push({
      name,
      role: ticket.value.status === 'pending' && i === 0 ? '当前审批人' : '参与人',
      color: colors[i % colors.length]
    })
  })
  return list
})

// 计算属性：是否显示操作按钮
const showActions = computed(() => {
  return ticket.value.status === 'pending' || ticket.value.status === 'processing'
})

// 头像颜色映射
const avatarColors = ['blue', 'green', 'orange', 'red', 'purple']
const getAvatarColor = (name) => {
  if (!name) return 'blue'
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return avatarColors[Math.abs(hash) % avatarColors.length]
}

// 判断是否当前用户
const isCurrentUser = (username) => {
  // 简化判断，实际应从 auth store 获取
  return false
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  if (diffHour < 24) return `${diffHour} 小时前`
  if (diffDay < 7) return `${diffDay} 天前`

  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${m}-${d} ${h}:${min}`
}

// 获取工单详情
const fetchDetail = async () => {
  try {
    const response = await getTicketDetail(route.params.id)
    ticket.value = response.data
    comments.value = response.data.comments || []
  } catch (error) {
    console.error('获取工单详情失败:', error)
    ElMessage.error('获取工单详情失败')
  }
}

// 获取时间线
const fetchTimeline = async () => {
  try {
    const response = await getTimeline(route.params.id)
    timeline.value = response.data || []
  } catch (error) {
    console.error('获取时间线失败:', error)
  }
}

// 添加评论
const addComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  commentLoading.value = true
  try {
    const response = await addCommentApi(route.params.id, {
      content: newComment.value
    })
    comments.value.push(response.data)
    newComment.value = ''
    ElMessage.success('评论成功')
  } catch (error) {
    console.error('评论失败:', error)
    ElMessage.error('评论失败')
  } finally {
    commentLoading.value = false
  }
}

// 打开操作抽屉
const openDrawer = (action) => {
  currentAction.value = action
  actionForm.comment = ''
  actionForm.assignee = ''
  drawerVisible.value = true
}

// 关闭抽屉
const closeDrawer = () => {
  drawerVisible.value = false
  currentAction.value = ''
  actionForm.comment = ''
  actionForm.assignee = ''
}

// 提交操作
const submitAction = async () => {
  if (currentAction.value === 'reject' && !actionForm.comment.trim()) {
    ElMessage.warning('请输入拒绝理由')
    return
  }
  if (currentAction.value === 'delegate' && !actionForm.assignee) {
    ElMessage.warning('请选择转办人')
    return
  }

  drawerLoading.value = true
  try {
    switch (currentAction.value) {
      case 'approve':
        await completeTask(route.params.id, {
          action: 'approve',
          comment: actionForm.comment
        })
        ElMessage.success('审批通过')
        break
      case 'reject':
        await rejectTask(route.params.id, {
          comment: actionForm.comment
        })
        ElMessage.success('已拒绝')
        break
      case 'delegate':
        await delegateTask(route.params.id, {
          assignee_id: actionForm.assignee,
          comment: actionForm.comment
        })
        ElMessage.success('已转办')
        break
    }
    closeDrawer()
    fetchDetail()
    fetchTimeline()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    drawerLoading.value = false
  }
}

// 撤销
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要撤销此工单吗？', '撤销确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    // TODO: 调用撤销 API
    ElMessage.success('撤销成功')
    fetchDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤销失败:', error)
    }
  }
}

// 返回
const goBack = () => {
  router.push('/my/applications')
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    rejected: '已拒绝',
    cancelled: '已取消'
  }
  return labels[status] || status
}

// 获取优先级标签
const getPriorityLabel = (priority) => {
  const labels = { high: '高', medium: '中', low: '低' }
  return labels[priority] || priority
}

onMounted(() => {
  fetchDetail()
  fetchTimeline()
})
</script>

<style scoped>
.ticket-detail {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

/* ===================== 页面标题 ===================== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-header-back {
  width: 36px;
  height: 36px;
  border-radius: var(--border-radius-medium, 8px);
  border: 1px solid var(--border-color, #E5E6EB);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-regular, #4E5969);
  transition: all 0.2s;
}
.page-header-back:hover {
  border-color: var(--primary-color, #409EFF);
  color: var(--primary-color, #409EFF);
}
.page-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #1D2129);
  margin: 0;
  line-height: 1.3;
}
.page-header-desc {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  margin: 2px 0 0;
}

/* ===================== 状态条 ===================== */
.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 24px;
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.status-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-bar-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  flex: 1;
}
.status-bar-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.status-bar-actions {
  display: flex;
  gap: 8px;
}

/* ===================== 状态标签（复用列表页） ===================== */
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.status-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-tag--pending    { background: #FFF7E8; color: #FF7D00; }
.status-tag--pending .status-tag__dot    { background: #FF7D00; animation: tagPulse 2s infinite; }
.status-tag--processing { background: #E8F3FF; color: #1677FF; }
.status-tag--processing .status-tag__dot { background: #1677FF; animation: tagPulse 2s infinite; }
.status-tag--completed  { background: #E8FFEA; color: #00B42A; }
.status-tag--completed .status-tag__dot  { background: #00B42A; }
.status-tag--rejected   { background: #FFECE8; color: #F53F3F; }
.status-tag--rejected .status-tag__dot   { background: #F53F3F; }
.status-tag--cancelled  { background: #F2F3F5; color: #86909C; }
.status-tag--cancelled .status-tag__dot  { background: #86909C; }
@keyframes tagPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ===================== 优先级 ===================== */
.priority-bar {
  width: 3px;
  height: 16px;
  border-radius: 2px;
  display: inline-block;
}
.priority-bar--high   { background: #F53F3F; }
.priority-bar--medium { background: #FF7D00; }
.priority-bar--low    { background: #C9CDD4; }
.priority-text { font-size: 13px; font-weight: 600; }
.priority-text--high   { color: #F53F3F; }
.priority-text--medium { color: #FF7D00; }
.priority-text--low    { color: #86909C; }

/* ===================== 两栏布局 ===================== */
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
  align-items: start;
}

/* ===================== 卡片 ===================== */
.card {
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  overflow: hidden;
}
.card-header {
  padding: 14px 20px;
  border-bottom: 1px solid #F2F3F5;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-body {
  padding: 20px 24px;
}
.card-body--bordered { border-top: 1px solid #F2F3F5; }
.card-body--compact  { padding: 12px 20px; }

/* ===================== Tabs ===================== */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #F2F3F5;
  padding: 0 24px;
  background: #FAFBFC;
}
.tab {
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary, #86909C);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.tab:hover { color: var(--primary-color, #409EFF); }
.tab.active {
  color: var(--primary-color, #409EFF);
  border-bottom-color: var(--primary-color, #409EFF);
  font-weight: 600;
}
.tab-badge {
  font-size: 11px;
  background: #F56C6C;
  color: #fff;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
  min-width: 18px;
  text-align: center;
  line-height: 1.4;
}

/* ===================== 描述列表 ===================== */
.desc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.desc-item {
  padding: 12px 0;
  border-bottom: 1px solid #FAFBFC;
  display: flex;
  gap: 12px;
}
.desc-item:nth-child(odd) { padding-right: 20px; }
.desc-item:nth-child(even) { padding-left: 20px; border-left: 1px solid #FAFBFC; }
.desc-item--full { grid-column: 1 / -1; padding-right: 0; border-left: none; }
.desc-label {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  min-width: 70px;
  flex-shrink: 0;
}
.desc-value {
  font-size: 14px;
  color: var(--text-primary, #1D2129);
  font-weight: 500;
}
.desc-value--mono {
  font-family: 'SF Mono', Monaco, 'Cascadia Mono', monospace;
  font-size: 13px;
}

/* ===================== 区块标题 ===================== */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  margin-bottom: 16px;
}
.section-title__bar {
  width: 3px;
  height: 16px;
  background: var(--primary-color, #409EFF);
  border-radius: 2px;
}

/* ===================== 评论气泡 ===================== */
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.comment-bubble {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.comment-bubble--self { flex-direction: row-reverse; }
.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.comment-avatar--blue   { background: linear-gradient(135deg, #409EFF, #66B1FF); }
.comment-avatar--green  { background: linear-gradient(135deg, #67C23A, #85CE61); }
.comment-avatar--orange { background: linear-gradient(135deg, #E6A23C, #EBB563); }
.comment-avatar--red    { background: linear-gradient(135deg, #F56C6C, #F89898); }
.comment-avatar--purple { background: linear-gradient(135deg, #9B59B6, #BB77D4); }
.comment-bubble-content { max-width: 320px; }
.comment-bubble-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.comment-bubble--self .comment-bubble-meta { flex-direction: row-reverse; }
.comment-bubble-name { font-size: 13px; font-weight: 600; color: var(--text-primary, #1D2129); }
.comment-bubble-time { font-size: 11px; color: var(--text-placeholder, #C9CDD4); }
.comment-bubble-box {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-regular, #4E5969);
}
.comment-bubble:not(.comment-bubble--self) .comment-bubble-box {
  background: #F2F3F5;
  border-top-left-radius: 4px;
}
.comment-bubble--self .comment-bubble-box {
  background: var(--primary-color, #409EFF);
  color: #fff;
  border-top-right-radius: 4px;
}

/* 空评论 */
.empty-comments {
  text-align: center;
  padding: 40px 0;
  color: var(--text-secondary, #86909C);
}
.empty-comments__icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  background: #F7F8FA;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder, #C9CDD4);
}
.empty-comments p { margin: 0; }
.empty-comments__hint { font-size: 13px; margin-top: 4px !important; }

/* 评论输入 */
.comment-input-area {
  border-top: 1px solid #F2F3F5;
  padding: 16px 24px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.comment-input-area :deep(.el-textarea) { flex: 1; }

/* ===================== 右侧边栏 ===================== */
.aside-card { margin-bottom: 16px; }

/* 迷你时间线 */
.mini-timeline { padding: 4px 0; }
.mini-timeline-item {
  display: flex;
  gap: 12px;
  padding-bottom: 16px;
  position: relative;
}
.mini-timeline-item:last-child { padding-bottom: 0; }
.mini-timeline-item::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 28px;
  bottom: 0;
  width: 1.5px;
  background: #F2F3F5;
}
.mini-timeline-item:last-child::before { display: none; }
.mini-timeline-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}
.mini-timeline-dot--green  { background: #E8FFEA; color: #00B42A; }
.mini-timeline-dot--blue   { background: #E8F3FF; color: #409EFF; }
.mini-timeline-dot--gray   { background: #F2F3F5; color: #86909C; }
.mini-timeline-dot--default { background: #F2F3F5; color: #86909C; }
.mini-timeline-content { flex: 1; min-width: 0; }
.mini-timeline-title { font-size: 13px; color: var(--text-primary, #1D2129); font-weight: 500; }
.mini-timeline-time { font-size: 11px; color: var(--text-placeholder, #C9CDD4); margin-top: 2px; }
.empty-tip {
  text-align: center;
  font-size: 13px;
  color: var(--text-placeholder, #C9CDD4);
  padding: 20px 0;
}

/* 参与人 */
.participant-list { display: flex; flex-direction: column; gap: 12px; }
.participant-item { display: flex; align-items: center; gap: 10px; }
.participant-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.participant-avatar--blue   { background: linear-gradient(135deg, #409EFF, #66B1FF); }
.participant-avatar--green  { background: linear-gradient(135deg, #67C23A, #85CE61); }
.participant-avatar--orange { background: linear-gradient(135deg, #E6A23C, #EBB563); }
.participant-avatar--red    { background: linear-gradient(135deg, #F56C6C, #F89898); }
.participant-name { font-size: 13px; font-weight: 600; color: var(--text-primary, #1D2129); }
.participant-role { font-size: 11px; color: var(--text-secondary, #86909C); }

/* ===================== 抽屉内容 ===================== */
.drawer-content { padding: 0; }
.action-confirm {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: var(--border-radius-medium, 8px);
  margin-bottom: 24px;
}
.action-confirm--approve { background: #F0F9EB; }
.action-confirm--reject  { background: #FEF0F0; }
.action-confirm--delegate { background: #FFF7E8; }
.action-confirm-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.action-confirm-icon--approve { background: #E8FFEA; color: #67C23A; }
.action-confirm-icon--reject  { background: #FFECE8; color: #F56C6C; }
.action-confirm-icon--delegate { background: #FFF7E8; color: #E6A23C; }
.action-confirm-title { font-size: 14px; font-weight: 600; color: var(--text-primary, #1D2129); }
.action-confirm-desc { font-size: 12px; color: var(--text-secondary, #86909C); margin-top: 2px; }
.drawer-form-group { margin-bottom: 20px; }
.drawer-form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  margin-bottom: 8px;
}
.required { color: #F56C6C; }
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ===================== 响应式 ===================== */
@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
  .desc-grid { grid-template-columns: 1fr; }
  .desc-item:nth-child(even) { padding-left: 0; border-left: none; }
  .status-bar { flex-direction: column; align-items: flex-start; }
  .status-bar-actions { width: 100%; }
}
</style>
