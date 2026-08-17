<template>
  <div class="process-definition-editor">
    <!-- 步骤指示器 -->
    <div class="wizard-steps">
      <div class="wizard-step" v-for="(step, index) in steps" :key="step.title" :class="{ active: currentStep === index, finished: currentStep > index }">
        <div class="step-indicator">
          <span v-if="currentStep > index" class="step-check">✓</span>
          <template v-else>{{ index + 1 }}</template>
        </div>
        <div class="step-label">
          <span class="step-title">{{ step.title }}</span>
          <span class="step-desc">{{ step.desc }}</span>
        </div>
        <div v-if="index < steps.length - 1" class="step-line" />
      </div>
    </div>

    <!-- 步骤 1：基本信息 -->
    <div class="step-content">
      <div class="step-header">
        <h3>基本信息</h3>
        <p>配置流程的基础信息与发起范围</p>
      </div>
      <div class="form-body">
        <div class="collapse-section">
          <div class="collapse-header">基本信息 <span class="collapse-arrow">▼</span></div>
          <div class="collapse-body">
            <div class="form-grid">
              <div class="form-item" :class="{ highlight: focus === 'name' }">
                <label>流程名称 <span class="required">*</span></label>
                <div class="el-input"><div class="el-input__inner">服务器申请</div></div>
              </div>
              <div class="form-item" :class="{ highlight: focus === 'key' }">
                <label>唯一标识 <span class="required">*</span></label>
                <div class="el-input"><div class="el-input__inner">server_request</div></div>
              </div>
              <div class="form-item">
                <label>流程分类</label>
                <div class="el-select"><div class="el-input__inner">IT 运维</div><span class="el-input__suffix">▼</span></div>
              </div>
              <div class="form-item">
                <label>流程分组</label>
                <div class="el-input"><div class="el-input__inner">基础设施</div></div>
              </div>
              <div class="form-item">
                <label>上线状态</label>
                <div class="el-select"><div class="el-input__inner">正式上线</div><span class="el-input__suffix">▼</span></div>
              </div>
              <div class="form-item">
                <label>发起人自审</label>
                <div class="switch-row"><span class="switch-off">○</span><span class="field-tip">允许发起人审批自己的申请</span></div>
              </div>
            </div>
            <div class="form-item form-item--full">
              <label>流程描述</label>
              <div class="el-textarea"><div class="el-textarea__inner">用于申请服务器资源，支持 CPU、内存、操作系统等配置</div></div>
            </div>
          </div>
        </div>

        <div class="collapse-section">
          <div class="collapse-header">发起人设置 <span class="collapse-arrow">▼</span></div>
          <div class="collapse-body">
            <div class="form-grid">
              <div class="form-item">
                <label>提交范围</label>
                <div class="el-select"><div class="el-input__inner">全员可提交</div><span class="el-input__suffix">▼</span></div>
              </div>
              <div class="form-item">
                <label>流程管理员</label>
                <div class="el-select"><div class="el-input__inner">admin</div><span class="el-input__suffix">▼</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="wizard-footer">
      <button class="btn-default">保存草稿</button>
      <button class="btn-primary">发布</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const steps = [
  { title: '基本信息', desc: '配置流程基础信息' },
  { title: '表单设计', desc: '设计申请表单' },
  { title: '流程建模', desc: '设计审批流程' },
  { title: '检查', desc: '检查并发布' },
]

const currentStep = 0
</script>

<style scoped lang="scss">
.process-definition-editor { width: 100%; height: 100%; display: flex; flex-direction: column; background: #f5f7fa; overflow-y: auto; }

.wizard-steps {
  display: flex; align-items: flex-start; justify-content: center;
  background: #fff; border-bottom: 1px solid #e5e6eb;
  padding: 20px 40px; gap: 0;
}
.wizard-step { display: flex; align-items: center; position: relative; }
.step-indicator {
  width: 32px; height: 32px; border-radius: 50%;
  border: 2px solid #dcdfe6; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; color: #c0c4cc; background: #fff;
  &.active { background: #409eff; color: #fff; border-color: #409eff; }
  .wizard-step.active & { background: #409eff; color: #fff; border-color: #409eff; }
  .wizard-step.finished & { background: #67c23a; color: #fff; border-color: #67c23a; }
}
.step-check { font-size: 14px; }
.step-label { margin-left: 10px; }
.step-title { display: block; font-size: 14px; font-weight: 600; color: #1d2129; }
.step-desc { display: block; font-size: 12px; color: #86909c; margin-top: 2px; }
.step-line { width: 60px; height: 2px; background: #e5e6eb; margin: 0 16px; margin-top: 16px; position: absolute; right: -76px; }
.wizard-step:last-child .step-line { display: none; }

.step-content { flex: 1; padding: 24px; }
.step-header { margin-bottom: 20px; h3 { font-size: 16px; font-weight: 600; color: #1d2129; margin: 0 0 4px; } p { font-size: 13px; color: #86909c; margin: 0; } }

.collapse-section { background: #fff; border-radius: 12px; margin-bottom: 16px; overflow: hidden; }
.collapse-header {
  padding: 14px 20px; font-size: 14px; font-weight: 600; color: #1d2129;
  border-bottom: 1px solid #f2f3f5; display: flex; justify-content: space-between; align-items: center;
}
.collapse-arrow { font-size: 10px; color: #c0c4cc; }
.collapse-body { padding: 20px; }

.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.form-item {
  display: flex; flex-direction: column; gap: 6px;
  &--full { grid-column: 1 / -1; }
  &.highlight { background: rgba(64,158,255,0.05); padding: 8px; border-radius: 8px; border: 1px solid rgba(64,158,255,0.3); }
  label { font-size: 13px; color: #4e5969; font-weight: 500; }
}
.required { color: #f56c6c; }
.el-input, .el-select { display: flex; align-items: center; border: 1px solid #dcdfe6; border-radius: 6px; height: 34px; }
.el-input__inner { padding: 0 12px; font-size: 13px; color: #4e5969; flex: 1; }
.el-input__suffix { padding-right: 8px; font-size: 10px; color: #c0c4cc; }
.el-textarea { border: 1px solid #dcdfe6; border-radius: 6px; }
.el-textarea__inner { padding: 10px 12px; font-size: 13px; color: #4e5969; min-height: 60px; }
.switch-row { display: flex; align-items: center; gap: 8px; }
.switch-off { color: #c0c4cc; font-size: 16px; }
.field-tip { font-size: 12px; color: #86909c; }

.wizard-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 16px 24px; background: #fff; border-top: 1px solid #e5e6eb;
}
.btn-default { padding: 8px 20px; background: #fff; border: 1px solid #dcdfe6; border-radius: 8px; font-size: 14px; color: #606266; cursor: pointer; &:hover { border-color: #409eff; color: #409eff; } }
.btn-primary { padding: 8px 20px; background: #409eff; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; &:hover { background: #337ecc; } }
</style>
