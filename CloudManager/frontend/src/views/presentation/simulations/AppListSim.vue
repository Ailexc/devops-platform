<script setup lang="ts">
</script>

<template>
  <div class="app-sim">
    <div class="list-header">
      <h2>📦 应用中心</h2>
      <span class="btn-add">+ 新建应用</span>
    </div>

    <div class="app-grid">
      <div class="app-card">
        <div class="app-icon" style="background: #667eea15; color: #667eea;">📡</div>
        <div class="app-info">
          <div class="app-name">监控服务</div>
          <div class="app-desc">基础设施监控与告警</div>
        </div>
        <div class="app-status active">active</div>
        <div class="app-meta">
          <span>🖥️ 12 台主机</span>
          <span>🌐 3 个环境</span>
        </div>
      </div>

      <div class="app-card">
        <div class="app-icon" style="background: #10b98115; color: #10b981;">🛒</div>
        <div class="app-info">
          <div class="app-name">电商系统</div>
          <div class="app-desc">核心交易业务系统</div>
        </div>
        <div class="app-status active">active</div>
        <div class="app-meta">
          <span>🖥️ 28 台主机</span>
          <span>🌐 4 个环境</span>
        </div>
      </div>

      <div class="app-card">
        <div class="app-icon" style="background: #f59e0b15; color: #f59e0b;">📊</div>
        <div class="app-info">
          <div class="app-name">数据分析平台</div>
          <div class="app-desc">数据采集与分析</div>
        </div>
        <div class="app-status active">active</div>
        <div class="app-meta">
          <span>🖥️ 8 台主机</span>
          <span>🌐 2 个环境</span>
        </div>
      </div>

      <div class="app-card">
        <div class="app-icon" style="background: #ef444415; color: #ef4444;">🔐</div>
        <div class="app-info">
          <div class="app-name">权限中心</div>
          <div class="app-desc">统一身份认证与权限管理</div>
        </div>
        <div class="app-status active">active</div>
        <div class="app-meta">
          <span>🖥️ 6 台主机</span>
          <span>🌐 3 个环境</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-sim {
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

.btn-add {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.app-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.app-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
  cursor: pointer;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.app-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 12px;
}

.app-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.app-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 12px;
}

.app-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 12px;
}

.app-status.active {
  background: #d1fae5;
  color: #059669;
}

.app-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
