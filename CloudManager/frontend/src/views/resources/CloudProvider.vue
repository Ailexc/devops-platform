<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const provider = computed(() => route.params.provider as string)

const providerInfo: Record<string, { name: string; icon: string; color: string }> = {
  aws: { name: 'AWS', icon: '☁️', color: '#f97316' },
  aliyun: { name: '阿里云', icon: '🌐', color: '#3b82f6' },
  tencent: { name: '腾讯云', icon: '🟣', color: '#8b5cf6' },
}

const currentProvider = computed(() => providerInfo[provider.value] ?? providerInfo.aws)

// 筛选
const selectedAccount = ref('all')
const selectedRegion = ref('all')
const selectedStatus = ref('all')

const accounts = [
  { id: 'all', name: '全部账号' },
  { id: 'prod', name: '生产环境 (AK****8f)' },
  { id: 'dev', name: '测试环境 (AK****2a)' },
]

const regions = [
  { id: 'all', name: '全部地域' },
  { id: 'us-east-1', name: 'us-east-1 (弗吉尼亚)' },
  { id: 'us-west-2', name: 'us-west-2 (俄勒冈)' },
  { id: 'ap-southeast-1', name: 'ap-southeast-1 (新加坡)' },
]

// 资源类型
const resourceTypes = ref([
  {
    id: 'compute',
    title: '计算资源',
    icon: '🖥️',
    color: '#667eea',
    total: 18,
    subs: [
      { name: '云主机 EC2', count: 14 },
      { name: '负载均衡 ELB', count: 4 },
      { name: '容器 ECS', count: 0 },
    ],
    tags: ['EC2', 'ELB', 'ECS', 'Lambda'],
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
      { name: '子网 Subnet', count: 4 },
      { name: '安全组 SG', count: 6 },
    ],
    tags: ['VPC', 'Subnet', 'Security Group', 'Route Table'],
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
      { name: '快照 Snapshot', count: 3 },
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
      { name: '参数组', count: 1 },
    ],
    tags: ['RDS', 'ElastiCache', 'Parameter Group'],
    statusText: '5 个资源全部可用',
  },
])

// 概览统计
const overviewStats = [
  { value: '32', label: '资源总数', change: '↑ 3 较上月', up: true },
  { value: '25', label: '运行中', change: '↑ 2 较上月', up: true },
  { value: '¥12,500', label: '月度费用', change: '↓ 8% 较上月', up: false },
  { value: '99.9%', label: '可用性', change: '↑ 0.1% 较上月', up: true },
]

// 跳转到资源类型详情
function goToResourceType(type: string) {
  router.push(`/resources/${provider.value}/${type}`)
}
</script>

<template>
  <div class="cloud-provider-page">
    <!-- 顶部筛选栏 -->
    <div class="filter-header">
      <div class="cloud-header">
        <div class="cloud-title">
          <span class="cloud-icon">{{ currentProvider?.icon }}</span>
          <h1>{{ currentProvider?.name }}</h1>
          <span class="sync-status">✅ 最近同步: 2 分钟前</span>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary">🔄 同步资源</button>
          <button class="btn btn-primary">+ 申请资源</button>
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">云账号</span>
          <select v-model="selectedAccount" class="filter-select">
            <option v-for="acc in accounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
          </select>
        </div>
        <div class="filter-group">
          <span class="filter-label">地域</span>
          <select v-model="selectedRegion" class="filter-select">
            <option v-for="r in regions" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>
        <div class="filter-group">
          <span class="filter-label">状态</span>
          <select v-model="selectedStatus" class="filter-select">
            <option value="all">全部状态</option>
            <option value="running">运行中</option>
            <option value="stopped">已停止</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="content">
      <!-- 资源类型卡片 -->
      <div class="resource-types">
        <div
          v-for="item in resourceTypes"
          :key="item.id"
          class="resource-type-card"
          @click="goToResourceType(item.id)"
        >
          <div class="type-header">
            <div class="type-icon" :style="{ background: `${item.color}15`, color: item.color }">
              {{ item.icon }}
            </div>
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
            <span class="status-indicator healthy"></span>
            <span class="status-text">{{ item.statusText }}</span>
          </div>
        </div>
      </div>

      <!-- 概览统计 -->
      <div class="overview-section">
        <div class="overview-title">📊 资源概览</div>
        <div class="overview-grid">
          <div v-for="stat in overviewStats" :key="stat.label" class="overview-item">
            <div class="overview-value">{{ stat.value }}</div>
            <div class="overview-label">{{ stat.label }}</div>
            <div class="overview-change" :class="stat.up ? 'up' : 'down'">{{ stat.change }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cloud-provider-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.filter-header {
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.cloud-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cloud-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cloud-icon {
  font-size: 28px;
}

.cloud-title h1 {
  font-size: 20px;
  font-weight: 700;
}

.sync-status {
  font-size: 12px;
  color: #10b981;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-top: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: #64748b;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #f8fafc;
  min-width: 140px;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.resource-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.resource-type-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.resource-type-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border-color: #667eea;
}

.type-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.type-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.type-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

.type-count {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
}

.type-count span {
  font-size: 14px;
  font-weight: 400;
  color: #64748b;
  margin-left: 4px;
}

.type-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.type-detail-item {
  text-align: center;
}

.type-detail-value {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.type-detail-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.type-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.example-tag {
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
}

.type-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.healthy {
  background: #10b981;
}

.status-text {
  font-size: 12px;
  color: #64748b;
}

.overview-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.overview-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 16px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.overview-item {
  text-align: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.overview-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.overview-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.overview-change {
  font-size: 11px;
  margin-top: 4px;
}

.overview-change.up {
  color: #10b981;
}

.overview-change.down {
  color: #ef4444;
}
</style>
