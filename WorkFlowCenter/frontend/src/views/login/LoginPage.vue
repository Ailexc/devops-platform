<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="48" height="48" rx="12" fill="white" fill-opacity="0.15"/>
              <path d="M14 16h20v4H14zM14 24h14v4H14zM14 32h8v4H14z" fill="white"/>
              <circle cx="36" cy="34" r="6" fill="#4ADE80" stroke="white" stroke-width="2"/>
              <path d="M34 34l2 2 3-3" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1>Workflow</h1>
        </div>
        <p class="brand-tagline">流程驱动的业务自动化平台</p>
        <div class="brand-features">
          <div class="feature-item">
            <div class="feature-icon">⚡</div>
            <div>
              <div class="feature-title">高效流程</div>
              <div class="feature-desc">可视化流程设计，快速搭建审批链路</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🔒</div>
            <div>
              <div class="feature-title">安全可靠</div>
              <div class="feature-desc">完善的权限体系，数据安全有保障</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <div>
              <div class="feature-title">智能分析</div>
              <div class="feature-desc">实时数据看板，流程效率一目了然</div>
            </div>
          </div>
        </div>
      </div>
      <div class="brand-footer">
        <span>© 2026 Workflow Platform · Powered by Beeflow</span>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-panel">
      <div class="login-card">
        <div class="login-header">
          <h2>欢迎回来</h2>
          <p>选择用户快速登录系统</p>
        </div>

        <div class="quick-login-form">
          <div class="form-group">
            <label class="form-label">选择用户</label>
            <el-select
              v-model="selectedUserId"
              placeholder="请选择要登录的用户"
              size="large"
              class="user-select"
              :loading="loadingUsers"
              filterable
            >
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="getUserLabel(user)"
                :value="user.id"
              />
            </el-select>
          </div>

          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            :disabled="!selectedUserId"
            @click="handleQuickLogin"
          >
            快速登录
          </el-button>
        </div>

        <div class="login-footer">
          <div class="tip-text">
            <el-icon><InfoFilled /></el-icon>
            <span>开发环境：选择用户后直接登录，无需输入密码</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getQuickLoginUsers } from '@/api/modules/auth'
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const users = ref([])
const selectedUserId = ref(null)
const loadingUsers = ref(false)
const loading = ref(false)

const getUserDisplayName = (user) => {
  if (user.first_name && user.last_name) {
    return `${user.last_name}${user.first_name}`
  }
  return user.username
}

const getUserLabel = (user) => {
  const name = getUserDisplayName(user)
  const dept = user.department__name || '未分配'
  return `${dept}-${name}`
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await getQuickLoginUsers()
    users.value = response.data || response
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loadingUsers.value = false
  }
}

const handleQuickLogin = async () => {
  if (!selectedUserId.value) {
    ElMessage.warning('请选择用户')
    return
  }

  loading.value = true
  try {
    const result = await authStore.quickLogin(selectedUserId.value)
    if (result.success) {
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } else {
      ElMessage.error(result.error || '登录失败')
    }
  } catch (error) {
    ElMessage.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  overflow: hidden;
}

/* 左侧品牌区 */
.login-brand {
  flex: 1;
  background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 50%, #0a1929 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}
.login-brand::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 50%, rgba(64, 158, 255, 0.08) 0%, transparent 50%),
              radial-gradient(circle at 70% 80%, rgba(103, 194, 58, 0.06) 0%, transparent 40%);
  pointer-events: none;
}
.brand-content {
  position: relative;
  z-index: 1;
  max-width: 480px;
  width: 100%;
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.logo-icon svg {
  width: 56px;
  height: 56px;
}
.brand-logo h1 {
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  margin: 0;
  letter-spacing: -0.5px;
}
.brand-tagline {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 48px;
  line-height: 1.6;
}
.brand-features {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.feature-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}
.feature-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
  line-height: 1.5;
}
.brand-footer {
  position: absolute;
  bottom: 32px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.25);
}

/* 右侧登录区 */
.login-panel {
  width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fc;
  padding: 60px;
}
.login-card {
  width: 100%;
  max-width: 380px;
}
.login-header {
  margin-bottom: 40px;
}
.login-header h2 {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
}
.login-header p {
  margin: 0;
  font-size: 14px;
  color: #86909c;
}

.quick-login-form {
  width: 100%;
}
.form-group {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}
.user-select {
  width: 100%;
}
.user-select :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
}
.user-select :deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc !important;
  box-shadow: none !important;
}
.user-select :deep(.el-input__wrapper.is-focus),
.user-select :deep(.el-input.is-focus .el-input__wrapper),
.user-select :deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: none !important;
  border-color: #dcdfe6 !important;
  outline: none !important;
}
.user-select :deep(.el-input__inner:focus) {
  outline: none !important;
}
.login-button {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  margin-top: 8px;
}



.login-footer {
  text-align: center;
  margin-top: 32px;
}
.tip-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 8px 16px;
  border-radius: 6px;
}

/* 响应式 */
@media (max-width: 900px) {
  .login-brand { display: none; }
  .login-panel { width: 100%; }
}
</style>

<!-- 非 scoped：覆盖 Element Plus 下拉框 focus 蓝色边框 -->
<style>
.login-page .el-select .el-select__wrapper {
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
  transition: border-color 0.2s !important;
}
.login-page .el-select .el-select__wrapper:hover {
  border-color: #c0c4cc !important;
}
.login-page .el-select .el-select__wrapper:focus-within {
  box-shadow: none !important;
  border-color: #dcdfe6 !important;
}
.login-page .el-select .el-select__input:focus {
  outline: none !important;
  box-shadow: none !important;
}
</style>
