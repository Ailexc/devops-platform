<script setup lang="ts">
const resources = [
  { name: 'web-server-01', id: 'i-0a1b2c3d4e5f6', spec: 'm5.xlarge (4C8G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
  { name: 'web-server-02', id: 'i-0b2c3d4e5f6g7', spec: 'm5.xlarge (4C8G)', status: 'running', region: 'us-east-1', zone: 'us-east-1b' },
  { name: 'api-server-01', id: 'i-1c3d4e5f6g7h8', spec: 'm5.2xlarge (8C16G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
  { name: 'worker-01', id: 'i-3e5f6g7h8i9j0', spec: 'm5.large (2C4G)', status: 'stopped', region: 'us-west-2', zone: 'us-west-2a' },
  { name: 'db-primary', id: 'i-5g7h8i9j0k1l2', spec: 'r5.2xlarge (8C64G)', status: 'running', region: 'us-east-1', zone: 'us-east-1a' },
]
</script>

<template>
  <div class="type-sim">
    <div class="breadcrumb">
      <span class="link">☁️ AWS</span>
      <span>/</span>
      <span>🖥️ 计算资源</span>
    </div>

    <div class="title-bar">
      <h2>🖥️ 计算资源</h2>
      <button class="back-btn">← 返回</button>
    </div>

    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">14</div><div class="stat-label">云主机 EC2</div></div>
      <div class="stat-card"><div class="stat-value">4</div><div class="stat-label">负载均衡 ELB</div></div>
      <div class="stat-card"><div class="stat-value">12</div><div class="stat-label">运行中</div></div>
      <div class="stat-card"><div class="stat-value">2</div><div class="stat-label">异常</div></div>
    </div>

    <div class="resource-table">
      <div class="table-header">
        <div class="table-title">🖥️ 云主机 (EC2) <span class="count">{{ resources.length }} 台</span></div>
        <input type="text" class="search-input" placeholder="搜索主机名/ID..." />
      </div>
      <table>
        <thead>
          <tr><th>名称</th><th>ID</th><th>规格</th><th>状态</th><th>地域</th><th>可用区</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in resources" :key="item.id">
            <td><strong>{{ item.name }}</strong></td>
            <td class="mono">{{ item.id }}</td>
            <td>{{ item.spec }}</td>
            <td>
              <span class="status-badge" :class="item.status">
                <span class="dot"></span>
                {{ item.status === 'running' ? '运行中' : '已停止' }}
              </span>
            </td>
            <td>{{ item.region }}</td>
            <td>{{ item.zone }}</td>
            <td>
              <div class="actions">
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
.type-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.breadcrumb {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 12px;
}

.link { color: #667eea; cursor: pointer; }

.title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.title-bar h2 { font-size: 18px; font-weight: 700; color: #1a1a2e; margin: 0; }

.back-btn {
  padding: 6px 12px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.stat-value { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 11px; color: #64748b; margin-top: 4px; }

.resource-table {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.table-header {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}

.count {
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 8px;
  margin-left: 6px;
}

.search-input {
  padding: 5px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 12px;
  width: 160px;
}

table { width: 100%; border-collapse: collapse; }

th {
  text-align: left;
  padding: 10px 12px;
  background: #f8fafc;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

td {
  padding: 12px;
  font-size: 12px;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
}

tr:hover { background: #f8fafc; }

.mono { font-family: monospace; font-size: 11px; color: #94a3b8; }

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.running { background: #d1fae5; color: #059669; }
.status-badge.stopped { background: #fef3c7; color: #d97706; }

.dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

.actions { display: flex; gap: 4px; }

.action-btn {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  border: none;
}

.action-btn.start { background: #d1fae5; color: #059669; }
.action-btn.stop { background: #fee2e2; color: #dc2626; }
.action-btn.detail { background: #f1f5f9; color: #475569; }
</style>
