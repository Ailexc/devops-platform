<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { resourceApi } from '@/api'
import type { ResourceStats } from '@/types'

const router = useRouter()
const stats = ref<ResourceStats[]>([])
const loading = ref(false)

const summaryCards = ref([
  { 
    title: '资源总数', 
    value: 79, 
    icon: 'server',
    gradient: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
    trend: '+3',
    trendUp: true
  },
  { 
    title: '运行中', 
    value: 65, 
    icon: 'check-circle',
    gradient: 'linear-gradient(135deg, #11998E 0%, #38EF7D 100%)',
    trend: '+2',
    trendUp: true
  },
  { 
    title: '月度费用', 
    value: '¥35.2K', 
    icon: 'dollar',
    gradient: 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
    trend: '-8%',
    trendUp: false
  },
  { 
    title: '工单待办', 
    value: 5, 
    icon: 'file-text',
    gradient: 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
    trend: '+2',
    trendUp: true
  },
])

// 云厂商资源分布
const cloudProviders = ref([
  { 
    id: 'aws', 
    name: 'AWS', 
    icon: '☁️', 
    color: '#f97316',
    count: 32,
    running: 25,
    stopped: 5,
    error: 2,
    status: '正常'
  },
  { 
    id: 'aliyun', 
    name: '阿里云', 
    icon: '🌐', 
    color: '#3b82f6',
    count: 28,
    running: 22,
    stopped: 4,
    error: 2,
    status: '正常'
  },
  { 
    id: 'tencent', 
    name: '腾讯云', 
    icon: '🟣', 
    color: '#8b5cf6',
    count: 19,
    running: 18,
    stopped: 1,
    error: 0,
    status: '部分异常'
  },
])

// 快捷操作
const quickActions = [
  { label: '资源概览', icon: 'chart', path: '/resources/overview', color: '#667EEA' },
  { label: '工单中心', icon: 'file-text', path: '/ticket/list', color: '#11998E' },
  { label: '成本分析', icon: 'dollar', path: '/cost/trends', color: '#F5576C' },
  { label: '操作记录', icon: 'audit', path: '/audit/logs', color: '#4FACFE' },
]

// 最近工单（模拟数据）
const recentTickets = ref([
  { id: 1, title: '申请云主机 web-server-02', status: 'pending', time: '10分钟前' },
  { id: 2, title: '释放测试环境资源', status: 'executing', time: '1小时前' },
  { id: 3, title: '变更生产环境配置', status: 'success', time: '2小时前' },
  { id: 4, title: '申请数据库扩容', status: 'failed', time: '3小时前' },
])

const statusColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: '#FEF3C7', text: '#D97706' },
  executing: { bg: '#DBEAFE', text: '#2563EB' },
  success: { bg: '#D1FAE5', text: '#059669' },
  failed: { bg: '#FEE2E2', text: '#DC2626' },
}

const statusLabels: Record<string, string> = {
  pending: '待审批',
  executing: '执行中',
  success: '已完成',
  failed: '已失败',
}

function goToProvider(id: string) {
  router.push(`/resources/${id}`)
}

// 图标路径
const iconPaths: Record<string, string> = {
  server: 'M5 3a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5zm0 6a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2H5zm0 6a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2H5z',
  'check-circle': 'M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3',
  'pause-circle': 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z',
  'file-text': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 15h8M8 11h4',
  'grid': 'M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z',
  dollar: 'M12 2v20m5-17H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H7',
  audit: 'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6m-6 4h6m-6 4h4m-4 4h2',
  plus: 'M12 5v14M5 12h14',
  chart: 'M18 20V10M12 20V4M6 20v-6',
}
</script>

