<template>
  <div class="player-controls">
    <div class="controls-left">
      <button class="ctrl-btn" :disabled="!hasPrevScenario" @click="$emit('prevScenario')" title="上一场景">← 上一场景</button>
      <button class="ctrl-btn" :disabled="stepIndex === 0" @click="$emit('prev')" title="上一步 (←)">上一步</button>
    </div>

    <div class="controls-center">
      <div class="keyboard-hints">
        <span class="hint"><kbd>←</kbd><kbd>→</kbd> 翻页</span>
        <span class="hint"><kbd>Space</kbd> 下一步</span>
        <span class="hint"><kbd>ESC</kbd> 返回</span>
        <span class="hint"><kbd>R</kbd> 重播</span>
      </div>
    </div>

    <div class="controls-right">
      <button class="ctrl-btn next-btn" :disabled="stepIndex === total - 1" @click="$emit('next')" title="下一步 (→ / Space)">下一步 →</button>
      <button class="ctrl-btn auto-btn" :class="{ active: isAutoPlaying }" @click="$emit('toggleAutoPlay')">
        {{ isAutoPlaying ? '⏸ 暂停' : '▶ 自动' }}
      </button>
      <button class="ctrl-btn" @click="$emit('reset')" title="重播 (R)">⟳ 重播</button>
      <button class="ctrl-btn" :disabled="!hasNextScenario" @click="$emit('nextScenario')" title="下一场景">下一场景 →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  stepIndex: number
  total: number
  isAutoPlaying: boolean
  hasPrevScenario?: boolean
  hasNextScenario?: boolean
}>()

defineEmits<{
  prev: []
  next: []
  reset: []
  toggleAutoPlay: []
  prevScenario: []
  nextScenario: []
}>()
</script>

<style scoped>
.player-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  flex-shrink: 0;
}

.controls-left, .controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.controls-center {
  flex: 1;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.ctrl-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.ctrl-btn:hover:not(:disabled) {
  border-color: var(--brand);
  color: var(--brand);
  background: var(--brand-softer);
}

.ctrl-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.next-btn {
  background: var(--brand);
  color: #fff;
  border-color: var(--brand);
}

.next-btn:hover:not(:disabled) {
  background: var(--brand-strong);
  border-color: var(--brand-strong);
  color: #fff;
}

.auto-btn.active {
  background: var(--success-bg);
  color: var(--success);
  border-color: var(--success);
}

/* 快捷键提示 */
.keyboard-hints {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}
.hint {
  font-size: 11px;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
}
.hint kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 4px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 3px;
  font-size: 10px;
  font-family: inherit;
  color: var(--text-secondary);
  line-height: 1;
}
</style>
