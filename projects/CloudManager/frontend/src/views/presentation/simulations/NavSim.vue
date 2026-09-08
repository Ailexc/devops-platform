<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<template>
  <div class="nav-sim">
    <div class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">☁️</span>
        <span class="logo-text">Cloud Manager</span>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-group">
          <div class="nav-group-title">概览</div>
          <div class="nav-item">
            <span class="nav-icon">📊</span>
            <span>工作台</span>
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">资源管理</div>
          <div class="nav-item-group">
            <div class="nav-item expandable">
              <span class="nav-icon">☁️</span>
              <span>资源管理</span>
              <span class="nav-arrow">›</span>
            </div>
            <div class="nav-children">
              <div class="nav-child">资源概览</div>
              <div class="nav-child">AWS</div>
              <div class="nav-child">阿里云</div>
              <div class="nav-child">腾讯云</div>
              <div class="nav-child">云账号管理</div>
            </div>
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">业务中心</div>
          <div class="nav-item">
            <span class="nav-icon">📦</span>
            <span>应用中心</span>
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">运维中心</div>
          <div class="nav-item">
            <span class="nav-icon">📋</span>
            <span>工单中心</span>
          </div>
          <div class="nav-item">
            <span class="nav-icon">🎯</span>
            <span>场景模板库</span>
          </div>
          <div class="nav-item">
            <span class="nav-icon">🕘</span>
            <span>操作记录</span>
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">财务管理</div>
          <div class="nav-item-group">
            <div class="nav-item expandable">
              <span class="nav-icon">💰</span>
              <span>成本管理</span>
              <span class="nav-arrow">›</span>
            </div>
            <div class="nav-children">
              <div class="nav-child">成本趋势</div>
              <div class="nav-child active">成本优化总览</div>
              <div class="nav-child">规则配置</div>
              <div class="nav-child">分析报告</div>
            </div>
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">系统演示</div>
          <div class="nav-item">
            <span class="nav-icon">🎬</span>
            <span>系统演示</span>
          </div>
        </div>
      </nav>
    </div>
    <div class="main-area">
      <div class="header">
        <span class="breadcrumb">首页 / 资源管理 / AWS</span>
      </div>
      <div class="content">
        <div class="hint-box">
          <span class="hint-icon">💡</span>
          <span>资源管理按云厂商组织：资源概览 → AWS/阿里云/腾讯云 → 云账号管理</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.nav-sim {
  display: flex;
  height: 100%;
  background: #f8fafc;
}

.sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #e5e7eb;
}

.logo-icon { font-size: 24px; }
.logo-text { font-size: 15px; font-weight: 600; color: #1a1a2e; }

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.nav-group {
  margin-bottom: 8px;
}

.nav-group-title {
  padding: 8px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-item, .nav-child {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover, .nav-child:hover {
  background: #f3f4f6;
  color: #1a1a2e;
}

.nav-item.active, .nav-child.active {
  background: #eef2ff;
  color: #667eea;
}

.nav-icon { font-size: 16px; }
.nav-arrow { margin-left: auto; font-size: 14px; color: #9ca3af; }

.nav-children {
  padding-left: 44px;
}

.nav-child {
  padding: 8px 16px;
  font-size: 13px;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.breadcrumb {
  font-size: 13px;
  color: #64748b;
}

.content {
  flex: 1;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hint-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  font-size: 14px;
  color: #166534;
}

.hint-icon { font-size: 20px; }
</style>
