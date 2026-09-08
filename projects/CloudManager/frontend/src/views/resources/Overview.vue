<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const cloudProviders = [
  { id: 'aws', name: 'AWS', icon: '☁️', color: '#f97316', count: 32, status: '正常' },
  { id: 'aliyun', name: '阿里云', icon: '🌐', color: '#3b82f6', count: 28, status: '正常' },
  { id: 'tencent', name: '腾讯云', icon: '🟣', color: '#8b5cf6', count: 19, status: '部分异常' },
]

function goToProvider(id: string) {
  router.push(`/resources/${id}`)
}
</script>

<template>
  <div class="overview-page">
    <div class="page-header">
      <h1>📊 资源概览</h1>
      <p>多云资源统一视图</p>
    </div>

    <!-- 总览统计 -->
    <div class="total-stats">
      <div class="total-stat">
        <div class="stat-value">79</div>
        <div class="stat-label">资源总数</div>
      </div>
      <div class="total-stat">
        <div class="stat-value">65</div>
        <div class="stat-label">运行中</div>
      </div>
      <div class="total-stat">
        <div class="stat-value">¥35,200</div>
        <div class="stat-label">月度费用</div>
      </div>
      <div class="total-stat">
        <div class="stat-value">99.8%</div>
        <div class="stat-label">整体可用性</div>
      </div>
    </div>

    <!-- 云厂商卡片 -->
    <div class="provider-grid">
      <div 
        v-for="provider in cloudProviders" 
        :key="provider.id"
        class="provider-card"
        @click="goToProvider(provider.id)"
      >
        <div class="provider-header">
          <div class="provider-icon" :style="{ background: `${provider.color}15`, color: provider.color }">
            {{ provider.icon }}
          </div>
          <div class="provider-info">
            <div class="provider-name">{{ provider.name }}</div>
            <div class="provider-count">{{ provider.count }} 个资源</div>
          </div>
          <div class="provider-status" :class="{ warning: provider.status === '部分异常' }">
            {{ provider.status }}
          </div>
        </div>
        <div class="provider-stats">
          <div class="provider-stat">
            <span class="stat-icon">🖥️</span>
            <span>18</span>
          </div>
          <div class="provider-stat">
            <span class="stat-icon">🌐</span>
            <span>8</span>
          </div>
          <div class="provider-stat">
            <span class="stat-icon">🗄️</span>
            <span>6</span>
          </div>
          <div class="provider-stat">
            <span class="stat-icon">📦</span>
            <span>5</span>
          </div>
        </div>
        <div class="provider-arrow">→</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.page-header p {
  font-size: 14px;
  color: #64748b;
}

.total-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.total-stat {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.provider-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.provider-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border-color: #667eea;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.provider-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.provider-info {
  flex: 1;
}

.provider-name {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.provider-count {
  font-size: 14px;
  color: #64748b;
}

.provider-status {
  padding: 4px 10px;
  background: #d1fae5;
  color: #059669;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.provider-status.warning {
  background: #fef3c7;
  color: #d97706;
}

.provider-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 16px 0;
  border-top: 1px solid #f1f5f9;
}

.provider-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.stat-icon {
  font-size: 18px;
}

.provider-arrow {
  text-align: center;
  font-size: 20px;
  color: #667eea;
  margin-top: 12px;
}
</style>
