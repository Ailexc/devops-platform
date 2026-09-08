<template>
  <div class="my-app-detail">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="goBack"><el-icon><ArrowLeft /></el-icon></div>
        <div>
          <h1>{{ title }}</h1>
          <p class="page-header-desc">{{ instance.instance_no }} · {{ instance.definition_name }}</p>
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
      <div class="meta-item" v-if="instance.current_node_key">
        <span class="meta-label">当前节点</span>
        <span class="meta-value mono">{{ instance.current_node_key }}</span>
      </div>
    </div>

    <div v-loading="loading" class="detail-layout">
      <!-- 左侧主内容 -->
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

          <!-- 流程追踪 -->
          <div v-show="activeTab === 'timeline'" class="tab-content">
            <div class="card-body">
              <FlowNodeStatus :instance-id="route.params.id" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Document, EditPen, Clock } from '@element-plus/icons-vue'
import { getInstanceDetail, getDefinition } from '@/api/modules/process'
import FlowNodeStatus from '@/components/ticket/FlowNodeStatus.vue'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const instance = ref({})
const definition = ref({})
const activeTab = ref('basic')

const title = computed(() => instance.value.business_key || instance.value.definition_name || '申请详情')
const formSchema = computed(() => definition.value.form_schema || {})
const formData = ref({})

const goBack = () => router.back()

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const insRes = await getInstanceDetail(route.params.id)
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
  } catch (error) {
    console.error('获取申请详情失败:', error)
    ElMessage.error('获取申请详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.my-app-detail { padding: 24px; background: #f7f8fa; min-height: 100%; max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header h1 { margin: 0 0 4px; font-size: 20px; color: #1d2129; }
.page-header-back { width: 34px; height: 34px; border-radius: 8px; background: #fff; border: 1px solid #e5e6eb; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #4e5969; }
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

.meta-bar { display: flex; gap: 0; flex-wrap: wrap; background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; }
.meta-item { display: flex; flex-direction: column; gap: 2px; padding: 4px 24px 4px 0; margin-right: 24px; border-right: 1px solid #f2f3f5; }
.meta-item:last-child { border-right: none; margin-right: 0; }
.meta-label { font-size: 12px; color: #86909c; }
.meta-value { font-size: 13px; color: #1d2129; font-weight: 500; }
.mono { font-family: ui-monospace, monospace; }

.detail-layout { display: flex; gap: 16px; }
.detail-main { flex: 1; min-width: 0; }
.card { background: #fff; border: 1px solid #e5e6eb; border-radius: 12px; overflow: hidden; }
.tabs { display: flex; border-bottom: 1px solid #f2f3f5; padding: 0 8px; }
.tab { display: flex; align-items: center; gap: 6px; padding: 14px 18px; cursor: pointer; color: #86909c; font-size: 14px; border-bottom: 2px solid transparent; }
.tab.active { color: #165dff; border-bottom-color: #165dff; font-weight: 600; }
.tab-content { padding: 0; }
.card-body { padding: 20px; }

.desc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px 32px; }
.desc-item { display: flex; flex-direction: column; gap: 4px; }
.desc-item--full { grid-column: 1 / -1; }
.desc-label { font-size: 12px; color: #86909c; }
.desc-value { font-size: 14px; color: #1d2129; }
.desc-value--mono { font-family: ui-monospace, monospace; }

.record-list { display: flex; flex-direction: column; gap: 16px; }
.record-item { display: flex; gap: 12px; }
.record-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; flex-shrink: 0; }
.record-avatar--blue { background: #4080ff; }
.record-avatar--green { background: #00b42a; }
.record-avatar--orange { background: #ff7d00; }
.record-avatar--red { background: #f53f3f; }
.record-avatar--purple { background: #722ed1; }
.record-main { flex: 1; min-width: 0; }
.record-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.record-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.record-action { font-size: 12px; padding: 1px 8px; border-radius: 4px; }
.record-action--approve { color: #00b42a; background: #e8ffea; }
.record-action--reject { color: #f53f3f; background: #ffece8; }
.record-action--delegate { color: #ff7d00; background: #fff3e8; }
.record-action--cc { color: #4080ff; background: #e8f3ff; }
.record-action--comment { color: #86909c; background: #f2f3f5; }
.record-task { font-size: 12px; color: #86909c; }
.record-opinion { font-size: 13px; color: #4e5969; margin-top: 4px; background: #f7f8fa; border-radius: 6px; padding: 8px 10px; }
.record-time { font-size: 12px; color: #c9cdd4; margin-top: 4px; }
.record-source { color: #722ed1; margin-left: 8px; }
</style>
