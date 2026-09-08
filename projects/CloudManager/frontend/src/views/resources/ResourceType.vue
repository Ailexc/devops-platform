<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const provider = computed(() => route.params.provider as string)
const resourceType = computed(() => route.params.type as string)

const providerInfo: Record<string, { name: string; icon: string }> = {
  aws: { name: 'AWS', icon: '☁️' },
  aliyun: { name: '阿里云', icon: '🌐' },
  tencent: { name: '腾讯云', icon: '🟣' },
}

const typeInfo: Record<string, { name: string; icon: string }> = {
  compute: { name: '计算资源', icon: '🖥️' },
  network: { name: '网络资源', icon: '🌐' },
  storage: { name: '存储资源', icon: '🗄️' },
  database: { name: '数据库', icon: '📦' },
}

const currentProvider = computed(() => providerInfo[provider.value] ?? providerInfo.aws)
const currentType = computed(() => typeInfo[resourceType.value] ?? typeInfo.compute)

// 模拟资源数据
const resources = ref([
  { id: 1, name: 'web-server-01', cloudId: 'i-0a1b2c3d4e5f6', spec: 'm5.xlarge (4C8G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
  { id: 2, name: 'web-server-02', cloudId: 'i-0b2c3d4e5f6g7', spec: 'm5.xlarge (4C8G)', status: 'running', region: 'us-east-1', zone: 'us-east-1b' },
  { id: 3, name: 'api-server-01', cloudId: 'i-1c3d4e5f6g7h8', spec: 'm5.2xlarge (8C16G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
  { id: 4, name: 'api-server-02', cloudId: 'i-2d4e5f6g7h8i9', spec: 'm5.2xlarge (8C16G)', status: 'running', region: 'us-east-1', zone: 'us-east-1b' },
  { id: 5, name: 'worker-01', cloudId: 'i-3e5f6g7h8i9j0', spec: 'm5.large (2C4G)', status: 'stopped', region: 'us-west-2', zone: 'us-west-2a' },
  { id: 6, name: 'db-primary', cloudId: 'i-5g7h8i9j0k1l2', spec: 'r5.2xlarge (8C64G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
])

const searchQuery = ref('')

const filteredResources = computed(() => {
  if (!searchQuery.value) return resources.value
  return resources.value.filter(r => 
    r.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    r.cloudId.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

function goBack() {
  router.push(`/resources/${provider.value}`)
}
</script>

<template>
  <div class="resource-type-page">
    <!-- 面包屑 -->
    <div class="breadcrumb">
      <span class="breadcrumb-link" @click="goBack">{{ currentProvider?.icon }} {{ currentProvider?.name }}</span>
      <span class="breadcrumb-separator">/</span>
      <span>{{ currentType?.icon }} {{ currentType?.name }}</span>
    </div>

    <!-- 标题栏 -->
    <div class="title-bar">
      <h2>{{ currentType?.icon }} {{ currentType?.name }}</h2>
      <button class="btn btn-secondary" @click="goBack">← 返回</button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">14</div>
        <div class="stat-label">云主机 EC2</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">4</div>
        <div class="stat-label">负载均衡 ELB</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">12</div>
        <div class="stat-label">运行中</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">2</div>
        <div class="stat-label">异常</div>
      </div>
    </div>

    <!-- 资源表格 -->
    <div class="resource-table">
      <div class="table-header">
        <div class="table-title">
          🖥️ 云主机 (EC2)
          <span class="table-count">{{ filteredResources.length }} 台</span>
        </div>
        <input 
          v-model="searchQuery"
          type="text" 
          class="search-input" 
          placeholder="搜索主机名/ID..." 
        />
      </div>
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>ID</th>
            <th>规格</th>
            <th>状态</th>
            <th>地域</th>
            <th>可用区</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredResources" :key="item.id">
            <td>
              <div class="resource-name">{{ item.name }}</div>
            </td>
            <td class="resource-id">{{ item.cloudId }}</td>
            <td>{{ item.spec }}</td>
            <td>
              <span class="status-badge" :class="item.status">
                <span class="status-dot"></span>
                {{ item.status === 'running' ? '运行中' : '已停止' }}
              </span>
            </td>
            <td>{{ item.region }}</td>
            <td>{{ item.zone }}</td>
            <td>
              <div class="action-btns">
                <button v-if="item.status === 'stopped'" class="action-btn start">启动</button>
                <button v-if="item.status === 'running'" class="action-btn stop">停止</button>
                <button class="action-btn detail">详情</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.resource-type-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.breadcrumb {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 16px;
}

.breadcrumb-link {
  color: #667eea;
  cursor: pointer;
}

.breadcrumb-link:hover {
  text-decoration: underline;
}

.breadcrumb-separator {
  margin: 0 8px;
}

.title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-bar h2 {
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.resource-table {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.table-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-count {
  font-size: 13px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 10px;
}

.search-input {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 12px 16px;
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

td {
  padding: 14px 16px;
  font-size: 13px;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
}

tr:hover {
  background: #f8fafc;
}

.resource-name {
  font-weight: 600;
  color: #1a1a2e;
}

.resource-id {
  font-size: 12px;
  color: #94a3b8;
  font-family: monospace;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: #d1fae5;
  color: #059669;
}

.status-badge.stopped {
  background: #fef3c7;
  color: #d97706;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.action-btns {
  display: flex;
  gap: 6px;
}

.action-btn {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}

.action-btn.start {
  background: #d1fae5;
  color: #059669;
}

.action-btn.stop {
  background: #fee2e2;
  color: #dc2626;
}

.action-btn.detail {
  background: #f1f5f9;
  color: #475569;
}
</style>
