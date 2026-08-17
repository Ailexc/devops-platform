<template>
  <div class="apply-page">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back">←</div>
        <div>
          <h1>发起申请</h1>
          <p class="page-header-desc">选择要发起的流程，填写表单后提交</p>
        </div>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-bar">
      <div class="step" :class="{ active: true }">
        <div class="step__number">1</div>
        <span class="step__label">选择流程</span>
      </div>
      <div class="step__line"></div>
      <div class="step">
        <div class="step__number">2</div>
        <span class="step__label">填写表单</span>
      </div>
    </div>

    <!-- 流程选择区域 -->
    <div class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">
          <span class="content-card-bar"></span>
          选择流程
        </div>
      </div>
      <div class="content-card-body">
        <div class="definition-grid" :class="{ highlight: focus === 'form' }">
          <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">暂无可发起的流程，请联系管理员配置</div>
          </div>
        </div>
        <div class="card-footer">
          <button class="btn-primary is-disabled">
            下一步：填写表单 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<style scoped lang="scss">
.apply-page { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px;
}
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-back {
  width: 32px; height: 32px; border-radius: 8px; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #4e5969; cursor: pointer;
}
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }

.steps-bar { display: flex; align-items: center; justify-content: center; padding: 24px 40px; }
.step { display: flex; align-items: center; gap: 8px; &.active .step__number { background: #409eff; color: #fff; border-color: #409eff; } }
.step__number {
  width: 28px; height: 28px; border-radius: 50%; border: 2px solid #dcdfe6;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; color: #c0c4cc;
}
.step__label { font-size: 14px; color: #4e5969; font-weight: 500; }
.step__line { width: 80px; height: 2px; background: #e5e6eb; margin: 0 16px; }

.content-card { margin: 0 24px 24px; background: #fff; border-radius: 12px; overflow: hidden; }
.content-card-header { padding: 16px 20px; border-bottom: 1px solid #f2f3f5; }
.content-card-title {
  font-size: 15px; font-weight: 600; color: #1d2129;
  display: flex; align-items: center; gap: 8px;
}
.content-card-bar { display: inline-block; width: 3px; height: 14px; background: #409eff; border-radius: 2px; }
.content-card-body { padding: 24px; }

.definition-grid {
  min-height: 300px; display: flex; align-items: center; justify-content: center;
  transition: all 0.3s; &.highlight { box-shadow: inset 0 0 0 2px rgba(64,158,255,0.3); border-radius: 8px; }
}
.empty-state { text-align: center; padding: 40px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { font-size: 14px; color: #c9cdd4; }
.card-footer { display: flex; justify-content: flex-end; padding-top: 16px; border-top: 1px solid #f2f3f5; margin-top: 16px; }
.btn-primary {
  padding: 10px 24px; background: #409eff; color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer;
  &:hover { background: #337ecc; }
  &.is-disabled { background: #a0cfff; cursor: not-allowed; &:hover { background: #a0cfff; } }
}
</style>
