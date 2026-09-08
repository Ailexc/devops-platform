<template>
  <div class="task-detail">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="goBack"><el-icon><ArrowLeft /></el-icon></div>
        <div>
          <h1>{{ title }}</h1>
          <p class="page-header-desc">{{ instance.instance_no }} · {{ task.node_name || '任务办理' }}</p>
        </div>
      </div>
      <span v-if="instance.status" class="status-tag" :class="'status-tag--' + instance.status">
        <span class="status-tag__dot"></span>{{ instance.status_display }}
      </span>
    </div>

    <!-- 关键信息条 -->
    <div v-if="instance.status" class="meta-bar">
      <div class="meta-item">
        <span class="meta-label">流程</span>
        <span class="meta-value">{{ instance.definition_name }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">发起人</span>
        <span class="meta-value">{{ instance.started_by_name }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">发起时间</span>
        <span class="meta-value">{{ formatTime(instance.started_at) }}</span>
      </div>
      <div class="meta-item" v-if="instance.ended_at">
        <span class="meta-label">结束时间</span>
        <span class="meta-value">{{ formatTime(instance.ended_at) }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">当前节点</span>
        <span class="meta-value mono">{{ task.node_name || instance.current_node_key || '-' }}</span>
      </div>
    </div>

    <div v-loading="loading" class="detail-layout">
      <div class="detail-main">
        <div class="card">
          <div class="tabs">
            <div class="tab" :class="{ active: activeTab === 'basic' }" @click="activeTab = 'basic'">
              <el-icon><Document /></el-icon> 基本信息
            </div>
            <div class="tab" :class="{ active: activeTab === 'form' }" @click="activeTab = 'form'">
              <el-icon><EditPen /></el-icon> 表单数据
            </div>
            <div class="tab" :class="{ active: activeTab === 'timeline' }" @click="activeTab = 'timeline'">
              <el-icon><Clock /></el-icon> 流程追踪
            </div>
          </div>

          <!-- 基本信息 -->
          <div v-show="activeTab === 'basic'" class="tab-content">
            <div class="card-body">
              <div class="desc-grid">
                <div class="desc-item desc-item--full">
                  <span class="desc-label">申请标题</span>
                  <span class="desc-value">{{ title }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">申请单号</span>
                  <span class="desc-value desc-value--mono">{{ instance.instance_no }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">流程模板</span>
                  <span class="desc-value">{{ instance.definition_name }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">状态</span>
                  <span class="desc-value">{{ instance.status_display }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">发起人</span>
                  <span class="desc-value">{{ instance.started_by_name }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">发起时间</span>
                  <span class="desc-value">{{ formatTime(instance.started_at) }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">结束时间</span>
                  <span class="desc-value">{{ instance.ended_at ? formatTime(instance.ended_at) : '-' }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">当前节点</span>
                  <span class="desc-value mono">{{ instance.current_node_key || '-' }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">当前任务</span>
                  <span class="desc-value">{{ task.node_name || '-' }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">任务状态</span>
                  <span class="desc-value">{{ task.status_display || '-' }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">处理人</span>
                  <span class="desc-value">{{ task.assignee_name || '待认领' }}</span>
                </div>
                <div class="desc-item">
                  <span class="desc-label">业务主键</span>
                  <span class="desc-value mono">{{ instance.business_key || '-' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 表单数据 -->
          <div v-show="activeTab === 'form'" class="tab-content">
            <div class="card-body">
              <template v-if="formSchema?.rules?.length">
                <FormRenderer
                  v-model="formData"
                  :rules="formSchema.rules"
                  :options="formSchema.options || {}"
                  :readonly="true"
                />
              </template>
              <el-empty v-else description="该流程无表单数据" :image-size="60" />
            </div>
          </div>

          <!-- 流程追踪（含流程图） -->
          <div v-show="activeTab === 'timeline'" class="tab-content">
            <div class="card-body">
              <FlowNodeStatus v-if="task.instance" :instance-id="task.instance" />
            </div>
          </div>
        </div>

        <!-- 审批操作（待办 / 异常时显示） -->
        <div v-if="showActions" class="card action-card">
          <div class="card-header">
            <span>{{ isAbnormal ? '异常处理' : '审批操作' }}</span>
          </div>
          <div class="card-body">
            <el-alert
              v-if="isAbnormal"
              type="error"
              :closable="false"
              show-icon
              title="自动执行异常，请排查执行日志后处理"
              :description="task.opinion"
              class="abnormal-alert"
            />
            <el-alert
              v-if="isConfirmTask"
              type="info"
              :closable="false"
              show-icon
              title="自动执行 + 人工确认"
              description="确认后系统将执行本节点的自动动作"
              class="abnormal-alert"
            />
            <el-form :model="actionForm" label-width="80px">
              <el-form-item label="审批意见" required>
                <el-input
                  v-model="actionForm.comment"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入审批意见（同意/拒绝必填）"
                />
              </el-form-item>
              <el-form-item v-if="currentAction === 'delegate'" label="转办人">
                <el-select v-model="actionForm.assignee" placeholder="请选择转办人" style="width: 100%">
                  <el-option v-for="user in users" :key="user.id" :label="user.name" :value="user.id" />
                </el-select>
              </el-form-item>
            </el-form>
            <div class="action-buttons">
              <template v-if="isConfirmTask">
                <el-button type="primary" @click="submitAction('approve')" :loading="submitting">确认并执行</el-button>
                <el-button type="danger" @click="submitAction('reject')" :loading="submitting">拒绝</el-button>
              </template>
              <template v-else-if="isAbnormal">
                <el-button type="warning" @click="rerunAction" :loading="submitting">重新执行</el-button>
                <el-button type="success" @click="markHandled" :loading="submitting">标记处理完成</el-button>
              </template>
              <template v-else>
                <el-button type="primary" @click="submitAction('approve')" :loading="submitting">同意</el-button>
                <el-button type="danger" @click="submitAction('reject')" :loading="submitting">拒绝</el-button>
                <el-button type="warning" @click="submitAction('delegate')" :loading="submitting">转办</el-button>
                <el-button type="info" @click="submitAction('return')" :loading="submitting">退回</el-button>
              </template>
            </div>
          </div>
        </div>

        <!-- 审批历史 -->
        <div class="card history-card">
          <div class="card-header"><span>审批历史</span></div>
          <div class="card-body">
            <el-timeline v-if="approvalHistory.length">
              <el-timeline-item
                v-for="record in approvalHistory"
                :key="record.id"
                :timestamp="formatTime(record.created_at)"
                :type="record.action === 'approve' ? 'success' : record.action === 'reject' ? 'danger' : 'primary'"
              >
                <div class="history-item">
                  <div class="history-user">{{ record.username }} <span class="history-action">{{ actionLabel(record.action) }}</span></div>
                  <div v-if="record.initiator_source_display" class="history-source">{{ record.initiator_source_display }}</div>
                  <div v-if="record.comment" class="history-comment">{{ record.comment }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无审批记录" :image-size="50" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Document, EditPen, Clock } from '@element-plus/icons-vue'
import { getTaskDetail, completeTask, rejectTask, delegateTask, returnTask, rerunTask } from '@/api/modules/task'
import { getInstanceDetail, getDefinition, getInstanceApprovalRecords } from '@/api/modules/process'
import { getUsers } from '@/api/modules/admin'
import FlowNodeStatus from '@/components/ticket/FlowNodeStatus.vue'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const task = ref({})
const instance = ref({})
const definition = ref({})
const formData = ref({})
const approvalHistory = ref([])
const users = ref([])
const submitting = ref(false)
const currentAction = ref('')
const activeTab = ref('basic')

const actionForm = reactive({
  comment: '',
  assignee: ''
})

const title = computed(() => instance.value.business_key || instance.value.definition_name || '任务办理')
const formSchema = computed(() => definition.value.form_schema || {})

// 获取用户列表（供转办人选择）
const fetchUsers = async () => {
  try {
    const response = await getUsers({ page_size: 200 })
    const data = response?.data ?? response
    users.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 计算属性：是否显示操作按钮
const showActions = computed(() => {
  return (
    task.value.status === 'pending' ||
    task.value.status === 'claimed' ||
    task.value.status === 'abnormal'
  )
})

const isAbnormal = computed(() => task.value.status === 'abnormal')

const isConfirmTask = computed(
  () =>
    task.value.task_config_mode === 'confirm' &&
    (task.value.status === 'pending' || task.value.status === 'claimed')
)

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

// 获取任务详情 + 关联实例 / 流程定义 / 审批记录
const fetchDetail = async () => {
  loading.value = true
  try {
    const response = await getTaskDetail(route.params.id)
    task.value = response?.data ?? response

    if (task.value.instance) {
      // 关联实例（用于基本信息 / 表单数据 / 流程图）
      try {
        const insRes = await getInstanceDetail(task.value.instance)
        instance.value = insRes?.data ?? insRes ?? {}
        formData.value = JSON.parse(JSON.stringify(instance.value.variables || {}))
        if (instance.value.definition) {
          try {
            const defRes = await getDefinition(instance.value.definition)
            definition.value = defRes?.data ?? defRes ?? {}
          } catch (e) {
            console.error('获取流程定义失败:', e)
          }
        }
      } catch (e) {
        console.error('获取实例详情失败:', e)
      }

      // 审批记录（含发起来源），用于审批历史
      try {
        const records = await getInstanceApprovalRecords(task.value.instance)
        const list = Array.isArray(records) ? records : (records?.results || [])
        approvalHistory.value = list.map((record) => ({
          id: record.id,
          created_at: record.created_at,
          action: record.action,
          username: record.user_name,
          comment: record.opinion,
          initiator_source_display: record.initiator_source_display
        }))
      } catch (error) {
        console.error('获取审批记录失败:', error)
        approvalHistory.value = []
      }
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    loading.value = false
  }
}

const actionLabel = (action) => {
  const labels = { approve: '同意', reject: '拒绝', delegate: '转办', cc: '抄送', comment: '评论' }
  return labels[action] || '操作'
}

// 提交操作
const submitAction = async (action) => {
  currentAction.value = action

  // 确认任务：必须填写办理说明
  if (action === 'approve' && isConfirmTask.value && !actionForm.comment) {
    ElMessage.warning('请填写办理说明')
    return
  }

  // 审批意见必填：同意/拒绝均需填写意见
  if ((action === 'approve' || action === 'reject') && !actionForm.comment) {
    ElMessage.warning('请填写审批意见')
    return
  }
  
  // 验证
  
  if (action === 'delegate' && !actionForm.assignee) {
    ElMessage.warning('请选择转办人')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要执行此操作吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  
  submitting.value = true
  try {
    switch (action) {
      case 'approve':
        await completeTask(route.params.id, {
          action: 'approve',
          comment: actionForm.comment
        })
        break
      case 'reject':
        await rejectTask(route.params.id, {
          comment: actionForm.comment
        })
        break
      case 'delegate':
        await delegateTask(route.params.id, {
          assignee_id: actionForm.assignee,
          comment: actionForm.comment
        })
        break
      case 'return':
        await returnTask(route.params.id, {
          comment: actionForm.comment
        })
        break
    }
    
    ElMessage.success('操作成功')
    actionForm.comment = ''
    actionForm.assignee = ''
    fetchDetail()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 异常任务：重新执行失败的动作
const rerunAction = async () => {
  try {
    await ElMessageBox.confirm('确定重新执行失败的动作吗？', '重新执行', {
      confirmButtonText: '重新执行',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  submitting.value = true
  try {
    await rerunTask(route.params.id)
    ElMessage.success('已重新执行')
    fetchDetail()
  } catch (error) {
    console.error('重新执行失败:', error)
    ElMessage.error('重新执行失败，请查看执行日志')
  } finally {
    submitting.value = false
  }
}

// 异常任务：标记处理完成并推进流程
const markHandled = async () => {
  submitting.value = true
  try {
    await completeTask(route.params.id, {
      result: 'approve',
      opinion: actionForm.comment || '人工处理完成'
    })
    ElMessage.success('已标记处理完成')
    fetchDetail()
  } catch (error) {
    console.error('处理失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 返回
const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchDetail()
  fetchUsers()
})
</script>

<style scoped>
.task-detail {
  padding: 24px;
  background: #f7f8fa;
  min-height: 100%;
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px; margin-bottom: 16px; flex-wrap: wrap;
}
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header h1 { margin: 0 0 4px; font-size: 20px; color: #1d2129; }
.page-header-back {
  width: 34px; height: 34px; border-radius: 8px; background: #fff;
  border: 1px solid #e5e6eb; display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #4e5969;
}
.page-header-back:hover { border-color: #409eff; color: #409eff; }
.page-header-desc { margin: 0; font-size: 13px; color: #86909c; }

.status-tag { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
.status-tag__dot { width: 8px; height: 8px; border-radius: 50%; background: #c9cdd4; }
.status-tag--running { color: #409eff; }
.status-tag--running .status-tag__dot { background: #409eff; }
.status-tag--completed { color: #00b42a; }
.status-tag--completed .status-tag__dot { background: #00b42a; }
.status-tag--terminated { color: #f53f3f; }
.status-tag--terminated .status-tag__dot { background: #f53f3f; }
.status-tag--suspended { color: #ff7d00; }
.status-tag--suspended .status-tag__dot { background: #ff7d00; }

.meta-bar {
  display: flex; gap: 0; flex-wrap: wrap; background: #fff;
  border: 1px solid #e5e6eb; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px;
}
.meta-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 4px 24px 4px 0; margin-right: 24px; border-right: 1px solid #f2f3f5;
}
.meta-item:last-child { border-right: none; margin-right: 0; }
.meta-label { font-size: 12px; color: #86909c; }
.meta-value { font-size: 13px; color: #1d2129; font-weight: 500; }
.mono { font-family: ui-monospace, monospace; }

.detail-layout { display: flex; gap: 16px; }
.detail-main { flex: 1; min-width: 0; }
.card {
  background: #fff; border: 1px solid #e5e6eb; border-radius: 12px;
  overflow: hidden; margin-bottom: 16px;
}
.card-header {
  padding: 14px 20px; font-size: 14px; font-weight: 600; color: #1d2129;
  border-bottom: 1px solid #f2f3f5;
}
.card-body { padding: 20px; }

.tabs { display: flex; border-bottom: 1px solid #f2f3f5; padding: 0 8px; }
.tab {
  display: flex; align-items: center; gap: 6px; padding: 14px 18px; cursor: pointer;
  color: #86909c; font-size: 14px; border-bottom: 2px solid transparent;
}
.tab.active { color: #165dff; border-bottom-color: #165dff; font-weight: 600; }
.tab-content { padding: 0; }

.desc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px 32px; }
.desc-item { display: flex; flex-direction: column; gap: 4px; }
.desc-item--full { grid-column: 1 / -1; }
.desc-label { font-size: 12px; color: #86909c; }
.desc-value { font-size: 14px; color: #1d2129; }
.desc-value--mono { font-family: ui-monospace, monospace; }

.abnormal-alert { margin-bottom: 16px; }
.action-buttons { display: flex; gap: 10px; margin-top: 16px; }

.history-item { line-height: 1.8; }
.history-user { font-weight: 600; color: #1d2129; }
.history-action { color: #4e5969; margin-left: 8px; font-weight: 400; }
.history-source { color: #409eff; font-size: 12px; margin-top: 4px; }
.history-comment {
  color: #86909c; font-size: 13px; margin-top: 4px;
  background: #f7f8fa; border-radius: 6px; padding: 8px 10px;
}
</style>
