<template>
  <div class="presentation-player" @keydown="handleKeydown" tabindex="0" ref="playerRef">
    <!-- 顶部工具栏 -->
    <div class="top-bar">
      <button class="back-btn" @click="goBack">← 返回目录</button>
      <div class="scene-info">
        <span class="scene-title">{{ scene.title }}</span>
        <span class="step-count">步骤 {{ currentStep + 1 }} / {{ scene.steps.length }}</span>
      </div>
      <div class="role-badge" :style="{ '--theme-color': scene.themeColor }">
        <span class="role-avatar">{{ scene.roleLabel.charAt(0) }}</span>
        <span class="role-name">{{ scene.roleLabel }}</span>
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="player-body">
      <!-- 左侧步骤栏 -->
      <div class="step-sidebar">
        <div
          v-for="(step, index) in scene.steps"
          :key="index"
          :class="['step-item', { active: index === currentStep, completed: index < currentStep }]"
          @click="goToStep(index)"
        >
          <div class="step-num" :style="index <= currentStep ? { background: scene.themeColor } : {}">
            <span v-if="index < currentStep">✓</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-label">{{ step.title || `步骤 ${index + 1}` }}</div>
        </div>
      </div>

      <!-- 中间模拟区 -->
      <div class="screen-area">
        <transition :name="transitionName" mode="out-in">
          <component
            :is="screenComponent"
            :key="currentStep"
            :focus="currentStepData.focus"
          />
        </transition>
      </div>

      <!-- 右侧信息栏 -->
      <div class="info-panel">
        <div class="info-step-header">
          <span class="info-step-badge" :style="{ background: scene.themeColor }">
            Step {{ currentStep + 1 }}
          </span>
          <span class="info-step-title">{{ currentStepData.title }}</span>
        </div>
        <div class="info-narration">
          <span class="narration-icon">📝</span>
          <span>{{ currentStepData.narration }}</span>
        </div>
        <div v-if="currentStepData.highlight" class="info-highlight">
          <span class="highlight-label">🎯 核心亮点</span>
          <span class="highlight-text">{{ currentStepData.highlight }}</span>
        </div>
        <div class="info-nav">
          <button class="nav-btn" :disabled="currentStep === 0" @click="prevStep">◀ 上一步</button>
          <button class="nav-btn primary" :disabled="isLastStep" @click="nextStep" :style="{ background: scene.themeColor }">
            下一步 ▶
          </button>
        </div>
      </div>
    </div>

    <!-- 底部快捷键 -->
    <div class="bottom-bar">
      <span class="shortcut"><kbd>←</kbd> 上一步</span>
      <span class="shortcut"><kbd>→</kbd> 下一步</span>
      <span class="shortcut"><kbd>ESC</kbd> 返回目录</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Scene } from '@/types/presentation'
import { getSceneById, getPrevScene, getNextScene } from '@/data/presentations'

import LoginSim from '@/components/presentation/screens/LoginSim.vue'
import DashboardSim from '@/components/presentation/screens/DashboardSim.vue'
import FlowDesignerSim from '@/components/presentation/screens/FlowDesignerSim.vue'
import FormDesignerSim from '@/components/presentation/screens/FormDesignerSim.vue'
import TaskDetailSim from '@/components/presentation/screens/TaskDetailSim.vue'
import CapabilitySim from '@/components/presentation/screens/CapabilitySim.vue'
import ApiDemoSim from '@/components/presentation/screens/ApiDemoSim.vue'
import ApplySim from '@/components/presentation/screens/ApplySim.vue'
import SummarySim from '@/components/presentation/screens/SummarySim.vue'
import MyApplicationsSim from '@/components/presentation/screens/MyApplicationsSim.vue'
import TodoListSim from '@/components/presentation/screens/TodoListSim.vue'
import ProcessConfigSim from '@/components/presentation/screens/ProcessConfigSim.vue'
import TaskJobSim from '@/components/presentation/screens/TaskJobSim.vue'
import WebhookSim from '@/components/presentation/screens/WebhookSim.vue'
import EventLogSim from '@/components/presentation/screens/EventLogSim.vue'
import ProcessOverviewSim from '@/components/presentation/screens/ProcessOverviewSim.vue'
import IntegrationSim from '@/components/presentation/screens/IntegrationSim.vue'
import ArchOverviewSim from '@/components/presentation/screens/ArchOverviewSim.vue'
import ValueDashboardSim from '@/components/presentation/screens/ValueDashboardSim.vue'
import FlowCanvasSim from '@/components/presentation/screens/FlowCanvasSim.vue'
import FlowCheckSim from '@/components/presentation/screens/FlowCheckSim.vue'
import AutoProcessSim from '@/components/presentation/screens/AutoProcessSim.vue'
import DemoSummarySim from '@/components/presentation/screens/DemoSummarySim.vue'

