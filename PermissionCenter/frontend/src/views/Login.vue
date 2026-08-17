<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="orb orb-1"></div><div class="orb orb-2"></div>
    </div>
    <div class="login-card">
      <div class="brand">
        <div class="brand-logo">PC</div>
        <div>
          <div class="brand-name">Permission Center</div>
          <div class="brand-sub">权限中心控制台 · Decentralized IAM</div>
        </div>
      </div>
      <form @submit.prevent="doLogin" class="login-form">
        <label class="field-label">选择人员（DEMO · 免密码）</label>
        <select v-model="selected" class="people-select" :disabled="loading">
          <option v-for="p in people" :key="p.username" :value="p.username">
            {{ p.org_path ? p.org_path + ' · ' + p.display_name : p.display_name }}{{ p.is_admin ? '（管理员）' : p.is_leader ? '（组长）' : '' }}
          </option>
        </select>
        <button type="submit" class="btn btn-primary btn-full" :disabled="loading || !selected">
          {{ loading ? '登录中…' : '一键登录' }}
        </button>
        <div class="login-tip">演示系统：选择人员即登录 · 支持快速切换视角</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const people = ref<any[]>([])
const selected = ref('')
const loading = ref(false)
const router = useRouter()

onMounted(async () => {
  try {
    const d: any = await api.people()
    people.value = d.items || []
    const first = people.value.find((p: any) => !p.is_admin) || people.value[0]
    selected.value = first?.username || ''
  } catch { /* ignore */ }
})

async function doLogin() {
  if (!selected.value) return
  loading.value = true
  try {
    const data: any = await api.demoLogin(selected.value)
    localStorage.setItem('iam_token', data.access_token)
    if (data.user) localStorage.setItem('iam_user', JSON.stringify(data.user))
    router.push('/')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); position: relative; overflow: hidden; padding: 20px; }
.login-bg { position: absolute; inset: 0; pointer-events: none; }
.orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: .45; }
.orb-1 { width: 420px; height: 420px; background: var(--brand); top: -120px; left: -80px; }
.orb-2 { width: 360px; height: 360px; background: #60a5fa; bottom: -100px; right: -60px; }
.login-card { position: relative; width: 400px; max-width: 100%; background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow-lg); padding: 32px; }
.brand { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.brand-logo { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, var(--brand), var(--brand-strong)); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; }
.brand-name { font-size: 16px; font-weight: 700; }
.brand-sub { font-size: 12px; color: var(--text-tertiary); }
.login-form { display: flex; flex-direction: column; gap: 14px; }
.field-label { font-size: 13px; font-weight: 600; }
.people-select { height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; height: 40px; border-radius: 8px; font-size: 14px; font-weight: 600; border: 1px solid transparent; cursor: pointer; }
.btn-primary { background: var(--brand); color: #fff; }
.btn-primary:hover { background: var(--brand-strong); }
.btn-full { width: 100%; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.login-tip { font-size: 12px; color: var(--text-tertiary); text-align: center; }
</style>
