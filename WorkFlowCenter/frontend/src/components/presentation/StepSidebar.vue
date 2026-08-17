<template>
  <div class="step-sidebar">
    <div class="sidebar-title">{{ scene.title }}</div>
    <div class="step-list">
      <div
        v-for="(step, index) in scene.steps"
        :key="index"
        :class="['step-item', {
          active: index === currentStep,
          completed: index < currentStep,
        }]"
        @click="$emit('goto', index)"
      >
        <div class="step-indicator">
          <span v-if="index < currentStep" class="step-check">✓</span>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="step-label">{{ step.title || `步骤 ${index + 1}` }}</div>
      </div>
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
  goto: [index: number]
}>()
</script>

<style scoped lang="scss">
.step-sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-title {
  padding: 20px 16px 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  border-bottom: 1px solid #f0f0f0;
}

.step-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;

  &:hover {
    background: #f5f7fa;
  }

  &.active {
    background: rgba(102, 126, 234, 0.1);

    .step-indicator {
      background: #667eea;
      color: #fff;
    }

    .step-label {
      color: #667eea;
      font-weight: 600;
    }
  }

  &.completed {
    .step-indicator {
      background: #10b981;
      color: #fff;
    }

    .step-label {
      color: #94a3b8;
    }
  }
}

.step-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-check {
  font-size: 11px;
}

.step-label {
  font-size: 13px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