const props = defineProps<{ sceneId: string }>()
const router = useRouter()
const playerRef = ref<HTMLElement>()

const screenMap: Record<string, any> = {
  LoginSim,
  DashboardSim,
  FlowDesignerSim,
  FormDesignerSim,
  TaskDetailSim,
  CapabilitySim,
  ApiDemoSim,
  ApplySim,
  SummarySim,
  MyApplicationsSim,
  TodoListSim,
  ProcessConfigSim,
  TaskJobSim,
  WebhookSim,
  EventLogSim,
  ProcessOverviewSim,
  IntegrationSim,
  ArchOverviewSim,
  ValueDashboardSim,
  FlowCanvasSim,
  FlowCheckSim,
  AutoProcessSim,
  DemoSummarySim,
}

const scene = computed<Scene>(() => getSceneById(props.sceneId) || getSceneById('overview')!)
const currentStep = ref(0)
const transitionName = ref('slide-left')

const currentStepData = computed(() => scene.value.steps[currentStep.value])
const screenComponent = computed(() => screenMap[currentStepData.value.component])
const isLastStep = computed(() => currentStep.value >= scene.value.steps.length - 1)

function prevStep() {
  if (currentStep.value > 0) {
    transitionName.value = 'slide-right'
    currentStep.value--
  } else {
    const prev = getPrevScene(scene.value.id)
    if (prev) router.push(`/presentation/${prev.id}`)
  }
}

function nextStep() {
  if (!isLastStep.value) {
    transitionName.value = 'slide-left'
    currentStep.value++
  } else {
    const next = getNextScene(scene.value.id)
    if (next) router.push(`/presentation/${next.id}`)
  }
}

function goToStep(index: number) {
  transitionName.value = index > currentStep.value ? 'slide-left' : 'slide-right'
  currentStep.value = index
}

function goBack() {
  router.push('/presentation')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') prevStep()
  else if (e.key === 'ArrowRight' || e.key === ' ') {
    e.preventDefault()
    nextStep()
  }
  else if (e.key === 'Escape') goBack()
}

onMounted(() => {
  playerRef.value?.focus()
})
</script>

<style scoped lang="scss">
.presentation-player {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
  outline: none;
}

/* 顶部工具栏 */
.top-bar {
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 16px;
  flex-shrink: 0;
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
  white-space: nowrap;

  &:hover { background: #f5f7fa; color: #1a1a2e; }
}

.scene-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scene-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.step-count {
  font-size: 13px;
  color: #94a3b8;
  padding: 4px 10px;
  background: #f5f7fa;
  border-radius: 10px;
}

.role-badge {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--theme-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.role-name {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

/* 三栏布局 */
.player-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧步骤栏 */
.step-sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 12px 8px;
  overflow-y: auto;
  flex-shrink: 0;
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

  &:hover { background: #f5f7fa; }

  &.active {
    background: rgba(102, 126, 234, 0.1);
    .step-num { color: #fff; }
    .step-label { color: #667eea; font-weight: 600; }
  }

  &.completed {
    .step-num { background: #10b981; color: #fff; }
    .step-label { color: #94a3b8; }
  }
}

.step-num {
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

.step-label {
  font-size: 13px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 中间模拟区 */
.screen-area {
  flex: 1;
  overflow: hidden;
  background: #fff;
}

/* 右侧信息栏 */
.info-panel {
  width: 340px;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 16px;
  flex-shrink: 0;
}

.info-step-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-step-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.info-step-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.info-narration {
  flex: 1;
  font-size: 14px;
  line-height: 1.9;
  color: #374151;
  overflow-y: auto;
}

.narration-icon { font-size: 16px; flex-shrink: 0; margin-top: 2px; }

.info-highlight {
  padding: 14px 16px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%);
  border-radius: 10px;
  border-left: 3px solid #3b82f6;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.highlight-label {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.highlight-text {
  font-size: 14px;
  font-weight: 500;
  color: #1e40af;
  line-height: 1.5;
}

.info-nav {
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

  &:hover:not(:disabled) { border-color: #d1d5db; background: #f9fafb; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }

  &.primary {
    color: #fff;
    border-color: transparent;
    &:hover:not(:disabled) { opacity: 0.9; }
  }
}

/* 底部快捷键 */
.bottom-bar {
  height: 36px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  flex-shrink: 0;
}

.shortcut {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}

kbd {
  display: inline-block;
  padding: 2px 6px;
  background: #f5f7fa;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  font-family: monospace;
  color: #64748b;
}

/* 过渡动画 */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-left-enter-from { transform: translateX(30px); opacity: 0; }
.slide-left-leave-to { transform: translateX(-30px); opacity: 0; }
.slide-right-enter-from { transform: translateX(-30px); opacity: 0; }
.slide-right-leave-to { transform: translateX(30px); opacity: 0; }
</style>
