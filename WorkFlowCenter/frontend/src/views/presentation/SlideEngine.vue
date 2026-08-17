<template>
  <div class="slide-engine" @keydown="handleKeydown" tabindex="0" ref="slideContainer">
    <!-- 顶部标题栏 -->
    <div class="slide-header">
      <h1>{{ currentScene.title }}</h1>
      <div class="slide-controls">
        <el-button-group>
          <el-button :icon="ArrowLeft" @click="prevSlide" :disabled="currentSlideIndex === 0" />
          <el-button @click="toggleAutoPlay">
            <el-icon v-if="isAutoPlaying"><VideoPause /></el-icon>
            <el-icon v-else><VideoPlay /></el-icon>
          </el-button>
          <el-button :icon="ArrowRight" @click="nextSlide" :disabled="currentSlideIndex === currentSlides.length - 1" />
        </el-button-group>
        <span class="slide-progress">{{ currentSlideIndex + 1 }} / {{ currentSlides.length }}</span>
      </div>
    </div>

    <!-- Slide 内容区 -->
    <div class="slide-content">
      <transition name="slide-fade" mode="out-in">
        <div :key="currentSlideIndex" class="slide-item">
          <!-- Hero 类型 -->
          <div v-if="currentSlide.type === 'hero'" class="slide-hero">
            <div class="hero-background" :style="{ background: currentSlide.background || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }">
              <h1>{{ currentSlide.title }}</h1>
              <h2 v-if="currentSlide.subtitle">{{ currentSlide.subtitle }}</h2>
              <p v-if="currentSlide.description">{{ currentSlide.description }}</p>
            </div>
          </div>

          <!-- 文字页类型 -->
          <div v-else-if="currentSlide.type === 'text'" class="slide-text">
            <h2>{{ currentSlide.title }}</h2>
            <div class="text-content">
              <p v-if="currentSlide.content">{{ currentSlide.content }}</p>
              <ul v-if="currentSlide.bullets && currentSlide.bullets.length">
                <li v-for="(bullet, index) in currentSlide.bullets" :key="index">{{ bullet }}</li>
              </ul>
            </div>
          </div>

          <!-- 截图页类型 -->
          <div v-else-if="currentSlide.type === 'image'" class="slide-image">
            <h2>{{ currentSlide.title }}</h2>
            <div class="image-container">
              <img :src="currentSlide.image" :alt="currentSlide.title" />
            </div>
            <p v-if="currentSlide.caption" class="image-caption">{{ currentSlide.caption }}</p>
          </div>

          <!-- 代码页类型 -->
          <div v-else-if="currentSlide.type === 'code'" class="slide-code">
            <h2>{{ currentSlide.title }}</h2>
            <div class="code-container">
              <pre><code>{{ currentSlide.code }}</code></pre>
            </div>
            <p v-if="currentSlide.description" class="code-description">{{ currentSlide.description }}</p>
          </div>
        </div>
      </transition>
    </div>

    <!-- 底部导航栏 -->
    <div class="slide-footer">
      <div class="slide-dots">
        <span 
          v-for="(slide, index) in currentSlides" 
          :key="index" 
          :class="['dot', { active: index === currentSlideIndex }]"
          @click="goToSlide(index)"
        ></span>
      </div>
      <div class="slide-navigation">
        <el-button @click="prevSlide" :disabled="currentSlideIndex === 0">
          <el-icon><ArrowLeft /></el-icon> 上一步
        </el-button>
        <el-button @click="nextSlide" :disabled="currentSlideIndex === currentSlides.length - 1">
          下一步 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 场景选择器 -->
    <div class="scene-selector" v-if="showSceneSelector">
      <el-select v-model="currentSceneId" placeholder="选择演示场景" @change="switchScene">
        <el-option
          v-for="scene in scenes"
          :key="scene.id"
          :label="scene.title"
          :value="scene.id"
        />
      </el-select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ArrowLeft, ArrowRight, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { scenes } from '@/data/presentation-slides'

const slideContainer = ref(null)
const currentSceneId = ref(scenes[0]?.id || '')
const currentSlideIndex = ref(0)
const isAutoPlaying = ref(false)
const showSceneSelector = ref(true)
let autoPlayTimer = null

