<template>
  <div class="app">
    <header class="hd">
      <div class="hd-l">
        <h1>🏗️ CMDB 数据维护平台</h1>
        <span class="ver">v0.1 dev</span>
      </div>
      <div class="hd-r">
        <select
          v-model="backendKey"
          class="backend-switch"
          @change="onBackendSwitch"
          title="切换后端实现（API 契约不变）"
        >
          <option value="python">Python 后端 (Django + Celery)</option>
          <option value="go">Go 后端 (Gin + asynq)</option>
        </select>
        <span class="user-chip" v-if="username" title="当前登录用户（统一认证 SSO）">👤 {{ username }}</span>
        <span><span class="hl"></span>系统运行中</span>
        <span>Redis 正常 · 3 Worker 在线</span>
        <span>上次全量: 2026-07-25 04:00</span>
      </div>
    </header>

    <nav class="tab-bar">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="tab-b"
        :class="{ act: $route.path === tab.path }"
      >
        <span class="ic">{{ tab.icon }}</span>{{ tab.label }}
      </router-link>
    </nav>

    <main class="ct">
      <router-view />
    </main>
  </div>
</template>

<script>
import { getCurrentBackend, switchBackend, fetchCurrentUser } from './api/index.js'

export default {
  name: 'App',
  data() {
    return {
      backendKey: getCurrentBackend(),
      username: localStorage.getItem('cmdb.user') || '',
      tabs: [
        { path: '/dashboard', icon: '📊', label: '监控大盘' },
        { path: '/tasks', icon: '⚙️', label: '任务管理' },
        { path: '/history', icon: '📋', label: '执行历史' },
        { path: '/docs', icon: '📄', label: '系统文档' },
        { path: '/interview', icon: '🎤', label: '面试手册' },
      ],
    }
  },
  mounted() {
    this.loadUser()
  },
  methods: {
    onBackendSwitch() {
      switchBackend(this.backendKey)
      // 切换后重新加载，全部请求走新后端
      location.reload()
    },
    async loadUser() {
      if (!localStorage.getItem('cmdb.token')) return
      try {
        const res = await fetchCurrentUser()
        this.username = res.data.username
        localStorage.setItem('cmdb.user', res.data.username)
      } catch {
        /* 未认证则保持匿名 */
      }
    },
  },
}
</script>


<style>
:root {
  --bg: #f0f2f5;
  --card: #fff;
  --border: #e9ecef;
  --text: #212529;
  --t2: #6c757d;
  --blue: #4361ee;
  --bl: #eef1ff;
  --teal: #2ec4b6;
  --tl: #e6faf7;
  --coral: #ff6b6b;
  --cl: #ffe8e8;
  --amber: #ffd166;
  --al: #fff8e0;
  --purple: #7c3aed;
  --pl: #f0e8ff;
  --orange: #f97316;
  --ol: #fff3e6;
  --radius: 14px;
  --rs: 10px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}

.hd {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  padding: 18px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.hd-l { display: flex; align-items: center; gap: 12px; }
.hd-l h1 { color: #fff; font-size: 17px; font-weight: 700; }
.hd-l .ver {
  font-size: 9px; color: rgba(255,255,255,.4);
  background: rgba(255,255,255,.08); padding: 2px 8px;
  border-radius: 5px; font-weight: 600;
}
.hd-r { font-size: 11px; color: rgba(255,255,255,.5); display: flex; align-items: center; gap: 12px; }
.backend-switch {
  font-size: 11px; color: #333; background: #fff;
  border: 1px solid rgba(255,255,255,.25); border-radius: 6px;
  padding: 3px 6px; cursor: pointer; outline: none;
}
.backend-switch:focus { border-color: var(--blue); }
.hd-r .hl {
  width: 4px; height: 4px; border-radius: 50%; background: var(--teal);
  display: inline-block; margin-right: 3px;
  animation: pu 1.5s infinite;
}
@keyframes pu { 0%,100%{opacity:1} 50%{opacity:.2} }

.tab-bar {
  background: #fff; border-bottom: 1px solid var(--border);
  padding: 0 24px; display: flex; position: sticky; top: 0; z-index: 10;
}
.tab-b {
  padding: 10px 18px; font-size: 12px; font-weight: 500;
  border: none; background: none; cursor: pointer;
  color: var(--t2); border-bottom: 2px solid transparent;
  text-decoration: none; transition: all .15s;
}
.tab-b:hover { color: var(--text); }
.tab-b.act { color: var(--blue); border-bottom-color: var(--blue); font-weight: 600; }
.tab-b .ic { margin-right: 4px; }

.ct { max-width: 1240px; margin: 0 auto; padding: 14px 18px 36px; }
</style>
