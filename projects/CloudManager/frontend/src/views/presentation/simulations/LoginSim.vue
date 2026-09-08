<script setup lang="ts">
defineProps<{
  showRoleHint?: boolean
}>()

const portalApps = [
  { name: 'Cloud Manager', desc: '多云资源管理平台', icon: '☁️', color: '#667eea' },
  { name: 'Permission Center', desc: '去中心化权限管理', icon: '🔐', color: '#10b981' },
  { name: 'Monitor System', desc: '基础设施监控', icon: '📊', color: '#f59e0b' },
  { name: 'CI/CD Pipeline', desc: '持续集成部署', icon: '🚀', color: '#ef4444' },
]
</script>

<template>
  <div class="login-sim">
    <div class="login-card">
      <div class="login-header">
        <div class="logo">🏢</div>
        <h2>统一门户</h2>
        <p>Enterprise Unified Portal · SSO Single Sign-On</p>
      </div>
      <div class="login-form">
        <div class="form-group">
          <label>选择登录方式</label>
          <div class="sso-options">
            <div class="sso-btn active">
              <span class="sso-icon">🔑</span>
              <span>企业 SSO 登录</span>
            </div>
            <div class="sso-btn">
              <span class="sso-icon">👤</span>
              <span>账号密码登录</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>企业邮箱</label>
          <div class="input-box">
            <span class="input-icon">📧</span>
            <span class="input-placeholder">your.name@company.com</span>
          </div>
        </div>
        <button class="login-btn">统一登录</button>
      </div>
      <div class="login-tip">
        <span class="tip-icon">💡</span>
        <span>登录后可访问所有内部系统，无需重复认证</span>
      </div>
    </div>

    <div class="portal-preview">
      <h3>🌐 门户应用</h3>
      <div class="app-grid">
        <div v-for="app in portalApps" :key="app.name" class="app-item">
          <div class="app-icon" :style="{ background: `${app.color}15`, color: app.color }">
            {{ app.icon }}
          </div>
          <div class="app-info">
            <div class="app-name">{{ app.name }}</div>
            <div class="app-desc">{{ app.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-sim {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  width: 100%;
  max-width: 340px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 20px;
}

.logo {
  font-size: 40px;
  margin-bottom: 10px;
}

.login-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 4px 0;
}

.login-header p {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.sso-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.sso-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.sso-btn.active {
  background: #eef2ff;
  border-color: #667eea;
  color: #667eea;
}

.sso-icon { font-size: 14px; }

.input-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
}

.input-icon { font-size: 14px; }
.input-placeholder { color: #94a3b8; }

.login-btn {
  width: 100%;
  padding: 11px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.login-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 10px;
  background: #f0fdf4;
  border-radius: 6px;
  font-size: 11px;
  color: #166534;
  text-align: center;
  justify-content: center;
}

.tip-icon { font-size: 12px; }

.portal-preview {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 20px;
  width: 100%;
  max-width: 300px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.portal-preview h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 14px 0;
}

.app-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.app-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.app-item:hover {
  background: #f1f5f9;
  transform: translateX(2px);
}

.app-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.app-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.app-desc {
  font-size: 11px;
  color: #94a3b8;
}
</style>
