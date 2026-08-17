<template>
  <div class="ticket-create">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </div>
        <div>
          <h1>发起工单</h1>
          <p class="page-header-desc">选择流程模版并填写表单内容</p>
        </div>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-bar">
      <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
        <div class="step__number">
          <el-icon v-if="currentStep > 1"><Check /></el-icon>
          <span v-else>1</span>
        </div>
        <span class="step__label">选择模版</span>
      </div>
      <div class="step__line" :class="{ active: currentStep > 1 }"></div>
      <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
        <div class="step__number">
          <el-icon v-if="currentStep > 2"><Check /></el-icon>
          <span v-else>2</span>
        </div>
        <span class="step__label">填写表单</span>
      </div>
      <div class="step__line" :class="{ active: currentStep > 2 }"></div>
      <div class="step" :class="{ active: currentStep >= 3 }">
        <div class="step__number">3</div>
        <span class="step__label">提交工单</span>
      </div>
    </div>

    <!-- 表单内容 -->
    <div class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        class="ticket-form"
      >
        <!-- 流程模版选择 -->
        <div class="form-section">
          <div class="form-section__title">
            <span class="form-section__bar"></span>
            基本信息
          </div>
          <div class="form-section__body">
            <el-form-item prop="definition_id">
              <label class="form-label">流程模版 <span class="required">*</span></label>
              <el-select
                v-model="form.definition_id"
                placeholder="请选择流程模版"
                style="width: 100%"
                size="large"
                @change="handleDefinitionChange"
              >
                <el-option
                  v-for="item in definitions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                >
                  <div class="definition-option">
                    <el-icon><Document /></el-icon>
                    <span>{{ item.name }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item prop="title">
              <label class="form-label">工单标题 <span class="required">*</span></label>
              <el-input
                v-model="form.title"
                placeholder="请输入工单标题，简要描述你的需求"
                size="large"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </div>
        </div>

        <!-- 动态表单 -->
        <template v-if="currentDefinition?.form_schema?.rules?.length">
          <div class="form-section">
            <div class="form-section__title">
              <span class="form-section__bar"></span>
              表单内容
            </div>
            <div class="form-section__body">
              <FormRenderer
                v-model="form.form_data"
                :rules="currentDefinition.form_schema.rules"
                :options="currentDefinition.form_schema.options || {}"
              />
            </div>
          </div>
        </template>

        <!-- 提交按钮 -->
        <div class="form-actions">
          <el-button size="large" @click="goBack">取消</el-button>
          <el-button
            type="primary"
            size="large"
            @click="submit"
            :loading="submitting"
            class="submit-btn"
          >
            <el-icon><Promotion /></el-icon>
            提交工单
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDefinitions, getDefinition, startProcess } from '@/api/modules/process'
import FormRenderer from '@/components/FormRenderer/FormRenderer.vue'
import { ArrowLeft, Check, Document, Promotion } from '@element-plus/icons-vue'

const router = useRouter()

const formRef = ref(null)
const submitting = ref(false)
const definitions = ref([])
const currentDefinition = ref(null)

const form = reactive({
  definition_id: '',
  title: '',
  form_data: {}
})

const rules = {
  definition_id: [
    { required: true, message: '请选择流程模版', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入工单标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度为 2-100 个字符', trigger: 'blur' }
  ]
}

// 步骤计算
const currentStep = computed(() => {
  if (form.definition_id && form.title) return 3
  if (form.definition_id) return 2
  return 1
})

// 获取流程定义列表
const fetchDefinitions = async () => {
  try {
    const response = await getDefinitions({ status: 'published', page: 1, page_size: 100 })
    definitions.value = response.data?.items || []
  } catch (error) {
    console.error('获取流程定义失败:', error)
  }
}

// 流程定义变更
const handleDefinitionChange = async (id) => {
  if (!id) {
    currentDefinition.value = null
    return
  }
  try {
    const response = await getDefinition(id)
    currentDefinition.value = response.data
    form.form_data = {}
  } catch (error) {
    console.error('获取流程定义详情失败:', error)
  }
}

// 提交
const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await startProcess({
      definition_id: form.definition_id,
      title: form.title,
      form_data: form.form_data
    })
    ElMessage.success('工单提交成功')
    router.push('/my/applications')
  } catch (error) {
    console.error('提交工单失败:', error)
    ElMessage.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 返回
const goBack = () => {
  router.push('/')
}

onMounted(() => {
  fetchDefinitions()
})
</script>

<style scoped>
.ticket-create {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
  max-width: 800px;
  margin: 0 auto;
}

/* ===================== 页面标题 ===================== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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
  font-size: 22px;
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

/* ===================== 步骤条 ===================== */
.steps-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 24px;
  padding: 20px 0;
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.step__number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background: #F2F3F5;
  color: var(--text-secondary, #86909C);
  transition: all 0.3s;
}
.step.active .step__number {
  background: var(--primary-color, #409EFF);
  color: #fff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}
.step.done .step__number {
  background: #67C23A;
  color: #fff;
}
.step__label {
  font-size: 13px;
  color: var(--text-secondary, #86909C);
  font-weight: 500;
}
.step.active .step__label { color: var(--primary-color, #409EFF); font-weight: 600; }
.step.done .step__label { color: #67C23A; }
.step__line {
  width: 60px;
  height: 2px;
  background: #F2F3F5;
  margin: 0 16px;
  border-radius: 1px;
  transition: background 0.3s;
}
.step__line.active { background: var(--primary-color, #409EFF); }

/* ===================== 表单卡片 ===================== */
.form-card {
  background: #fff;
  border-radius: var(--ticket-radius, 12px);
  box-shadow: var(--ticket-card-shadow, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--ticket-card-border, #E5E6EB);
  overflow: hidden;
}

/* ===================== 表单区块 ===================== */
.form-section {
  padding: 0 32px;
}
.form-section:first-child { padding-top: 32px; }
.form-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  margin-bottom: 20px;
}
.form-section__bar {
  width: 3px;
  height: 16px;
  background: var(--primary-color, #409EFF);
  border-radius: 2px;
}
.form-section__body {
  padding-bottom: 24px;
}

/* ===================== 表单元素 ===================== */
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1D2129);
  margin-bottom: 8px;
}
.required { color: #F53F3F; }
.definition-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===================== 提交按钮 ===================== */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px 32px;
  border-top: 1px solid #F2F3F5;
  background: #FAFBFC;
}
.submit-btn {
  min-width: 120px;
}

/* ===================== 响应式 ===================== */
@media (max-width: 600px) {
  .ticket-create { padding: 16px; }
  .form-section { padding: 0 20px; }
  .form-actions { padding: 20px; }
  .steps-bar { padding: 16px; }
  .step__line { width: 32px; margin: 0 8px; }
}
</style>