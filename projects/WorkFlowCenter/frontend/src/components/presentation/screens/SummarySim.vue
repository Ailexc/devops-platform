<template>
  <div class="summary-sim">
    <div class="summary-content">
      <!-- 架构视图 -->
      <template v-if="focus === 'architecture'">
        <div class="summary-icon">🏗️</div>
        <h1 class="summary-title">技术架构</h1>
        <p class="summary-subtitle">前后端分离，现代化技术栈</p>
        <div class="arch-grid">
          <div class="arch-card">
            <div class="arch-layer">前端层</div>
            <div class="arch-items">
              <span class="arch-item">Vue 3</span>
              <span class="arch-item">Element Plus</span>
              <span class="arch-item">Pinia</span>
            </div>
          </div>
          <div class="arch-card">
            <div class="arch-layer">后端层</div>
            <div class="arch-items">
              <span class="arch-item">Django 5</span>
              <span class="arch-item">DRF</span>
              <span class="arch-item">django-fsm</span>
            </div>
          </div>
          <div class="arch-card">
            <div class="arch-layer">基础设施</div>
            <div class="arch-items">
              <span class="arch-item">Celery</span>
              <span class="arch-item">Redis</span>
              <span class="arch-item">PostgreSQL</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 模块视图 -->
      <template v-else-if="focus === 'modules'">
        <div class="summary-icon">🧩</div>
        <h1 class="summary-title">核心模块</h1>
        <p class="summary-subtitle">六大模块，覆盖完整业务链路</p>
        <div class="feature-grid">
          <div class="feature-card" v-for="m in modules" :key="m.title">
            <div class="feature-icon">{{ m.icon }}</div>
            <div class="feature-title">{{ m.title }}</div>
            <div class="feature-desc">{{ m.desc }}</div>
          </div>
        </div>
      </template>

      <!-- 外部集成视图 -->
      <template v-else-if="focus === 'integration'">
        <div class="summary-icon">🔗</div>
        <h1 class="summary-title">外部集成</h1>
        <p class="summary-subtitle">开放 API · Webhook · 事件驱动</p>
        <div class="arch-grid">
          <div class="arch-card">
            <div class="arch-layer">RESTful API</div>
            <div class="arch-items">
              <span class="arch-item">API Key 认证</span>
              <span class="arch-item">程序发起流程</span>
              <span class="arch-item">异步执行回调</span>
            </div>
          </div>
          <div class="arch-card">
            <div class="arch-layer">Webhook</div>
            <div class="arch-items">
              <span class="arch-item">事件回调订阅</span>
              <span class="arch-item">HMAC 签名验证</span>
              <span class="arch-item">外部系统通知</span>
            </div>
          </div>
          <div class="arch-card">
            <div class="arch-layer">事件日志</div>
            <div class="arch-items">
              <span class="arch-item">全链路审计</span>
              <span class="arch-item">按类型筛选</span>
              <span class="arch-item">异常排查</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 价值视图 -->
      <template v-else-if="focus === 'value'">
        <div class="summary-icon">🚀</div>
        <h1 class="summary-title">价值总结</h1>
        <p class="summary-subtitle">三大模块协同 · 全链路自动化 · 效率提升 80%</p>
        <div class="value-grid">
          <div class="value-item" v-for="v in values" :key="v.label">
            <div class="value-number">{{ v.number }}</div>
            <div class="value-label">{{ v.label }}</div>
          </div>
        </div>
        <div class="value-cards">
          <div class="value-card" v-for="card in valueCards" :key="card.title">
            <span class="vc-icon">{{ card.icon }}</span>
            <span class="vc-title">{{ card.title }}</span>
            <span class="vc-desc">{{ card.desc }}</span>
          </div>
        </div>
      </template>

      <!-- 默认总结视图 -->
      <template v-else>
        <div class="summary-icon">🎉</div>
        <h1 class="summary-title">总结</h1>
        <p class="summary-subtitle">流程驱动的业务自动化平台</p>
        <div class="feature-grid">
          <div class="feature-card" v-for="feature in features" :key="feature.title">
            <div class="feature-icon">{{ feature.icon }}</div>
            <div class="feature-title">{{ feature.title }}</div>
            <div class="feature-desc">{{ feature.desc }}</div>
          </div>
        </div>
        <div class="tech-tags">
          <span class="tag" v-for="tag in tags" :key="tag">{{ tag }}</span>
        </div>
        <div class="footer-text">模块化设计 · 插件化扩展 · 高性能 · 易集成</div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const features = [
  { icon: '🎨', title: '可视化流程设计', desc: '拖拽式配置，零代码搭建审批链路' },
  { icon: '📝', title: '智能表单引擎', desc: '20+ 组件，AI 智能生成' },
  { icon: '✅', title: '灵活审批引擎', desc: '串行/并行/会签/或签' },
  { icon: '⚡', title: '自动化执行', desc: 'Mock/HTTP 双模式' },
  { icon: '🔗', title: '程序发起', desc: 'RESTful API 接入' },
  { icon: '📊', title: '数据看板', desc: '实时统计，效率一目了然' },
]

