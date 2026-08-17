<template>
  <div class="presentation-hub">
    <div class="hub-background"></div>
    <div class="hub-content">
      <!-- 页头 -->
      <div class="hub-header">
        <div class="header-icon">🎬</div>
        <h1 class="header-title">系统宣讲</h1>
        <p class="header-subtitle">流程驱动的业务自动化平台 · 全方位展示系统能力</p>
        <div class="header-stats">
          <span class="stat-badge">{{ scenes.length }} 个场景</span>
          <span class="stat-badge">{{ totalSteps }} 个步骤</span>
          <span class="stat-badge">~8 分钟</span>
        </div>
      </div>

      <!-- 场景卡片 -->
      <div class="scene-grid">
        <div
          v-for="(scene, index) in scenes"
          :key="scene.id"
          class="scene-card"
          :style="{ '--theme-color': scene.themeColor }"
          @click="goToScene(scene.id)"
        >
          <div class="card-index">{{ index + 1 }}</div>
          <div class="card-body">
            <h3 class="card-title">{{ scene.title }}</h3>
            <p class="card-description">{{ scene.description }}</p>
            <div class="card-meta">
              <span class="meta-item">🕐 {{ scene.duration }}</span>
              <span class="meta-item">📋 {{ scene.steps.length }} 步</span>
            </div>
          </div>
          <div class="card-arrow">开始演示 →</div>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <div class="hub-footer">
        <span class="shortcut-hint">← → 翻页</span>
        <span class="shortcut-hint">Space 下一步</span>
        <span class="shortcut-hint">ESC 返回目录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { scenes } from '@/data/presentations'

const router = useRouter()

const totalSteps = computed(() => scenes.reduce((sum, s) => sum + s.steps.length, 0))

function goToScene(sceneId: string) {
  router.push(`/presentation/${sceneId}`)
}
</script>

<style scoped lang="scss">
.presentation-hub {
  width: 100%;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.hub-background {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4ecf7 100%);
  z-index: 0;

  &::before {
    content: '';
    position: absolute;
    top: -20%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(102, 126, 234, 0.15) 0%, transparent 70%);
    border-radius: 50%;
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -20%;
    left: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(118, 75, 162, 0.1) 0%, transparent 70%);
    border-radius: 50%;
  }
}

.hub-content {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 60px 24px 40px;
}

.hub-header {
  text-align: center;
  margin-bottom: 48px;
}

.header-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.header-title {
  font-size: 40px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px;
}

.header-subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0 0 20px;
}

.header-stats {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.stat-badge {
  padding: 6px 16px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.scene-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 16px;

  &:hover {
    border-color: var(--theme-color);
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);

    .card-arrow {
      color: var(--theme-color);
      transform: translateX(4px);
    }
  }
}

.card-index {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--theme-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
}

.card-body {
  flex: 1;
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.card-description {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 12px;
  line-height: 1.6;
}

.card-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  font-size: 13px;
  color: #94a3b8;
}

.card-arrow {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
  transition: all 0.3s;
}

.hub-footer {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.shortcut-hint {
  font-size: 13px;
  color: #94a3b8;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
}

@media (max-width: 768px) {
  .scene-grid {
    grid-template-columns: 1fr;
  }
}
</style>
