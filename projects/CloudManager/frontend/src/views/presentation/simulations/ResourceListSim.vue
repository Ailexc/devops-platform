<script setup lang="ts">
defineProps<{ focus?: string }>()

const resources = [
  { id: 1, name: 'web-server-01', type: '云主机', cloud: 'AWS', region: 'us-east-1', status: 'running', spec: '4C8G' },
  { id: 2, name: 'db-master-01', type: '云主机', cloud: '阿里云', region: 'cn-hangzhou', status: 'running', spec: '8C16G' },
  { id: 3, name: 'cache-redis-01', type: '缓存', cloud: 'AWS', region: 'us-east-1', status: 'running', spec: '2C4G' },
  { id: 4, name: 'web-server-02', type: '云主机', cloud: '腾讯云', region: 'ap-guangzhou', status: 'stopped', spec: '4C8G' },
  { id: 5, name: 'api-gateway-01', type: '云主机', cloud: '阿里云', region: 'cn-shanghai', status: 'running', spec: '2C4G' },
]

const statusMap: Record<string, { label: string; color: string; bg: string }> = {
  running: { label: '运行中', color: '#059669', bg: '#d1fae5' },
  stopped: { label: '已停止', color: '#d97706', bg: '#fef3c7' },
}
</script>

<template>
  <div class="resource-sim">
    <div class="list-header">
      <h2>云主机管理</h2>
      <div class="header-actions">
        <span class="btn-apply">+ 申请主机</span>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-tabs" :class="{ highlighted: focus === 'tabs' }">
        <span class="tab active">全部 (79)</span>
        <span class="tab">主机 (52)</span>
        <span class="tab">网络 (12)</span>
        <span class="tab">数据库 (8)</span>
        <span class="tab">缓存 (7)</span>
      </div>
      <div class="filter-right">
        <div class="cloud-filter" :class="{ highlighted: focus === 'cloudFilter' }">
          <span class="filter-icon">☁️</span>
          <span>全部云厂商</span>
          <span class="arrow">▼</span>
        </div>
        <div class="search-box" :class="{ highlighted: focus === 'search' }">
          <span class="search-icon">🔍</span>
          <span class="search-placeholder">搜索名称/ID...</span>
        </div>
      </div>
    </div>

    <div class="resource-table" :class="{ highlighted: focus === 'table' }">
      <div class="table-header">
        <div class="col name">资源名称</div>
        <div class="col type">类型</div>
        <div class="col cloud">云厂商</div>
        <div class="col region">地域</div>
        <div class="col status">状态</div>
        <div class="col spec">规格</div>
        <div class="col action">操作</div>
      </div>
      <div v-for="item in resources" :key="item.id" class="table-row">
        <div class="col name">{{ item.name }}</div>
        <div class="col type">{{ item.type }}</div>
        <div class="col cloud">{{ item.cloud }}</div>
        <div class="col region">{{ item.region }}</div>
        <div class="col status">
          <span class="status-badge" :style="{ background: statusMap[item.status]?.bg, color: statusMap[item.status]?.color }">
            {{ statusMap[item.status]?.label }}
          </span>
        </div>
        <div class="col spec">{{ item.spec }}</div>
        <div class="col action" :class="{ highlighted: focus === 'actions' }">
          <span class="action-btn">启动</span>
          <span class="action-btn">停止</span>
          <span class="action-btn">详情</span>
        </div>
      </div>
    </div>

    <div v-if="focus === 'new'" class="new-indicator">
      <span class="new-badge">NEW</span>
      <span>新创建的主机已自动出现在列表中</span>
    </div>
  </div>
</template>

<style scoped>
.resource-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.btn-apply {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.filter-tabs {
  display: flex;
  gap: 4px;
  transition: all 0.3s;
}

.filter-tabs.highlighted {
  outline: 2px solid #667eea;
  outline-offset: 4px;
  border-radius: 8px;
}

.tab {
  padding: 6px 12px;
  font-size: 13px;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
}

.tab.active {
  background: #667eea;
  color: #fff;
}

.filter-right {
  display: flex;
  gap: 12px;
}

.cloud-filter, .search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  color: #475569;
  transition: all 0.3s;
}

.cloud-filter.highlighted, .search-box.highlighted {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.arrow { font-size: 10px; color: #94a3b8; }
.search-placeholder { color: #94a3b8; }

.resource-table {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.resource-table.highlighted {
  border: 2px solid #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.table-header {
  display: flex;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
}

.table-row {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  color: #1e293b;
  transition: background 0.2s;
}

.table-row:hover {
  background: #f8fafc;
}

.col { flex: 1; }
.col.name { flex: 1.5; font-weight: 500; }
.col.action { flex: 1.5; display: flex; gap: 6px; }
.col.action.highlighted { outline: 2px solid #667eea; outline-offset: 2px; border-radius: 4px; }

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.action-btn {
  padding: 3px 8px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
}

.action-btn:hover {
  background: #e2e8f0;
}

.new-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  font-size: 13px;
  color: #166534;
}

.new-badge {
  padding: 2px 6px;
  background: #10b981;
  color: #fff;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
</style>