<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header fade-in">
      <div class="header-content">
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">欢迎回来，这是您的多云资源概览</p>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="router.push('/compute/instances')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path :d="iconPaths.plus"></path>
          </svg>
          <span>申请资源</span>
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div 
        v-for="(card, index) in summaryCards" 
        :key="card.title" 
        class="stat-card fade-in"
        :style="{ animationDelay: `${index * 0.1}s` }"
      >
        <div class="stat-card-bg" :style="{ background: card.gradient }"></div>
        <div class="stat-card-content">
          <div class="stat-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path :d="iconPaths[card.icon]"></path>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-title">{{ card.title }}</span>
            <span class="stat-value">{{ card.value }}</span>
            <div class="stat-trend" :class="{ up: card.trendUp, down: !card.trendUp }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="card.trendUp" d="M18 15l-6-6-6 6"></path>
                <path v-else d="M6 9l6 6 6-6"></path>
              </svg>
              <span>{{ card.trend }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-grid">
      <!-- 云厂商资源分布 -->
      <div class="card resource-card fade-in delay-2">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
            </svg>
            多云资源分布
          </h3>
          <button class="card-action" @click="router.push('/resources/overview')">
            查看全部
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
          </button>
        </div>
        <div class="card-body">
          <div class="cloud-providers-grid">
            <div 
              v-for="provider in cloudProviders" 
              :key="provider.id"
              class="cloud-provider-item"
              @click="goToProvider(provider.id)"
            >
              <div class="provider-header">
                <span class="provider-icon" :style="{ background: `${provider.color}15` }">{{ provider.icon }}</span>
                <div class="provider-info">
                  <span class="provider-name">{{ provider.name }}</span>
                  <span class="provider-count">{{ provider.count }} 个资源</span>
                </div>
                <span class="provider-status" :class="{ warning: provider.status === '部分异常' }">{{ provider.status }}</span>
              </div>
              <div class="provider-stats">
                <div class="provider-stat">
                  <span class="stat-dot running"></span>
                  <span>{{ provider.running }} 运行中</span>
                </div>
                <div class="provider-stat">
                  <span class="stat-dot stopped"></span>
                  <span>{{ provider.stopped }} 已停止</span>
                </div>
                <div v-if="provider.error > 0" class="provider-stat">
                  <span class="stat-dot error"></span>
                  <span>{{ provider.error }} 异常</span>
                </div>
              </div>
              <div class="provider-arrow">→</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="card quick-actions-card fade-in delay-3">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            快捷操作
          </h3>
        </div>
        <div class="card-body">
          <div class="quick-actions-grid">
            <button 
              v-for="action in quickActions" 
              :key="action.path"
              class="quick-action-item"
              @click="router.push(action.path)"
            >
              <div class="quick-action-icon" :style="{ background: `${action.color}15`, color: action.color }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path :d="iconPaths[action.icon]"></path>
                </svg>
              </div>
              <span class="quick-action-label">{{ action.label }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 最近工单 -->
      <div class="card tickets-card fade-in delay-4">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path>
              <path d="M14 2v6h6"></path>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            最近工单
          </h3>
          <button class="card-action" @click="router.push('/ticket/list')">
            查看全部
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
          </button>
        </div>
        <div class="card-body">
          <div class="ticket-list">
            <div v-for="ticket in recentTickets" :key="ticket.id" class="ticket-item">
              <div class="ticket-info">
                <span class="ticket-title">{{ ticket.title }}</span>
                <span class="ticket-time">{{ ticket.time }}</span>
              </div>
              <span 
                class="ticket-status" 
                :style="{ 
                  background: statusColors[ticket.status]?.bg, 
                  color: statusColors[ticket.status]?.text 
                }"
              >
                {{ statusLabels[ticket.status] }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.page-title {
  font-size: var(--cm-text-3xl);
  font-weight: var(--cm-font-bold);
  color: var(--cm-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--cm-text-base);
  color: var(--cm-text-secondary);
  margin: 8px 0 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--cm-color-primary-600) 0%, var(--cm-color-primary-700) 100%);
  border: none;
  border-radius: var(--cm-radius-lg);
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-semibold);
  font-family: inherit;
  color: white;
  cursor: pointer;
  transition: all var(--cm-transition-base);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  border-radius: var(--cm-radius-xl);
  overflow: hidden;
  padding: 24px;
  color: white;
}

.stat-card-bg {
  position: absolute;
  inset: 0;
  opacity: 1;
  transition: opacity var(--cm-transition-base);
}

.stat-card:hover .stat-card-bg {
  opacity: 0.9;
}

.stat-card-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--cm-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
}

.stat-icon-wrapper svg {
  width: 28px;
  height: 28px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-title {
  font-size: var(--cm-text-sm);
  opacity: 0.9;
  margin-bottom: 4px;
}

.stat-value {
  font-size: var(--cm-text-4xl);
  font-weight: var(--cm-font-bold);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--cm-radius-sm);
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
  width: fit-content;
}

.stat-trend.up {
  background: rgba(255, 255, 255, 0.25);
}

.stat-trend.down {
  background: rgba(0, 0, 0, 0.2);
}

.stat-trend svg {
  width: 14px;
  height: 14px;
}

/* 主内容网格 */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 24px;
}

.resource-card {
  grid-column: 1;
  grid-row: 1 / 3;
}

.quick-actions-card {
  grid-column: 2;
  grid-row: 1;
}

.tickets-card {
  grid-column: 2;
  grid-row: 2;
}

/* 卡片基础样式 */
.card {
  background: var(--cm-glass-bg);
  backdrop-filter: var(--cm-glass-blur);
  -webkit-backdrop-filter: var(--cm-glass-blur);
  border: 1px solid var(--cm-glass-border);
  border-radius: var(--cm-radius-xl);
  box-shadow: var(--cm-shadow-glass);
  transition: all var(--cm-transition-base);
}

.card:hover {
  box-shadow: var(--cm-shadow-glass-lg);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(124, 58, 237, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-primary);
  margin: 0;
}

.card-title svg {
  width: 22px;
  height: 22px;
  color: var(--cm-color-primary-600);
}

.card-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--cm-radius-md);
  font-size: var(--cm-text-sm);
  font-family: inherit;
  color: var(--cm-color-primary-600);
  cursor: pointer;
  transition: all var(--cm-transition-fast);
}

