<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">我的权限</div><div class="mock-user">👤 bob</div></div>
    <div class="mock-content">
      <h2 class="mock-title">我的权限</h2>
      <p class="mock-sub">按能力包维度查看：个人 / 组织 / 自建组 —— 每条授权都有对应申请单</p>

      <!-- 三维度 Tab -->
      <div class="tab-row">
        <div class="tab-item" :class="{ active: tab === 'personal' }" @click="tab = 'personal'">
          <span class="tab-icon">👤</span><span class="tab-name">个人权限</span><span class="tab-count">3</span>
        </div>
        <div class="tab-item" :class="{ active: tab === 'org' }" @click="tab = 'org'">
          <span class="tab-icon">🏢</span><span class="tab-name">组织权限</span><span class="tab-count">1</span>
        </div>
        <div class="tab-item" :class="{ active: tab === 'group' }" @click="tab = 'group'">
          <span class="tab-icon">👥</span><span class="tab-name">自建组权限</span><span class="tab-count">4</span>
        </div>
      </div>

      <!-- 个人权限 -->
      <div v-if="tab === 'personal'" class="perm-list">
        <div class="perm-card highlight">
          <div class="pc-head"><span class="pc-icon">🧩</span><span class="pc-name">新增服务</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">ITSM 工单 · 🔖 新增服务</div>
          <div class="pc-tags"><span class="tag blue">👤 个人</span><span class="tag gray">1 接口</span></div>
        </div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🖥️</span><span class="pc-name">新增服务器</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">ITSM 工单 · 🔖 新增服务器</div>
          <div class="pc-tags"><span class="tag blue">👤 个人</span><span class="tag gray">1 接口</span></div>
        </div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🗃️</span><span class="pc-name">主机管理</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">配置管理数据库 · 🔖 只读查看</div>
          <div class="pc-tags"><span class="tag blue">👤 个人</span><span class="tag gray">2 接口</span></div>
        </div>
      </div>

      <!-- 组织权限 -->
      <div v-if="tab === 'org'" class="perm-list">
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🧭</span><span class="pc-name">应用权限开通</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">ITSM 工单 · 🔖 应用权限开通</div>
          <div class="pc-tags"><span class="tag violet">🏢 组织继承</span><span class="tag gray">1 接口</span></div>
        </div>
      </div>

      <!-- 自建组权限 -->
      <div v-if="tab === 'group'" class="perm-list">
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🗄️</span><span class="pc-name">数据库管理</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">公共资源池 · 🔖 数据库管理</div>
          <div class="pc-tags"><span class="tag amber">👥 业务查询组</span><span class="tag gray">3 接口</span></div>
        </div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🖥️</span><span class="pc-name">主机管理</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">公共资源池 · 🔖 主机运维</div>
          <div class="pc-tags"><span class="tag amber">👥 测试环境运维组</span><span class="tag gray">5 接口</span></div>
        </div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🐳</span><span class="pc-name">测试环境容器登录</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">ITSM 工单 · 🔖 测试环境容器登录</div>
          <div class="pc-tags"><span class="tag amber">👥 业务查询组</span><span class="tag gray">1 接口</span></div>
        </div>
        <div class="perm-card">
          <div class="pc-head"><span class="pc-icon">🗃️</span><span class="pc-name">主机管理</span><span class="tag ok">已生效</span></div>
          <div class="pc-app">配置管理数据库 · 🔖 只读查看</div>
          <div class="pc-tags"><span class="tag amber">👥 测试环境运维组</span><span class="tag gray">2 接口</span></div>
          <div class="pc-foot">有效期至 2026-12-31 · 申请单 #18</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const tab = ref('personal')
</script>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 16px 22px; overflow: auto; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 11px; color: var(--text-secondary); margin-bottom: 12px; }
.tab-row { display: flex; gap: 8px; margin-bottom: 14px; }
.tab-item { display: flex; align-items: center; gap: 6px; padding: 8px 14px; border: 1.5px solid var(--border); border-radius: 8px; background: var(--bg-card); cursor: pointer; transition: all 0.15s; }
.tab-item:hover { border-color: var(--brand); }
.tab-item.active { border-color: var(--brand); background: var(--brand-soft); }
.tab-icon { font-size: 14px; }
.tab-name { font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.tab-item.active .tab-name { color: var(--brand); font-weight: 600; }
.tab-count { font-size: 11px; font-weight: 700; color: var(--text-tertiary); background: var(--bg-tertiary); padding: 1px 7px; border-radius: 10px; }
.tab-item.active .tab-count { background: var(--brand); color: #fff; }
.perm-list { display: flex; flex-direction: column; gap: 8px; }
.perm-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.perm-card.highlight { border-color: var(--brand); background: var(--brand-softer); }
.pc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.pc-icon { font-size: 18px; }
.pc-name { font-size: 14px; font-weight: 600; color: var(--text); flex: 1; }
.pc-app { font-size: 11px; color: var(--text-tertiary); margin-bottom: 6px; }
.pc-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.tag { font-size: 10px; padding: 2px 7px; border-radius: 8px; font-weight: 500; }
.tag.ok { color: var(--success); background: var(--success-bg); }
.tag.blue { color: var(--brand); background: var(--brand-soft); }
.tag.violet { color: var(--purple); background: var(--purple-bg); }
.tag.amber { color: var(--warning); background: var(--warning-bg); }
.tag.cyan { color: var(--info); background: var(--info-bg); }
.tag.gray { color: var(--text-tertiary); background: var(--bg-tertiary); }
.pc-foot { font-size: 10px; color: var(--text-tertiary); margin-top: 6px; }
</style>
