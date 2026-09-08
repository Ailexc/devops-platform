<script setup lang="ts">
</script>

<template>
  <div class="approval-sim">
    <div class="list-header">
      <h2>✅ 审批中心</h2>
      <div class="header-stats">
        <span class="stat">待审批: <strong>5</strong></span>
        <span class="stat">今日已处理: <strong>12</strong></span>
      </div>
    </div>

    <div class="approval-list">
      <div class="approval-card">
        <div class="approval-header">
          <div class="applicant">
            <span class="avatar">张</span>
            <div class="applicant-info">
              <span class="name">张三</span>
              <span class="role">运维工程师</span>
            </div>
          </div>
          <span class="time">10分钟前</span>
        </div>
        <div class="approval-content">
          <div class="content-title">📋 申请云主机 web-server-02</div>
          <div class="content-detail">
            <span>资源类型: 云主机</span>
            <span>规格: 4C8G</span>
            <span>云厂商: AWS</span>
          </div>
        </div>
        <div class="approval-actions">
          <span class="btn reject">驳回</span>
          <span class="btn approve">✅ 通过</span>
        </div>
      </div>

      <div class="approval-card">
        <div class="approval-header">
          <div class="applicant">
            <span class="avatar">李</span>
            <div class="applicant-info">
              <span class="name">李四</span>
              <span class="role">开发工程师</span>
            </div>
          </div>
          <span class="time">30分钟前</span>
        </div>
        <div class="approval-content">
          <div class="content-title">🔄 变更数据库配置</div>
          <div class="content-detail">
            <span>资源: db-master-01</span>
            <span>变更: 内存 16G → 32G</span>
          </div>
        </div>
        <div class="approval-actions">
          <span class="btn reject">驳回</span>
          <span class="btn approve">✅ 通过</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.approval-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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

.approval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.applicant {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  background: #667eea;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.name { font-size: 14px; font-weight: 600; color: #1a1a2e; display: block; }
.role { font-size: 12px; color: #94a3b8; display: block; }

.time {
  font-size: 12px;
  color: #94a3b8;
}

.approval-content {
  margin-bottom: 12px;
}

.content-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.content-detail {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
}

.approval-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn.reject {
  background: #f1f5f9;
  color: #64748b;
}

.btn.approve {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}
</style>
