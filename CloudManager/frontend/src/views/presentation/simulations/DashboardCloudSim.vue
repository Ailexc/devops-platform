<script setup lang="ts">
const cloudProviders = [
  { id: 'aws', name: 'AWS', icon: '☁️', color: '#f97316', count: 32, running: 25, stopped: 5, error: 2, status: '正常' },
  { id: 'aliyun', name: '阿里云', icon: '🌐', color: '#3b82f6', count: 28, running: 22, stopped: 4, error: 2, status: '正常' },
  { id: 'tencent', name: '腾讯云', icon: '🟣', color: '#8b5cf6', count: 19, running: 18, stopped: 1, error: 0, status: '部分异常' },
]

const summaryStats = [
  { title: '资源总数', value: '79', trend: '+3', up: true, gradient: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)' },
  { title: '运行中', value: '65', trend: '+2', up: true, gradient: 'linear-gradient(135deg, #11998E 0%, #38EF7D 100%)' },
  { title: '月度费用', value: '¥35.2K', trend: '-8%', up: false, gradient: 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)' },
  { title: '工单待办', value: '5', trend: '+2', up: true, gradient: 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)' },
]

const recentTickets = [
  { title: '申请云主机 web-server-02', status: 'pending', time: '10分钟前' },
  { title: '释放测试环境资源', status: 'executing', time: '1小时前' },
  { title: '变更生产环境配置', status: 'success', time: '2小时前' },
]

const statusColors: Record<string, string> = {
  pending: '#FEF3C7',
  executing: '#DBEAFE',
  success: '#D1FAE5',
}

const statusLabels: Record<string, string> = {
  pending: '待审批',
  executing: '执行中',
  success: '已完成',
}
</script>

<template>
  <div class="dashboard-sim">
    <!-- 统计卡片 -->
    <div class="summary-cards">
      <div v-for="stat in summaryStats" :key="stat.title" class="summary-card" :style="{ background: stat.gradient }">
        <div class="stat-content">
          <span class="stat-title">{{ stat.title }}</span>
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-trend" :class="stat.up ? 'up' : 'down'">{{ stat.up ? '↑' : '↓' }} {{ stat.trend }}</span>
        </div>
      </div>
    </div>

    <!-- 多云资源分布 -->
    <div class="cloud-section">
      <div class="section-header">
        <h3>☁️ 多云资源分布</h3>
        <span class="view-all">查看全部 →</span>
      </div>
      <div class="cloud-grid">
        <div v-for="provider in cloudProviders" :key="provider.id" class="cloud-card">
          <div class="cloud-header">
            <span class="cloud-icon" :style="{ background: `${provider.color}15` }">{{ provider.icon }}</span>
            <div class="cloud-info">
              <span class="cloud-name">{{ provider.name }}</span>
              <span class="cloud-count">{{ provider.count }} 个资源</span>
            </div>
            <span class="cloud-status" :class="{ warning: provider.status === '部分异常' }">{{ provider.status }}</span>
          </div>
          <div class="cloud-stats">
            <span class="cs-item"><span class="dot running"></span> {{ provider.running }} 运行中</span>
            <span class="cs-item"><span class="dot stopped"></span> {{ provider.stopped }} 已停止</span>
            <span v-if="provider.error > 0" class="cs-item"><span class="dot error"></span> {{ provider.error }} 异常</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近工单 -->
    <div class="tickets-section">
      <div class="section-header">
        <h3>📋 最近工单</h3>
      </div>
      <div class="ticket-list">
        <div v-for="ticket in recentTickets" :key="ticket.title" class="ticket-item">
          <span class="ticket-title">{{ ticket.title }}</span>
          <span class="ticket-status" :style="{ background: statusColors[ticket.status] }">{{ statusLabels[ticket.status] }}</span>
          <span class="ticket-time">{{ ticket.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-sim {
  padding: 16px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  border-radius: 12px;
  padding: 16px;
  color: #fff;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-title {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 11px;
  opacity: 0.8;
}

.cloud-section, .tickets-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.view-all {
  font-size: 12px;
  color: #667eea;
  cursor: pointer;
}

.cloud-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.cloud-card {
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cloud-card:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

.cloud-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.cloud-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.cloud-info {
  flex: 1;
}

.cloud-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.cloud-count {
  display: block;
  font-size: 11px;
  color: #64748b;
}

.cloud-status {
  padding: 2px 6px;
  background: #D1FAE5;
  color: #059669;
  border-radius: 4px;
  font-size: 10px;
}

.cloud-status.warning {
  background: #FEF3C7;
  color: #D97706;
}

.cloud-stats {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #64748b;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.dot.running { background: #10B981; }
.dot.stopped { background: #F59E0B; }
.dot.error { background: #EF4444; }

.ticket-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ticket-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  gap: 12px;
}

.ticket-title {
  flex: 1;
  font-size: 12px;
  color: #1a1a2e;
}

.ticket-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.ticket-time {
  font-size: 11px;
  color: #94a3b8;
}
</style>
