<template>
  <div class="arch-overview">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>🏗️</span></div>
        <div>
          <h1>系统架构</h1>
          <p class="page-header-desc">技术栈全景与部署架构</p>
        </div>
      </div>
    </div>

    <!-- 架构分层 -->
    <div class="arch-layers">
      <div class="arch-layer" v-for="(layer, idx) in layers" :key="layer.name">
        <div class="layer-header" :style="{ borderLeftColor: layer.color }">
          <span class="layer-icon">{{ layer.icon }}</span>
          <span class="layer-name">{{ layer.name }}</span>
          <span class="layer-desc">{{ layer.desc }}</span>
        </div>
        <div class="layer-techs">
          <div class="tech-card" v-for="tech in layer.techs" :key="tech.name">
            <div class="tech-name">{{ tech.name }}</div>
            <div class="tech-role">{{ tech.role }}</div>
          </div>
        </div>
        <div class="layer-arrow" v-if="idx < layers.length - 1">↓</div>
      </div>
    </div>

    <!-- 部署信息 -->
    <div class="deploy-row">
      <div class="deploy-card" v-for="d in deployInfo" :key="d.label">
        <div class="dc-icon">{{ d.icon }}</div>
        <div class="dc-info">
          <div class="dc-label">{{ d.label }}</div>
          <div class="dc-value">{{ d.value }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const layers = [
  {
    name: '前端层',
    desc: '响应式 SPA',
    icon: '🖥️',
    color: '#409eff',
    techs: [
      { name: 'Vue 3', role: '响应式框架，Composition API' },
      { name: 'Element Plus', role: 'UI 组件库' },
      { name: 'Pinia', role: '状态管理' },
      { name: 'Vue Router', role: '路由与权限控制' },
    ],
  },
  {
    name: '后端层',
    desc: 'RESTful API',
    icon: '⚙️',
    color: '#67c23a',
    techs: [
      { name: 'Django 5', role: 'Web 框架' },
      { name: 'DRF', role: 'RESTful API 序列化与视图' },
      { name: 'django-fsm', role: '流程状态机' },
      { name: 'SimpleJWT', role: 'JWT 认证鉴权' },
    ],
  },
  {
    name: '异步层',
    desc: '任务与事件',
    icon: '⚡',
    color: '#e6a23c',
    techs: [
      { name: 'Celery', role: '分布式任务队列' },
      { name: 'Redis', role: '消息 Broker + 缓存' },
      { name: 'EventBus', role: '事件发布与投递' },
    ],
  },
  {
    name: '数据层',
    desc: '持久化存储',
    icon: '💾',
    color: '#f56c6c',
    techs: [
      { name: 'PostgreSQL', role: '关系型数据库' },
      { name: 'SQLite', role: '开发环境轻量存储' },
    ],
  },
  {
    name: '部署层',
    desc: '容器化编排',
    icon: '📦',
    color: '#909399',
    techs: [
      { name: 'Docker', role: '容器化打包' },
      { name: 'Docker Compose', role: '多服务编排' },
      { name: 'Nginx', role: '反向代理 + 静态资源' },
    ],
  },
]

const deployInfo = [
  { icon: '🐳', label: '容器数量', value: '3 个服务' },
  { icon: '🌐', label: '访问入口', value: 'Nginx → 前端 / API' },
  { icon: '🔄', label: '数据库迁移', value: 'Django migrate 自动执行' },
  { icon: '🚀', label: '一键部署', value: 'docker compose up' },
]
</script>

<style scoped lang="scss">
.arch-overview { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; display: flex; flex-direction: column; }

.page-header {
  display: flex; align-items: center; background: #fff;
  border-bottom: 1px solid #e5e6eb; padding: 14px 24px; flex-shrink: 0;
}
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header-icon {
  width: 36px; height: 36px; border-radius: 10px; background: #e6f7ff;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.page-header h1 { font-size: 17px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 12px; color: #86909c; margin: 1px 0 0; }

.arch-layers { padding: 16px 24px 0; flex: 1; }

.arch-layer { margin-bottom: 8px; }
.layer-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #fff; border-radius: 8px; border-left: 4px solid;
  border: 1px solid #f2f3f5; border-left: 4px solid; margin-bottom: 8px;
}
.layer-icon { font-size: 16px; }
.layer-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.layer-desc { font-size: 12px; color: #86909c; margin-left: auto; }

.layer-techs {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  padding: 0 8px; margin-bottom: 4px;
}
.tech-card {
  background: #fff; border: 1px solid #f2f3f5; border-radius: 8px;
  padding: 10px 14px;
}
.tech-name { font-size: 13px; font-weight: 600; color: #1d2129; margin-bottom: 2px; }
.tech-role { font-size: 11px; color: #86909c; line-height: 1.4; }

.layer-arrow {
  text-align: center; color: #c9cdd4; font-size: 14px; line-height: 1;
  padding: 2px 0;
}

.deploy-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  padding: 0 24px 20px;
}
.deploy-card {
  display: flex; align-items: center; gap: 10px; background: #fff;
  border: 1px solid #f2f3f5; border-radius: 8px; padding: 12px 16px;
}
.dc-icon { font-size: 22px; }
.dc-label { font-size: 11px; color: #86909c; }
.dc-value { font-size: 13px; font-weight: 600; color: #1d2129; }
</style>
