<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getScene, getSceneIndex, scenes } from '@/data/presentations'
import { simulations } from './simulations'
import type { PresentationStep } from '@/types/presentation'

const router = useRouter()
const route = useRoute()

const sceneId = computed(() => route.params.sceneId as string)
const scene = computed(() => getScene(sceneId.value))
const sceneIndex = computed(() => getSceneIndex(sceneId.value))
const totalScenes = computed(() => scenes.length)

const currentStepIndex = ref(0)
const currentStep = computed(() => scene.value?.steps[currentStepIndex.value])
const totalSteps = computed(() => scene.value?.steps.length ?? 0)
const isFirstStep = computed(() => currentStepIndex.value === 0)
const isLastStep = computed(() => currentStepIndex.value === totalSteps.value - 1)

// 过渡动画
const transitionName = ref('slide-right')

// 计算进度百分比
const progress = computed(() => {
  if (!totalSteps.value) return 0
  return ((currentStepIndex.value + 1) / totalSteps.value) * 100
})

// 获取当前页面模拟组件
const currentSimComponent = computed(() => {
  if (!currentStep.value) return null
  return simulations[currentStep.value.pageComponent] || null
})

const currentSimProps = computed(() => {
  return currentStep.value?.pageProps || {}
})

// 导航到指定步骤
function goToStep(index: number) {
  if (!scene.value) return
  if (index < 0 || index >= totalSteps.value) return

  transitionName.value = index > currentStepIndex.value ? 'slide-right' : 'slide-left'
  currentStepIndex.value = index
}

// 下一步
function nextStep() {
  if (isLastStep.value) {
    // 如果是最后一个场景的最后一步，返回目录
    if (sceneIndex.value >= totalScenes.value - 1) {
      router.push('/presentation')
    } else {
      // 跳转到下一个场景
      const nextScene = scenes[sceneIndex.value + 1]
      if (nextScene) {
        router.push(`/presentation/${nextScene.id}`)
      }
    }
    return
  }
  goToStep(currentStepIndex.value + 1)
}

// 上一步
function prevStep() {
  if (isFirstStep.value) {
    // 如果是第一个场景的第一步，返回目录
    if (sceneIndex.value <= 0) {
      router.push('/presentation')
    } else {
      // 跳转到上一个场景的最后一步
      const prevScene = scenes[sceneIndex.value - 1]
      if (prevScene) {
        router.push(`/presentation/${prevScene.id}`)
      }
    }
    return
  }
  goToStep(currentStepIndex.value - 1)
}

// 返回目录
function backToHub() {
  router.push('/presentation')
}

// 键盘事件处理
function handleKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowRight':
    case ' ':
      e.preventDefault()
      nextStep()
      break
    case 'ArrowLeft':
      e.preventDefault()
      prevStep()
      break
    case 'Escape':
      e.preventDefault()
      backToHub()
      break
  }
}

// 监听路由变化，更新步骤
watch(
  () => route.params.sceneId,
  () => {
    currentStepIndex.value = 0
  }
)

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="presentation-player" v-if="scene">
    <!-- 顶部工具栏 -->
    <div class="player-toolbar">
      <div class="toolbar-left">
        <button class="toolbar-btn back-btn" @click="backToHub">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          <span>返回目录</span>
        </button>
      </div>
      <div class="toolbar-center">
        <span class="scene-title">{{ scene.title }}</span>
        <span class="step-counter">步骤 {{ currentStepIndex + 1 }} / {{ totalSteps }}</span>
      </div>
      <div class="toolbar-right">
        <div class="role-badge" v-if="scene.role">
          <span class="role-avatar">{{ scene.role[0] }}</span>
          <span class="role-info">
            <span class="role-name">{{ scene.role }}</span>
            <span class="role-desc">{{ scene.subtitle }}</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="player-content">
      <!-- 左侧：步骤指示器 -->
      <div class="steps-sidebar">
        <div class="steps-list">
          <button
            v-for="(step, index) in scene.steps"
            :key="step.id"
            class="step-item"
            :class="{
              active: index === currentStepIndex,
              completed: index < currentStepIndex
            }"
            @click="goToStep(index)"
          >
            <span class="step-number">{{ index + 1 }}</span>
            <span class="step-label">{{ step.title }}</span>
          </button>
        </div>
      </div>

      <!-- 中间：页面模拟区域 -->
      <div class="simulation-area">
        <transition :name="transitionName" mode="out-in">
          <div :key="currentStep?.id" class="sim-container">
            <component
              :is="currentSimComponent"
              v-if="currentSimComponent"
              v-bind="currentSimProps"
            />
          </div>
        </transition>
      </div>

      <!-- 右侧：说明卡片 -->
      <div class="info-sidebar">
        <div class="info-card">
          <div class="card-header">
            <span class="card-step">Step {{ currentStepIndex + 1 }}</span>
            <h3 class="card-title">{{ currentStep?.title }}</h3>
          </div>
          <p class="card-description">{{ currentStep?.description }}</p>
          <div class="card-narration" v-if="currentStep?.narration">
            <span class="narration-icon">📝</span>
            <span>{{ currentStep.narration }}</span>
          </div>
          <div class="card-highlight">
            <span class="highlight-icon">✨</span>
            <span>{{ currentStep?.highlight }}</span>
          </div>
        </div>

        <!-- 导航按钮 -->
        <div class="nav-buttons">
          <button class="nav-btn prev" :disabled="isFirstStep && sceneIndex <= 0" @click="prevStep">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6"/>
            </svg>
            <span>{{ isFirstStep ? '上一场景' : '上一步' }}</span>
          </button>
          <button class="nav-btn next" @click="nextStep">
            <span>{{ isLastStep ? (sceneIndex >= totalScenes - 1 ? '结束演示' : '下一场景') : '下一步' }}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 底部进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: `${progress}%`, background: scene.color }"></div>
    </div>

    <!-- 快捷键提示 -->
    <div class="keyboard-hints">
      <span class="hint"><kbd>←</kbd> 上一步</span>
      <span class="hint"><kbd>→</kbd> 下一步</span>
      <span class="hint"><kbd>ESC</kbd> 返回目录</span>
    </div>
  </div>

  <!-- 场景不存在 -->
  <div v-else class="player-empty">
    <div class="empty-content">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 8v4M12 16h.01"/>
      </svg>
      <h2>场景不存在</h2>
      <p>请返回目录选择正确的场景</p>
      <button class="nav-btn next" @click="backToHub">返回目录</button>
    </div>
  </div>
