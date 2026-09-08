<script setup lang="ts">
defineProps<{
  focus?: string
}>()

const stats = [
  { label: '云主机总数', value: 79, icon: '🖥️', color: '#667eea' },
  { label: '运行中', value: 52, icon: '✅', color: '#10b981' },
  { label: '已停止', value: 18, icon: '⏸️', color: '#f59e0b' },
  { label: '工单待办', value: 5, icon: '📋', color: '#ef4444' },
]

const resources = [
  { name: 'AWS', count: 32, percent: 41, color: '#f97316' },
  { name: '阿里云', count: 28, percent: 35, color: '#3b82f6' },
  { name: '腾讯云', count: 19, percent: 24, color: '#8b5cf6' },
]
</script>

<template>
  <div class="dashboard-sim">
    <div class="dash-header">
      <h2>工作台</h2>
      <div class="header-actions">
        <span class="search-box">🔍 搜索资源...</span>
        <span class="action-btn">+ 申请资源</span>
      </div>
    </div>

    <div class="stats-grid" :class="{ 'focus-resource': focus === 'resource' }">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-icon" :style="{ background: `${stat.color}15`, color: stat.color }">
          {{ stat.icon }}
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <div class="chart-card" :class="{ highlighted: focus === 'resource' }">
        <h3>资源分布</h3>
        <div class="chart-area">
          <div v-for="item in resources" :key="item.name" class="bar-item">
            <div class="bar-label">{{ item.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${item.percent}%`, background: item.color }"></div>
            </div>
            <div class="bar-value">{{ item.count }}台 ({{ item.percent }}%)</div>
          </div>
        </div>
      </div>

      <div class="recent-card">
        <h3>最近工单</h3>
        <div class="ticket-list">
          <div class="ticket-item">
            <span class="ticket-status pending">待审批</span>
            <span class="ticket-title">申请云主机 web-server-02</span>
            <span class="ticket-time">10分钟前</span>
          </div>
          <div class="ticket-item">
            <span class="ticket-status executing">执行中</span>
            <span class="ticket-title">释放测试环境资源</span>
            <span class="ticket-time">1小时前</span>
          </div>
          <div class="ticket-item">
            <span class="ticket-status success">已完成</span>
            <span class="ticket-title">变更生产环境配置</span>
            <span class="ticket-time">2小时前</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dash-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-box {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #94a3b8;
}

.action-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
  transition: all 0.3s;
}

.stats-grid.focus-resource {
  transform: scale(1.02);
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.content-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.chart-card, .recent-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.chart-card.highlighted {
  border: 2px solid #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 16px 0;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.bar-label {
  width: 60px;
  font-size: 13px;
  color: #475569;
}

.bar-track {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-value {
  width: 100px;
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

.ticket-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}

.ticket-item:last-child {
  border-bottom: none;
}

.ticket-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.ticket-status.pending { background: #fef3c7; color: #d97706; }
.ticket-status.executing { background: #dbeafe; color: #2563eb; }
.ticket-status.success { background: #d1fae5; color: #059669; }

.ticket-title {
  flex: 1;
  font-size: 13px;
  color: #1e293b;
}

.ticket-time {
  font-size: 12px;
  color: #94a3b8;
}
</style>
