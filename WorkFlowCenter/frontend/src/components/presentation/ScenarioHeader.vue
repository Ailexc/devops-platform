<template>
  <div class="scenario-header">
    <div class="header-left">
      <button class="back-btn" @click="$emit('back')">← 返回</button>
      <span class="scene-title">{{ scene.title }}</span>
      <span class="step-badge">步骤 {{ currentStep + 1 }}/{{ scene.steps.length }}</span>
    </div>
    <div class="header-right">
      <span class="role-badge" :style="{ '--theme-color': scene.themeColor }">
        <span class="role-icon">👤</span>
        {{ scene.roleLabel }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Scene } from '@/types/presentation'

defineProps<{
  scene: Scene
  currentStep: number
}>()

defineEmits<{
  back: []
}>()
</script>

<style scoped lang="scss">
.scenario-header {
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;

  &:hover {
    background: #f5f7fa;
    color: #1a1a2e;
  }
}

.scene-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.step-badge {
  font-size: 12px;
  color: #94a3b8;
  padding: 4px 10px;
  background: #f5f7fa;
  border-radius: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  background: color-mix(in srgb, var(--theme-color) 10%, transparent);
  color: var(--theme-color);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
}

.role-icon {
  font-size: 14px;
}
</style>