</template>

<style scoped>
.presentation-player {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f8fafc;
  color: #1a1a2e;
  z-index: 9990;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部工具栏 */
.player-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  z-index: 10001;
}

.toolbar-left, .toolbar-right {
  flex: 1;
}

.toolbar-right {
  display: flex;
  justify-content: flex-end;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scene-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.step-counter {
  font-size: 13px;
  color: #64748b;
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 12px;
}

.role-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: #f8fafc;
  border-radius: 10px;
}

.role-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.role-info {
  display: flex;
  flex-direction: column;
}

.role-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.role-desc {
  font-size: 11px;
  color: #94a3b8;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.toolbar-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
}

.toolbar-btn svg {
  width: 16px;
  height: 16px;
}

/* 主内容区 */
.player-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧步骤列表 */
.steps-sidebar {
  width: 180px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  padding: 16px 0;
  overflow-y: auto;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.step-item:hover {
  background: #f8fafc;
}

.step-item.active {
  background: #eef2ff;
  border-right: 3px solid #667eea;
}

.step-item.completed {
  opacity: 0.7;
}

.step-number {
  width: 24px;
  height: 24px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  flex-shrink: 0;
}

.step-item.active .step-number {
  background: #667eea;
  color: #fff;
}

.step-item.completed .step-number {
  background: #10b981;
  color: #fff;
}

.step-label {
  font-size: 13px;
  color: #475569;
}

.step-item.active .step-label {
  color: #1a1a2e;
  font-weight: 500;
}

/* 中间模拟区域 */
.simulation-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sim-container {
  flex: 1;
  overflow: hidden;
}

/* 右侧信息栏 */
.info-sidebar {
  width: 320px;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.info-card {
  flex: 1;
}

.card-header {
  margin-bottom: 12px;
}

.card-step {
  font-size: 11px;
  font-weight: 600;
  color: #667eea;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
  margin-bottom: 4px;
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.card-description {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.card-narration {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 12px;
}

.narration-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.card-highlight {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #4f46e5;
  line-height: 1.5;
}

.highlight-icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* 导航按钮 */
.nav-buttons {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.nav-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn svg {
  width: 16px;
  height: 16px;
}

.nav-btn.prev {
  background: #f1f5f9;
  color: #475569;
}

.nav-btn.prev:hover:not(:disabled) {
  background: #e2e8f0;
  color: #1e293b;
}

.nav-btn.prev:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.nav-btn.next {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.nav-btn.next:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

/* 进度条 */
.progress-bar {
  height: 3px;
  background: #e2e8f0;
}

.progress-fill {
  height: 100%;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 0 2px 2px 0;
}

/* 快捷键提示 */
.keyboard-hints {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 20px;
  z-index: 10001;
  background: #fff;
  padding: 6px 14px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.hint {
  font-size: 11px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  font-family: monospace;
  font-size: 10px;
  color: #64748b;
}

/* 过渡动画 */
.slide-right-enter-active,
.slide-right-leave-active,
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 场景不存在 */
.player-empty {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f8fafc;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
}

.empty-content svg {
  width: 64px;
  height: 64px;
  color: #cbd5e1;
  margin-bottom: 24px;
}

.empty-content h2 {
  font-size: 24px;
  margin: 0 0 12px 0;
  color: #1a1a2e;
}

.empty-content p {
  font-size: 16px;
  color: #64748b;
  margin: 0 0 32px 0;
}
</style>
