<template>
  <div class="login-sim">
    <div class="login-card">
      <div class="login-logo">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" width="40" height="40">
          <rect width="32" height="32" rx="8" fill="url(#g)"/>
          <path d="M8 10h16v2.5H8zM8 15h11v2.5H8zM8 20h6v2.5H8z" fill="#fff" fill-opacity=".9"/>
          <circle cx="24" cy="22" r="4" fill="#4ADE80"/>
          <defs><linearGradient id="g" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#409EFF"/><stop offset="1" stop-color="#2563EB"/></linearGradient></defs>
        </svg>
        <div>
          <div class="logo-title">Workflow</div>
          <div class="logo-sub">流程驱动的业务自动化平台</div>
        </div>
      </div>
      <div class="login-form">
        <label>选择用户</label>
        <div class="user-select">
          <span class="selected-user">👤 {{ currentUser }}</span>
          <span class="select-arrow">▼</span>
        </div>
        <button class="login-btn">快速登录</button>
      </div>
      <div class="login-hint">开发环境：选择用户后直接登录，无需输入密码</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const currentUser = '系统管理员（admin）'
</script>

<style scoped lang="scss">
.login-sim {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
}

.logo-sub {
  font-size: 12px;
  color: #94a3b8;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;

  label {
    font-size: 13px;
    color: #64748b;
    font-weight: 500;
  }
}

.user-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  cursor: pointer;
}

.selected-user {
  font-size: 14px;
  color: #374151;
}

.select-arrow {
  font-size: 10px;
  color: #94a3b8;
}

.login-btn {
  padding: 12px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.login-hint {
  margin-top: 16px;
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
}
</style>
