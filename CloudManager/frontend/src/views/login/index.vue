<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// Mock 用户数据（仅用于显示，实际登录调用后端）
interface MockUser {
  id: number
  username: string
  display_name: string
  department: string
  role: string
  avatar_color: string
}

const mockUsers: MockUser[] = [
  {
    id: 1,
    username: 'admin',
    display_name: '系统管理员',
    department: '技术部 / 平台架构组',
    role: '超级管理员',
    avatar_color: 'linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)',
  },
  {
    id: 2,
    username: 'cloud_admin',
    display_name: '云管理员',
    department: '技术部 / 云平台组',
    role: '云管理员',
    avatar_color: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
  },
  {
    id: 3,
    username: 'ops_user',
    display_name: '运维工程师',
    department: '运维部 / SRE团队',
    role: '运维工程师',
    avatar_color: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
  },
  {
    id: 4,
    username: 'readonly',
    display_name: '只读用户',
    department: '研发组',
    role: '只读用户',
    avatar_color: 'linear-gradient(135deg, #6B7280 0%, #4B5563 100%)',
  },
]

const selectedUserId = ref<number | null>(null)
const loading = ref(false)

const selectedUser = computed(() => {
  return mockUsers.find(u => u.id === selectedUserId.value)
})

async function handleLogin() {
  if (!selectedUserId.value) {
    message.warning('请选择一个用户')
    return
  }
  
  loading.value = true
  
  try {
    const user = selectedUser.value!
    
    // 调用后端登录接口，使用统一密码
    const response = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: user.username,
        password: 'admin123'
      })
    })
    
    if (!response.ok) {
      throw new Error('登录失败')
    }
    
    const data = await response.json()
    
    // 保存 token 和用户信息
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_info', JSON.stringify(data.user))
    
    // 更新 store
    userStore.user = data.user
    userStore.token = data.access
    userStore.isLoggedIn = true
    
    message.success(`欢迎回来，${data.user.display_name}！`)
    router.push('/dashboard')
    
  } catch (error: any) {
    message.error(error.message || '登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="login-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="gradient-orb orb-4"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo 和标题 -->
      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
          </svg>
        </div>
        <h1 class="login-title">Cloud Manager</h1>
        <p class="login-subtitle">多云资源管理平台</p>
      </div>

      <!-- 用户选择表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">选择用户登录</label>
          <div class="user-select-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <select 
              class="user-select" 
              v-model="selectedUserId"
            >
              <option :value="null" disabled>请选择用户...</option>
              <option 
                v-for="user in mockUsers" 
                :key="user.id" 
                :value="user.id"
              >
                {{ user.department }} - {{ user.display_name }}（{{ user.role }}）
              </option>
            </select>
            <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </div>

        <!-- 用户预览卡片 -->
        <div v-if="selectedUser" class="user-preview">
          <div class="user-avatar" :style="{ background: selectedUser.avatar_color }">
            {{ selectedUser.display_name.charAt(0) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ selectedUser.display_name }}</div>
            <div class="user-dept">{{ selectedUser.department }}</div>
            <div class="user-role">
              <span class="role-tag">{{ selectedUser.role }}</span>
            </div>
          </div>
        </div>

        <button type="submit" class="login-button" :disabled="loading || !selectedUserId">
          <span v-if="!loading">进入系统</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </form>

      <!-- 提示信息 -->
      <div class="demo-hint">
        <svg class="hint-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M12 16v-4"></path>
          <path d="M12 8h.01"></path>
        </svg>
        <span>统一密码：admin123（Demo 环境）</span>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="login-footer">
      <p>© 2026 Cloud Manager · 多云资源管理平台</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #F8FAFC;
}

.login-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
  top: -200px;
  right: -100px;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
  bottom: -150px;
  left: -100px;
  animation-delay: -5s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

.orb-4 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  top: 20%;
  left: 20%;
  animation-delay: -15s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -20px) scale(1.05); }
  50% { transform: translate(-10px, 20px) scale(0.95); }
  75% { transform: translate(15px, 10px) scale(1.02); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(124, 58, 237, 0.4);
}

.logo-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #64748B;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.user-select-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #9CA3AF;
  pointer-events: none;
  z-index: 1;
}

.user-select {
  width: 100%;
  padding: 14px 48px 14px 48px;
  font-size: 14px;
  font-family: inherit;
  color: #1E293B;
  background: white;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s;
  outline: none;
}

.user-select:hover {
  border-color: #D1D5DB;
}

.user-select:focus {
  border-color: #7C3AED;
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.1);
}

.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #9CA3AF;
  pointer-events: none;
}

.user-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid #E2E8F0;
}

.user-avatar {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 2px;
}

.user-dept {
  font-size: 12px;
  color: #64748B;
  margin-bottom: 6px;
}

.user-role {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-tag {
  padding: 2px 8px;
  background: #EDE9FE;
  color: #7C3AED;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.login-button {
  width: 100%;
  padding: 16px 24px;
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  color: white;
  background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
}

.login-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #6D28D9 0%, #4338CA 100%);
  opacity: 0;
  transition: opacity 0.2s;
}

.login-button:hover:not(:disabled)::before {
  opacity: 1;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
}

.login-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.login-button span {
  position: relative;
  z-index: 1;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.demo-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: #FEF3C7;
  border-radius: 10px;
  font-size: 13px;
  color: #92400E;
  border: 1px solid #FDE68A;
}

.hint-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #F59E0B;
}

.login-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  z-index: 1;
}

.login-footer p {
  font-size: 13px;
  color: #9CA3AF;
  margin: 0;
}

@media (max-width: 480px) {
  .login-card {
    margin: 16px;
    padding: 32px 24px;
  }
}
</style>
