<template>
  <div class="step-sidebar">
    <div class="sidebar-title">{{ scenarioTitle }}</div>
    <div class="step-list">
      <button
        v-for="(step, i) in steps"
        :key="i"
        class="step-item"
        :class="{ active: i === currentIndex, done: i < currentIndex }"
        @click="$emit('goto', i)"
      >
        <span class="step-num">{{ i + 1 }}</span>
        <span class="step-label">{{ step.title || step.narration.slice(0, 16) }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  scenarioTitle: string
  steps: { title?: string; narration: string; component: string }[]
  currentIndex: number
}>()

defineEmits<{ goto: [index: number] }>()
</script>

<style scoped>
.step-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-title {
  padding: 14px 16px 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}
.step-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.step-item:hover { background: var(--bg-hover); color: var(--text); }
.step-item.active { background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.step-item.done { color: var(--text-tertiary); }
.step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.step-item.active .step-num { background: var(--brand); color: #fff; }
.step-item.done .step-num { background: var(--success); color: #fff; }
.step-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
