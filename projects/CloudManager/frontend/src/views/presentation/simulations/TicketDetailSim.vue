<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<template>
  <div class="detail-sim">
    <div class="detail-header">
      <div class="breadcrumb">工单中心 / #1001</div>
      <h2>📋 申请云主机 web-server-02</h2>
      <div class="status-bar">
        <span class="status pending">待审批</span>
        <span class="type-badge">创建工单</span>
      </div>
    </div>

    <div class="detail-grid">
      <div class="info-card">
        <h3>基础信息</h3>
        <div class="info-list">
          <div class="info-item"><span class="label">工单号</span><span class="value">#1001</span></div>
          <div class="info-item"><span class="label">申请人</span><span class="value">张三 (运维工程师)</span></div>
          <div class="info-item"><span class="label">申请时间</span><span class="value">2026-08-08 10:30:00</span></div>
          <div class="info-item"><span class="label">工单类型</span><span class="value">创建资源</span></div>
        </div>
      </div>

      <div class="info-card">
        <h3>申请内容</h3>
        <div class="info-list">
          <div class="info-item"><span class="label">资源类型</span><span class="value">云主机</span></div>
          <div class="info-item"><span class="label">规格</span><span class="value">4C8G</span></div>
          <div class="info-item"><span class="label">云厂商</span><span class="value">AWS</span></div>
          <div class="info-item"><span class="label">地域</span><span class="value">us-east-1</span></div>
        </div>
      </div>

      <div class="info-card" :class="{ highlighted: focus === 'approval' }">
        <h3>📝 审批记录</h3>
        <div class="approval-list">
          <div class="approval-item">
            <div class="approver">
              <span class="avatar">李</span>
              <div class="approver-info">
                <span class="name">李四</span>
                <span class="role">云管理员</span>
              </div>
            </div>
            <div class="approval-status pending">待审批</div>
          </div>
          <div class="approval-item">
            <div class="approver">
              <span class="avatar">王</span>
              <div class="approver-info">
                <span class="name">王五</span>
                <span class="role">部门经理</span>
              </div>
            </div>
            <div class="approval-status waiting">等待中</div>
          </div>
        </div>
      </div>

      <div class="info-card" :class="{ highlighted: focus === 'execution' }">
        <h3>⚙️ 执行结果</h3>
        <div class="execution-list">
          <div class="exec-item">
            <span class="exec-icon">⏳</span>
            <span class="exec-text">等待审批通过后自动执行</span>
          </div>
          <div class="exec-item">
            <span class="exec-icon">📋</span>
            <span class="exec-text">Mock Provider 将自动创建主机</span>
          </div>
          <div class="exec-item">
            <span class="exec-icon">🔄</span>
            <span class="exec-text">执行完成后自动回写 CMDB</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.detail-header {
  margin-bottom: 20px;
}

.breadcrumb {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.status-bar {
  display: flex;
  gap: 8px;
}

.status {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status.pending { background: #fef3c7; color: #d97706; }

.type-badge {
  padding: 3px 10px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.info-card.highlighted {
  border: 2px solid #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 12px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}

.info-item:last-child { border-bottom: none; }
.label { color: #64748b; }
.value { color: #1e293b; font-weight: 500; }

.approval-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}

.approval-item:last-child { border-bottom: none; }

.approver {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  background: #667eea;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.name { font-size: 13px; font-weight: 500; color: #1e293b; display: block; }
.role { font-size: 11px; color: #94a3b8; display: block; }

.approval-status {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.approval-status.pending { background: #fef3c7; color: #d97706; }
.approval-status.waiting { background: #f1f5f9; color: #94a3b8; }

.exec-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  color: #475569;
}

.exec-item:last-child { border-bottom: none; }
.exec-icon { font-size: 16px; }
</style>
