<template>
  <div class="info-panel">
    <!-- 旁白 -->
    <div class="narration-section">
      <div class="narration-icon">📝</div>
      <div class="narration-text">{{ narration }}</div>
    </div>

    <!-- 卖点 -->
    <div v-if="highlight" class="highlight-section">
      <span class="highlight-badge" :style="{ '--theme-color': themeColor }">
        🎯 {{ highlight }}
      </span>
    </div>

    <!-- 导航按钮 -->
    <div class="nav-buttons">
      <button
        class="nav-btn"
        :disabled="isFirst"
        @click="$emit('prev')"
      >
        ◀ 上一步
      </button>
      <button
        class="nav-btn primary"
        :disabled="isLast"
        @click="$emit('next')"
      >
        下一步 ▶
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  narration: string
  highlight?: string
  themeColor: string
  isFirst: boolean
  isLast: boolean
}>()

defineEmits<{
  prev: []
  next: []
}>()
</script>

<style scoped lang="scss">
.info-panel {
  width: 300px;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 24px 20px;
  gap: 24px;
}

.narration-section {
  display: flex;
  gap: 12px;
  flex: 1;
}

.narration-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.narration-text {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
}

.highlight-section {
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
}

.highlight-badge {
  display: inline-block;
  font-size: 14px;
  font-weight: 600;
  color: var(--theme-color);
}

.nav-buttons {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.nav-btn {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    border-color: #d1d5db;
    background: #f9fafb;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &.primary {
    background: #667eea;
    color: #fff;
    border-color: #667eea;

    &:hover:not(:disabled) {
      background: #5a6fd6;
      border-color: #5a6fd6;
    }
  }
}
</style>