const modules = [
  { icon: '🔄', title: '流程引擎', desc: '可视化设计，支持串行/并行/条件分支' },
  { icon: '📝', title: '表单引擎', desc: '动态表单，AI 智能生成' },
  { icon: '✅', title: '审批引擎', desc: '会签/或签/条件审批' },
  { icon: '⚡', title: '能力平台', desc: 'Mock/HTTP 双模式执行' },
  { icon: '📡', title: '事件总线', desc: 'Webhook + 事件日志' },
  { icon: '📊', title: '数据看板', desc: '实时统计，效率分析' },
]

const values = [
  { number: '80%', label: '效率提升' },
  { number: '0', label: '代码配置' },
  { number: '100%', label: '全链路追踪' },
  { number: '24/7', label: '自动化执行' },
  { number: '3', label: '核心模块' },
  { number: '20+', label: '表单组件' },
]

const tags = ['Django 5', 'DRF', 'Vue 3', 'Element Plus', 'Celery', 'Redis']

const valueCards = [
  { icon: '⏱️', title: '上线提速', desc: '流程上线时间从数天缩短到分钟级' },
  { icon: '🎯', title: '零代码配置', desc: '业务人员无需开发即可搭建审批流程' },
  { icon: '🔄', title: '全链路追踪', desc: '从发起到执行，每一步都有迹可循' },
  { icon: '🔗', title: '开放集成', desc: 'RESTful API + Webhook，无缝对接现有系统' },
]
</script>

<style scoped lang="scss">
.summary-sim {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #409eff 0%, #764ba2 100%);
}
.summary-content { text-align: center; padding: 40px; }
.summary-icon { font-size: 48px; margin-bottom: 16px; }
.summary-title { font-size: 36px; font-weight: 700; color: #fff; margin: 0 0 8px; }
.summary-subtitle { font-size: 16px; color: rgba(255,255,255,0.8); margin: 0 0 32px; }

/* 架构视图 */
.arch-grid { display: flex; gap: 20px; justify-content: center; }
.arch-card {
  background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
  border-radius: 12px; padding: 24px; min-width: 180px; text-align: center;
}
.arch-layer { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 12px; }
.arch-items { display: flex; flex-direction: column; gap: 8px; }
.arch-item {
  padding: 6px 12px; background: rgba(255,255,255,0.2);
  border-radius: 6px; font-size: 13px; color: #fff;
}

/* 模块/功能视图 */
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px; }
.feature-card {
  background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
  border-radius: 12px; padding: 20px; text-align: center;
}
.feature-icon { font-size: 28px; margin-bottom: 8px; }
.feature-title { font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 4px; }
.feature-desc { font-size: 12px; color: rgba(255,255,255,0.7); }

/* 价值视图 */
.value-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 28px; }
.value-item { text-align: center; }
.value-number { font-size: 42px; font-weight: 700; color: #fff; }
.value-label { font-size: 13px; color: rgba(255,255,255,0.8); margin-top: 4px; }

.value-cards {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; max-width: 600px; margin: 0 auto;
}
.value-card {
  display: flex; flex-direction: column; align-items: flex-start; gap: 4px;
  background: rgba(255,255,255,0.12); backdrop-filter: blur(10px);
  border-radius: 10px; padding: 14px 18px; text-align: left;
}
.vc-icon { font-size: 20px; }
.vc-title { font-size: 14px; font-weight: 600; color: #fff; }
.vc-desc { font-size: 12px; color: rgba(255,255,255,0.75); line-height: 1.4; }

.tech-tags { display: flex; justify-content: center; gap: 8px; margin-bottom: 24px; }
.tag {
  padding: 6px 14px; background: rgba(255,255,255,0.2);
  border-radius: 20px; font-size: 12px; color: #fff; font-weight: 500;
}
.footer-text { font-size: 14px; color: rgba(255,255,255,0.6); }
</style>
