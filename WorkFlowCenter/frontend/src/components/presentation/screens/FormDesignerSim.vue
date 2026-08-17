<template>
  <div class="form-designer-sim">
    <div class="fd-header">
      <span class="fd-title">表单设计器</span>
      <div class="fd-tabs">
        <span class="tab active">编辑</span>
        <span class="tab">预览</span>
      </div>
    </div>
    <div class="fd-body">
      <div class="fd-palette">
        <div class="palette-title">组件</div>
        <div class="palette-item" v-for="item in formItems" :key="item">
          <span class="item-dot"></span>{{ item }}
        </div>
      </div>
      <div class="fd-canvas" :class="{ highlight: focus === 'schema' }">
        <div class="form-preview" :class="{ highlight: focus === 'preview' }">
          <div class="preview-title">申请表单预览</div>
          <div class="form-field">
            <label>主机名 <span class="required">*</span></label>
            <div class="field-input">请输入主机名</div>
          </div>
          <div class="form-row">
            <div class="form-field half">
              <label>CPU 核数</label>
              <div class="field-input">4</div>
            </div>
            <div class="form-field half">
              <label>内存 (GB)</label>
              <div class="field-input">8</div>
            </div>
          </div>
          <div class="form-field">
            <label>操作系统</label>
            <div class="field-select">CentOS 7 ▼</div>
          </div>
          <div class="form-field">
            <label>申请理由 <span class="required">*</span></label>
            <div class="field-textarea">请输入申请理由...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const formItems = ['单行输入', '多行文本', '数字输入', '下拉选择', '日期选择', '文件上传']
</script>

<style scoped lang="scss">
.form-designer-sim {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.fd-header {
  height: 48px;
  background: #fafbfc;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.fd-title { font-size: 14px; font-weight: 600; color: #1a1a2e; }

.fd-tabs { display: flex; gap: 4px; }

.tab {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;

  &.active { background: #667eea; color: #fff; }
}

.fd-body { flex: 1; display: flex; overflow: hidden; }

.fd-palette {
  width: 140px;
  background: #fafbfc;
  border-right: 1px solid #e5e7eb;
  padding: 12px;
}

.palette-title {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  cursor: grab;
  margin-bottom: 4px;

  &:hover { background: #f0f0f0; }
}

.item-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #667eea;
}

.fd-canvas {
  flex: 1;
  background: #f8f9fb;
  padding: 24px;
  overflow-y: auto;
  transition: all 0.3s;

  &.highlight {
    box-shadow: inset 0 0 0 3px rgba(102, 126, 234, 0.3);
  }
}

.form-preview {
  max-width: 500px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;

  &.highlight {
    border: 2px solid #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
  }
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
}

.form-field {
  margin-bottom: 16px;

  label {
    display: block;
    font-size: 13px;
    color: #374151;
    margin-bottom: 6px;
    font-weight: 500;
  }

  .required { color: #ef4444; }
}

.form-row {
  display: flex;
  gap: 16px;

  .half { flex: 1; }
}

.field-input, .field-select, .field-textarea {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  color: #94a3b8;
  background: #f9fafb;
}

.field-textarea {
  min-height: 80px;
}
</style>
