<script setup lang="ts">
const resourceTypes = [
  {
    id: 'compute',
    title: '计算资源',
    icon: '🖥️',
    color: '#667eea',
    total: 18,
    subs: [
      { name: '云主机 EC2', count: 14 },
      { name: '负载均衡 ELB', count: 4 },
    ],
    tags: ['EC2', 'ELB', 'ECS'],
    statusText: '12 运行中 · 5 已停止 · 1 异常',
  },
  {
    id: 'network',
    title: '网络资源',
    icon: '🌐',
    color: '#10b981',
    total: 8,
    subs: [
      { name: 'VPC', count: 2 },
      { name: '子网', count: 4 },
      { name: '安全组', count: 6 },
    ],
    tags: ['VPC', 'Subnet', 'Security Group'],
    statusText: '8 个资源全部可用',
  },
  {
    id: 'storage',
    title: '存储资源',
    icon: '🗄️',
    color: '#f59e0b',
    total: 6,
    subs: [
      { name: '云硬盘 EBS', count: 4 },
      { name: '对象存储 S3', count: 2 },
    ],
    tags: ['EBS', 'S3', 'Snapshot'],
    statusText: '6 个资源全部可用',
  },
  {
    id: 'database',
    title: '数据库',
    icon: '📦',
    color: '#8b5cf6',
    total: 5,
    subs: [
      { name: 'RDS 实例', count: 3 },
      { name: 'ElastiCache', count: 2 },
    ],
    tags: ['RDS', 'ElastiCache'],
    statusText: '5 个资源全部可用',
  },
]
</script>

<template>
  <div class="provider-sim">
    <div class="filter-header">
      <div class="cloud-title">
        <span class="cloud-icon">☁️</span>
        <h2>AWS</h2>
        <span class="sync-status">✅ 最近同步: 2 分钟前</span>
      </div>
      <div class="filter-row">
        <select class="filter-select"><option>全部账号</option></select>
        <select class="filter-select"><option>全部地域</option></select>
        <select class="filter-select"><option>全部状态</option></select>
      </div>
    </div>

    <div class="content">
      <div class="resource-types">
        <div v-for="item in resourceTypes" :key="item.id" class="resource-type-card">
          <div class="type-header">
            <div class="type-icon" :style="{ background: `${item.color}15`, color: item.color }">{{ item.icon }}</div>
            <div>
              <div class="type-title">{{ item.title }}</div>
              <div class="type-count">{{ item.total }} <span>个资源</span></div>
            </div>
          </div>
          <div class="type-details">
            <div v-for="sub in item.subs" :key="sub.name" class="type-detail-item">
              <div class="type-detail-value">{{ sub.count }}</div>
              <div class="type-detail-label">{{ sub.name }}</div>
            </div>
          </div>
          <div class="type-examples">
            <span v-for="tag in item.tags" :key="tag" class="example-tag">{{ tag }}</span>
          </div>
          <div class="type-status">
            <span class="status-dot"></span>
            <span class="status-text">{{ item.statusText }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.provider-sim {
  height: 100%;
  background: #f8fafc;
  overflow-y: auto;
}

.filter-header {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.cloud-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.cloud-icon { font-size: 24px; }
.cloud-title h2 { font-size: 18px; font-weight: 700; color: #1a1a2e; margin: 0; }
.sync-status { font-size: 11px; color: #10b981; }

.filter-row {
  display: flex;
  gap: 12px;
}

.filter-select {
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 12px;
  background: #f8fafc;
  min-width: 120px;
}

.content {
  padding: 20px;
}

.resource-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.resource-type-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.resource-type-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.type-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.type-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.type-title { font-size: 15px; font-weight: 700; color: #1a1a2e; }
.type-count { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.type-count span { font-size: 12px; font-weight: 400; color: #64748b; }

.type-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.type-detail-item { text-align: center; }
.type-detail-value { font-size: 16px; font-weight: 700; color: #1a1a2e; }
.type-detail-label { font-size: 10px; color: #64748b; }

.type-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.example-tag {
  padding: 3px 8px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 10px;
  color: #475569;
}

.type-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

.status-text { font-size: 10px; color: #64748b; }
</style>