.card-action:hover {
  background: var(--cm-color-primary-50);
}

.card-action svg {
  width: 16px;
  height: 16px;
}

.card-body {
  padding: 24px;
}

/* 资源分布 */
.resource-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--cm-border-default);
}

.resource-item:last-child {
  border-bottom: none;
}

.resource-info {
  display: flex;
  flex-direction: column;
  width: 140px;
  flex-shrink: 0;
}

.resource-type {
  font-size: var(--cm-text-base);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-primary);
  text-transform: capitalize;
}

.resource-status {
  font-size: var(--cm-text-xs);
  color: var(--cm-text-secondary);
}

.resource-bar-wrapper {
  flex: 1;
  height: 8px;
  background: var(--cm-bg-tertiary);
  border-radius: var(--cm-radius-full);
  overflow: hidden;
}

.resource-bar {
  height: 100%;
  border-radius: var(--cm-radius-full);
  transition: width 0.8s ease-out;
}

.resource-count {
  width: 50px;
  text-align: right;
  font-size: var(--cm-text-lg);
  font-weight: var(--cm-font-bold);
  color: var(--cm-text-primary);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--cm-text-tertiary);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 快捷操作 */
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.quick-action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: var(--cm-bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--cm-radius-lg);
  cursor: pointer;
  transition: all var(--cm-transition-base);
}

.quick-action-item:hover {
  background: white;
  border-color: var(--cm-color-primary-200);
  transform: translateY(-2px);
  box-shadow: var(--cm-shadow-md);
}

.quick-action-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--cm-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--cm-transition-base);
}

.quick-action-icon svg {
  width: 28px;
  height: 28px;
}

.quick-action-item:hover .quick-action-icon {
  transform: scale(1.1);
}

.quick-action-label {
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-primary);
}

/* 工单列表 */
.ticket-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ticket-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--cm-bg-tertiary);
  border-radius: var(--cm-radius-lg);
  transition: all var(--cm-transition-fast);
}

.ticket-item:hover {
  background: white;
  box-shadow: var(--cm-shadow-sm);
}

.ticket-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ticket-title {
  font-size: var(--cm-text-sm);
  font-weight: var(--cm-font-medium);
  color: var(--cm-text-primary);
}

.ticket-time {
  font-size: var(--cm-text-xs);
  color: var(--cm-text-tertiary);
}

.ticket-status {
  padding: 4px 12px;
  border-radius: var(--cm-radius-full);
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
}

/* 动画 */
.fade-in {
  animation: fadeIn 0.6s ease forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.delay-1 { animation-delay: 0.1s; opacity: 0; }
.delay-2 { animation-delay: 0.2s; opacity: 0; }
.delay-3 { animation-delay: 0.3s; opacity: 0; }
.delay-4 { animation-delay: 0.4s; opacity: 0; }

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .main-grid {
    grid-template-columns: 1fr;
  }
  
  .resource-card {
    grid-column: 1;
    grid-row: auto;
  }
  
  .quick-actions-card,
  .tickets-card {
    grid-column: 1;
    grid-row: auto;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .quick-actions-grid {
    grid-template-columns: 1fr;
  }
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  .quick-action-item:hover {
    background: var(--cm-bg-secondary);
  }
  
  .ticket-item:hover {
    background: var(--cm-bg-secondary);
  }
}

/* 云厂商资源分布 */
.cloud-providers-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.cloud-provider-item {
  background: var(--cm-bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--cm-radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all var(--cm-transition-base);
}

.cloud-provider-item:hover {
  background: white;
  border-color: var(--cm-color-primary-200);
  transform: translateY(-2px);
  box-shadow: var(--cm-shadow-md);
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.provider-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--cm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.provider-info {
  flex: 1;
}

.provider-name {
  display: block;
  font-size: var(--cm-text-base);
  font-weight: var(--cm-font-semibold);
  color: var(--cm-text-primary);
}

.provider-count {
  display: block;
  font-size: var(--cm-text-xs);
  color: var(--cm-text-secondary);
}

.provider-status {
  padding: 4px 8px;
  background: #D1FAE5;
  color: #059669;
  border-radius: var(--cm-radius-sm);
  font-size: var(--cm-text-xs);
  font-weight: var(--cm-font-medium);
}

.provider-status.warning {
  background: #FEF3C7;
  color: #D97706;
}

.provider-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.provider-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--cm-text-xs);
  color: var(--cm-text-secondary);
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.running {
  background: #10B981;
}

.stat-dot.stopped {
  background: #F59E0B;
}

.stat-dot.error {
  background: #EF4444;
}

.provider-arrow {
  text-align: center;
  font-size: var(--cm-text-lg);
  color: var(--cm-color-primary-600);
  opacity: 0;
  transition: all var(--cm-transition-fast);
}

.cloud-provider-item:hover .provider-arrow {
  opacity: 1;
}
</style>
