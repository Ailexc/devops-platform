<script setup lang="ts">
import { ref } from 'vue'

const selectedDept = ref('tech')

const orgTree = [
  {
    id: 'tech',
    name: '技术部',
    icon: '💻',
    children: [
      { id: 'platform', name: '平台架构组', appCount: 3 },
      { id: 'cloud', name: '云平台组', appCount: 2 },
    ],
  },
  {
    id: 'ops',
    name: '运维部',
    icon: '🔧',
    children: [
      { id: 'sre', name: 'SRE团队', appCount: 2 },
      { id: 'app-ops', name: '应用运维', appCount: 1 },
    ],
  },
  {
    id: 'data',
    name: '数据部',
    icon: '📊',
    children: [
      { id: 'data-dev', name: '数据开发', appCount: 2 },
      { id: 'data-analysis', name: '数据分析', appCount: 1 },
    ],
  },
]

const apps = [
  { id: 1, name: 'Cloud Manager', desc: '多云资源管理平台', dept: 'platform', icon: '☁️', envs: ['dev', 'test', 'staging', 'prod'], status: 'active', resources: 32 },
  { id: 2, name: 'Permission Center', desc: '去中心化权限管理', dept: 'platform', icon: '🔐', envs: ['dev', 'test', 'prod'], status: 'active', resources: 18 },
  { id: 3, name: 'Config Service', desc: '配置中心', dept: 'platform', icon: '⚙️', envs: ['dev', 'test', 'prod'], status: 'active', resources: 8 },
  { id: 4, name: 'Monitor System', desc: '基础设施监控', dept: 'sre', icon: '📡', envs: ['dev', 'test', 'prod'], status: 'active', resources: 15 },
  { id: 5, name: 'Log Platform', desc: '日志收集与分析', dept: 'sre', icon: '📝', envs: ['dev', 'test', 'prod'], status: 'active', resources: 12 },
  { id: 6, name: 'CI/CD Pipeline', desc: '持续集成部署', dept: 'app-ops', icon: '🚀', envs: ['dev', 'test'], status: 'active', resources: 6 },
  { id: 7, name: 'Data Warehouse', desc: '数据仓库', dept: 'data-dev', icon: '🗄️', envs: ['dev', 'prod'], status: 'active', resources: 20 },
  { id: 8, name: 'BI Dashboard', desc: '数据分析看板', dept: 'data-analysis', icon: '📊', envs: ['dev', 'test', 'prod'], status: 'active', resources: 8 },
]

const envColors: Record<string, string> = {
  dev: '#10b981',
  test: '#3b82f6',
  staging: '#f59e0b',
  prod: '#ef4444',
}

const envLabels: Record<string, string> = {
  dev: '开发',
  test: '测试',
  staging: '预发',
  prod: '生产',
}

const filteredApps = computed(() => {
  const deptIds = orgTree
    .find(d => d.id === selectedDept.value)
    ?.children.map(c => c.id) || []
  return apps.filter(app => deptIds.includes(app.dept))
})
</script>

<template>
  <div class="app-center-sim">
    <!-- 左侧：组织架构树 -->
    <div class="org-sidebar">
      <div class="sidebar-header">
        <h3>组织架构</h3>
      </div>
      <div class="org-tree">
        <div v-for="dept in orgTree" :key="dept.id" class="org-dept">
          <div 
            class="dept-item"
            :class="{ active: selectedDept === dept.id }"
            @click="selectedDept = dept.id"
          >
            <span class="dept-icon">{{ dept.icon }}</span>
            <span class="dept-name">{{ dept.name }}</span>
            <span class="dept-arrow">›</span>
          </div>
          <div class="dept-children">
            <div 
              v-for="child in dept.children" 
              :key="child.id"
              class="child-item"
            >
              <span class="child-dot"></span>
              <span class="child-name">{{ child.name }}</span>
              <span class="child-count">{{ child.appCount }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：应用列表 -->
    <div class="app-content">
      <div class="content-header">
        <div class="breadcrumb">
          <span class="link">技术部</span> / <span>平台架构组</span>
        </div>
        <h2>应用列表</h2>
        <div class="header-actions">
          <span class="btn-add">+ 新建应用</span>
        </div>
      </div>

      <div class="app-list">
        <div v-for="app in filteredApps" :key="app.id" class="app-card">
          <div class="app-header">
            <div class="app-icon" :style="{ background: '#f1f5f9' }">{{ app.icon }}</div>
            <div class="app-info">
              <div class="app-name">{{ app.name }}</div>
              <div class="app-desc">{{ app.desc }}</div>
            </div>
            <div class="app-status active">active</div>
          </div>
          <div class="app-envs">
            <span 
              v-for="env in app.envs" 
              :key="env"
              class="env-tag"
              :style="{ background: `${envColors[env]}15`, color: envColors[env] }"
            >
              {{ envLabels[env] }}
            </span>
          </div>
          <div class="app-meta">
            <span class="meta-item">🖥️ {{ app.resources }} 资源</span>
            <span class="meta-item">📊 拓扑图可用</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { computed } from 'vue'
</script>

<style scoped>
.app-center-sim {
  display: flex;
  height: 100%;
  background: #f1f5f9;
}

/* 左侧组织架构 */
.org-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.org-tree {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.org-dept {
  margin-bottom: 4px;
}

.dept-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.dept-item:hover {
  background: #f8fafc;
}

.dept-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.dept-icon { font-size: 16px; }
.dept-name { flex: 1; font-size: 13px; font-weight: 500; }
.dept-arrow { font-size: 12px; color: #94a3b8; }

.dept-children {
  padding-left: 42px;
}

.child-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px 6px 0;
  font-size: 12px;
  color: #64748b;
}

.child-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
}

.child-name { flex: 1; }
.child-count { color: #94a3b8; font-size: 11px; }

/* 右侧内容 */
.app-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.breadcrumb {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.link { color: #2563eb; cursor: pointer; }

.content-header h2 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-add {
  padding: 8px 16px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.app-list {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  align-content: start;
}

.app-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.app-card:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}

.app-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.app-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.app-info { flex: 1; }
.app-name { font-size: 14px; font-weight: 600; color: #0f172a; }
.app-desc { font-size: 12px; color: #64748b; }

.app-status {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.app-status.active {
  background: #dcfce7;
  color: #16a34a;
}

.app-envs {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.env-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.app-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #64748b;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>