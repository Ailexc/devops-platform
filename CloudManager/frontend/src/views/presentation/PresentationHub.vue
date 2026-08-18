<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { sceneMetas } from '@/data/presentations'

const router = useRouter()

const totalDuration = computed(() => {
  return sceneMetas.reduce((sum, s) => sum + s.duration, 0)
})

const totalSteps = computed(() => {
  return sceneMetas.reduce((sum, s) => sum + s.stepCount, 0)
})

// 图标映射
const iconPaths: Record<string, string> = {
  eye: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 100 6 3 3 0 000-6z',
  cloud: 'M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z',
  ticket: 'M15 5v2m0 4v2m0 4v2M5 5a2 2 0 0 0-2 2v3a2 2 0 1 1 0 4v3a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3a2 2 0 1 1 0-4V7a2 2 0 0 0-2-2H5z',
  topology: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  cost: 'M12 2v20m5-17H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H7',
  chain: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
}

function startScene(id: string) {
  router.push(`/presentation/${id}`)
}
</script>

<template>
  <div class="presentation-hub">
    <!-- 页头 -->
    <div class="hub-header">
      <div class="header-content">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
          </svg>
        </div>
        <h1 class="header-title">系统演示</h1>
        <p class="header-subtitle">像 PPT 一样逐步展示系统能力，6 个场景覆盖核心亮点</p>
        <div class="header-stats">
          <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ totalDuration }} 分钟
          </span>
          <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            {{ totalSteps }} 个步骤
          </span>
          <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            键盘快捷键支持
          </span>
        </div>
      </div>
    </div>

    <!-- 场景卡片列表 -->
    <div class="scene-grid">
      <button
        v-for="(scene, index) in sceneMetas"
        :key="scene.id"
        class="scene-card"
        @click="startScene(scene.id)"
      >
        <div class="card-glow" :style="{ background: scene.color }"></div>
        <div class="card-content">
          <div class="card-header">
            <span class="card-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="card-icon" :style="{ background: `${scene.color}20`, color: scene.color }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path :d="iconPaths[scene.icon] || iconPaths.eye"/>
              </svg>
            </div>
          </div>
          <h3 class="card-title">{{ scene.title }}</h3>
          <p class="card-subtitle">{{ scene.subtitle }}</p>
          <div class="card-meta">
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {{ scene.duration }} 分钟
            </span>
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 6h16M4 12h16M4 18h7"/>
              </svg>
              {{ scene.stepCount }} 步
            </span>
          </div>
          <div class="card-action">
            <span>开始演示</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </button>
    </div>

    <!-- 底部提示 -->
    <div class="hub-footer">
      <div class="footer-hints">
        <span class="hint-item">
          <kbd>←</kbd> <kbd>→</kbd> 翻页
        </span>
        <span class="hint-item">
          <kbd>ESC</kbd> 返回目录
        </span>
        <span class="hint-item">
          <kbd>Space</kbd> 下一步
        </span>
      </div>
      <p class="footer-tip">演示结束后将返回此页面，面试官感兴趣可随时跳转实际功能</p>
    </div>
  </div>
</template>

<style scoped>
.presentation-hub {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4ecf7 100%);
  color: #1a1a2e;
  padding: 0 0 60px 0;
}

/* 页头 */
.hub-header {
  padding: 60px 40px 48px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hub-header::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, rgba(99, 102, 241, 0.08) 0%, transparent 50%);
  pointer-events: none;
}

.header-content {
  position: relative;
  z-index: 1;
}

.header-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
}

.header-icon svg {
  width: 36px;
  height: 36px;
  color: #fff;
}

.header-title {
  font-size: 40px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px 0;
}

.header-subtitle {
  font-size: 18px;
  color: #64748b;
  margin: 0 0 32px 0;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.header-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #94a3b8;
  background: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-item svg {
  width: 16px;
  height: 16px;
  color: #667eea;
}

/* 场景卡片网格 */
.scene-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  padding: 0 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.scene-card {
  position: relative;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  text-align: left;
  color: inherit;
  font: inherit;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.scene-card:hover {
  transform: translateY(-4px);
  border-color: #c7d2fe;
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.15);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  opacity: 0;
  transition: opacity 0.3s;
}

.scene-card:hover .card-glow {
  opacity: 1;
}

.card-content {
  padding: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-index {
  font-size: 32px;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.card-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.card-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #94a3b8;
}

.meta-item svg {
  width: 14px;
  height: 14px;
}

.card-action {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #667eea;
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.3s;
}

.scene-card:hover .card-action {
  opacity: 1;
  transform: translateX(0);
}

.card-action svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s;
}

.scene-card:hover .card-action svg {
  transform: translateX(4px);
}

/* 底部提示 */
.hub-footer {
  margin-top: 48px;
  text-align: center;
}

.footer-hints {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 16px;
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #94a3b8;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-family: monospace;
  font-size: 11px;
  color: #64748b;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.footer-tip {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .hub-header {
    padding: 40px 20px 32px;
  }

  .header-title {
    font-size: 28px;
  }

  .header-subtitle {
    font-size: 16px;
  }

  .header-stats {
    flex-direction: column;
    gap: 12px;
  }

  .scene-grid {
    padding: 0 20px;
    grid-template-columns: 1fr;
  }

  .footer-hints {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
