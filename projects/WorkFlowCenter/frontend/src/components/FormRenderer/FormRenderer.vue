<template>
  <div class="form-renderer-wrapper">
    <form-create
      v-if="hasRules"
      v-model="formData"
      :rule="rules"
      :option="formOptions"
      @submit="onSubmit"
      @update:api="onApiReady"
    />
    <div v-else class="form-empty">
      <el-empty description="暂无表单配置" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, nextTick } from 'vue'
import formCreate from '@form-create/element-ui'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  rules: {
    type: Array,
    default: () => []
  },
  options: {
    type: Object,
    default: () => ({})
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const formData = ref(props.modelValue || {})
const fApi = ref(null)

// 存在表单规则时才渲染 form-create
const hasRules = computed(() => (props.rules || []).length > 0)

// 获取 form-create 实例（form-create v3 通过 @update:api 暴露 api）
const onApiReady = (api) => {
  fApi.value = api
  // 回填初始值（父组件传入的 modelValue）
  if (props.modelValue && Object.keys(props.modelValue).length) {
    api.setValue(props.modelValue)
  }
}

// 表单配置
const formOptions = computed(() => {
  const baseOptions = {
    submitBtn: false,     // 不显示内置提交按钮
    resetBtn: false,      // 不显示内置重置按钮
    ...props.options,
  }
  
  if (props.readonly) {
    baseOptions.disabled = true
  }
  
  return baseOptions
})

// 监听外部 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && JSON.stringify(newVal) !== JSON.stringify(formData.value)) {
      formData.value = { ...newVal }
      // 同步到 form-create
      if (fApi.value) {
        fApi.value.setValue(newVal)
      }
    }
  },
  { deep: true }
)

// 监听表单数据变化
watch(
  formData,
  (newVal) => {
    emit('update:modelValue', { ...newVal })
  },
  { deep: true }
)

// 获取表单数据（供外部调用）
const getFormData = async () => {
  if (!fApi.value) return formData.value
  
  try {
    const data = await fApi.value.submit()
    return data
  } catch (e) {
    // 校验失败
    throw e
  }
}

// 设置表单数据
const setFormData = (data) => {
  formData.value = { ...data }
  if (fApi.value) {
    fApi.value.setValue(data)
  }
}

// 提交处理
const onSubmit = (formData) => {
  emit('submit', formData)
}

// 暴露方法给父组件
defineExpose({
  getFormData,
  setFormData,
  fApi
})
</script>

<style scoped>
.form-renderer-wrapper {
  width: 100%;
}

.form-renderer-wrapper :deep(.el-form-item) {
  margin-bottom: 18px;
}

.form-empty {
  padding: 20px;
}
</style>
