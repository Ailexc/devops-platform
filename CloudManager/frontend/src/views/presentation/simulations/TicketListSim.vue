<script setup lang="ts">
defineProps<{ focus?: string }>()

const tickets = [
  { id: 1001, title: '申请云主机 web-server-02', type: '创建', status: 'pending', applicant: '张三', time: '10分钟前' },
  { id: 1000, title: '释放测试环境资源', type: '下线', status: 'executing', applicant: '李四', time: '1小时前' },
  { id: 999, title: '变更生产环境配置', type: '变更', status: 'success', applicant: '王五', time: '2小时前' },
  { id: 998, title: '停止开发环境主机', type: '停止', status: 'failed', applicant: '赵六', time: '3小时前' },
  { id: 997, title: '创建数据库从库', type: '创建', status: 'success', applicant: '张三', time: '昨天' },
]

const statusMap: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: '待审批', color: '#d97706', bg: '#fef3c7' },
  executing: { label: '执行中', color: '#2563eb', bg: '#dbeafe' },
  success: { label: '已完成', color: '#059669', bg: '#d1fae5' },
  failed: { label: '已失败', color: '#dc2626', bg: '#fee2e2' },
}
</script>

<template>
  <div class="ticket-sim">
    <div class="list-header">
      <h2>📋 工单中心</h2>
      <div class="header-stats">
        <span class="stat">待审批: <strong>5</strong></span>
        <span class="stat">执行中: <strong>2</strong></span>
        <span class="stat">已完成: <strong>128</strong></span>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-tabs" :class="{ highlighted: focus === 'status' }">
        <span class="tab active">全部</span>
        <span class="tab">待审批</span>
        <span class="tab">执行中</span>
        <span class="tab">已完成</span>
        <span class="tab">已失败</span>
      </div>
      <div class="filter-right">
        <div class="type-filter" :class="{ highlighted: focus === 'type' }">
          <span>工单类型</span>
          <span class="arrow">▼</span>
        </div>
      </div>
    </div>

    <div class="ticket-table">
      <div class="table-header">
        <div class="col id">工单号</div>
        <div class="col title">工单标题</div>
        <div class="col type">类型</div>
        <div class="col status">状态</div>
        <div class="col applicant">申请人</div>
        <div class="col time">创建时间</div>
      </div>
      <div v-for="item in tickets" :key="item.id" class="table-row" :class="{ 'new-row': focus === 'new' && item.id === 1001 }">
        <div class="col id">#{{ item.id }}</div>
        <div class="col title">{{ item.title }}</div>
        <div class="col type">{{ item.type }}</div>
        <div class="col status">
          <span class="status-badge" :style="{ background: statusMap[item.status]?.bg, color: statusMap[item.status]?.color }">
            {{ statusMap[item.status]?.label }}
          </span>
        </div>
        <div class="col applicant">{{ item.applicant }}</div>
        <div class="col time">{{ item.time }}</div>
      </div>
    </div>

    <div v-if="focus === 'closed'" class="closed-hint">
      <span class="hint-icon">✅</span>
      <span>工单执行完成后自动回写 CMDB，数据保持一致</span>
    </div>
  </div>
</template>

<style scoped>
.ticket-sim {
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

.header-stats {
  display: flex;
  gap: 16px;
}

.stat {
  font-size: 13px;
  color: #64748b;
}

.stat strong {
  color: #1a1a2e;
  font-weight: 600;
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

.type-filter {
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

.type-filter.highlighted {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.arrow { font-size: 10px; color: #94a3b8; }

.ticket-table {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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
  transition: all 0.3s;
}

.table-row:hover { background: #f8fafc; }

.table-row.new-row {
  background: #f0fdf4;
  border-left: 3px solid #10b981;
}

.col { flex: 1; }
.col.id { flex: 0.8; color: #94a3b8; }
.col.title { flex: 2; font-weight: 500; }

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.closed-hint {
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

.hint-icon { font-size: 16px; }
</style>
