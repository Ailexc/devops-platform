<template>
  <div class="mock-screen login-screen">
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-icon">PC</div>
        <div class="logo-text">Permission Center</div>
        <div class="logo-sub">权限中心</div>
      </div>
      <div class="login-form">
        <div class="form-label">选择登录身份</div>
        <div class="user-select">
          <div class="user-option" v-for="u in users" :key="u.name" :class="{ selected: selected === u.name }" @click="selected = u.name">
            <div class="user-avatar" :style="{ background: u.color }">{{ u.name[0] }}</div>
            <div class="user-meta">
              <div class="user-name">{{ u.name }}</div>
              <div class="user-role">{{ u.role }}</div>
            </div>
          </div>
        </div>
        <button class="login-btn">登 录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const selected = ref('小黄')
const users = [
  { name: '小黄', role: '应用 Owner · 监控服务', color: '#2f6fed' },
  { name: '小红', role: '普通用户 · 研发一部', color: '#dc2626' },
  { name: 'admin', role: '系统管理员', color: '#7c3aed' },
]
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; padding: 24px; }
.login-card { width: 380px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow-lg); overflow: hidden; }
.login-logo { text-align: center; padding: 32px 24px 20px; background: linear-gradient(135deg, var(--brand) 0%, #1e5ad7 100%); color: #fff; }
.logo-icon { width: 48px; height: 48px; border-radius: 12px; background: rgba(255,255,255,0.2); display: inline-flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; margin-bottom: 12px; }
.logo-text { font-size: 18px; font-weight: 600; }
.logo-sub { font-size: 12px; opacity: 0.8; margin-top: 2px; }
.login-form { padding: 24px; }
.form-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.user-select { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.user-option { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px; cursor: pointer; transition: all 0.15s; }
.user-option:hover { border-color: var(--brand); background: var(--brand-softer); }
.user-option.selected { border-color: var(--brand); background: var(--brand-soft); }
.user-avatar { width: 36px; height: 36px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; flex-shrink: 0; }
.user-meta { display: flex; flex-direction: column; }
.user-name { font-size: 14px; font-weight: 600; color: var(--text); }
.user-role { font-size: 12px; color: var(--text-tertiary); }
.login-btn { width: 100%; padding: 10px; border: none; border-radius: 8px; background: var(--brand); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.login-btn:hover { background: var(--brand-strong); }
</style>