// 当前场景
const currentScene = computed(() => {
  return scenes.find(s => s.id === currentSceneId.value) || scenes[0]
})

// 当前场景的 slides
const currentSlides = computed(() => {
  return currentScene.value?.slides || []
})

// 当前 slide
const currentSlide = computed(() => {
  return currentSlides.value[currentSlideIndex.value] || {}
})

// 切换场景
const switchScene = () => {
  currentSlideIndex.value = 0
  stopAutoPlay()
}

// 上一页
const prevSlide = () => {
  if (currentSlideIndex.value > 0) {
    currentSlideIndex.value--
  }
}

// 下一页
const nextSlide = () => {
  if (currentSlideIndex.value < currentSlides.value.length - 1) {
    currentSlideIndex.value++
  }
}

// 跳转到指定页
const goToSlide = (index) => {
  currentSlideIndex.value = index
}

// 切换自动播放
const toggleAutoPlay = () => {
  if (isAutoPlaying.value) {
    stopAutoPlay()
  } else {
    startAutoPlay()
  }
}

// 开始自动播放
const startAutoPlay = () => {
  isAutoPlaying.value = true
  autoPlayTimer = setInterval(() => {
    if (currentSlideIndex.value < currentSlides.value.length - 1) {
      currentSlideIndex.value++
    } else {
      stopAutoPlay()
    }
  }, 5000)
}

// 停止自动播放
const stopAutoPlay = () => {
  isAutoPlaying.value = false
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (e.key === 'ArrowLeft') {
    prevSlide()
  } else if (e.key === 'ArrowRight') {
    nextSlide()
  } else if (e.key === ' ') {
    e.preventDefault()
    toggleAutoPlay()
  }
}

onMounted(() => {
  // 聚焦容器以接收键盘事件
  if (slideContainer.value) {
    slideContainer.value.focus()
  }
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<style scoped>
.slide-engine {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  outline: none;
}

.slide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.slide-header h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.slide-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slide-progress {
  font-size: 14px;
  color: #606266;
}

.slide-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  overflow: hidden;
}

.slide-item {
  width: 100%;
  max-width: 1200px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Hero 类型样式 */
.slide-hero {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-background {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  text-align: center;
  padding: 40px;
}

.hero-background h1 {
  font-size: 48px;
  margin: 0 0 16px 0;
}

.hero-background h2 {
  font-size: 24px;
  margin: 0 0 24px 0;
  opacity: 0.9;
}

.hero-background p {
  font-size: 18px;
  margin: 0;
  opacity: 0.8;
  max-width: 600px;
}

/* 文字页样式 */
.slide-text {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.slide-text h2 {
  margin: 0 0 24px 0;
  font-size: 32px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 12px;
}

.text-content {
  font-size: 18px;
  line-height: 1.8;
  color: #606266;
}

.text-content p {
  margin: 0 0 16px 0;
}

.text-content ul {
  margin: 0;
  padding-left: 24px;
}

.text-content li {
  margin-bottom: 12px;
}

/* 截图页样式 */
.slide-image {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.slide-image h2 {
  margin: 0 0 24px 0;
  font-size: 32px;
  color: #303133;
  border-bottom: 2px solid #67c23a;
  padding-bottom: 12px;
}

.image-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.image-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-caption {
  margin: 16px 0 0 0;
  font-size: 16px;
  color: #909399;
  text-align: center;
}

/* 代码页样式 */
.slide-code {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.slide-code h2 {
  margin: 0 0 24px 0;
  font-size: 32px;
  color: #303133;
  border-bottom: 2px solid #e6a23c;
  padding-bottom: 12px;
}

.code-container {
  flex: 1;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 24px;
  overflow: auto;
}

.code-container pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #d4d4d4;
}

.code-description {
  margin: 16px 0 0 0;
  font-size: 16px;
  color: #909399;
}

/* 底部导航栏 */
.slide-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.slide-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #dcdfe6;
  cursor: pointer;
  transition: all 0.3s;
}

.dot.active {
  background: #409eff;
  transform: scale(1.2);
}

.dot:hover {
  background: #409eff;
  opacity: 0.8;
}

.slide-navigation {
  display: flex;
  gap: 12px;
}

/* 场景选择器 */
.scene-selector {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 100;
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateX(30px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-30px);
  opacity: 0;
}
</style>
