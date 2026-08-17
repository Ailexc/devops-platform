<template>
  <div class="value-dashboard">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>🚀</span></div>
        <div>
          <h1>运营数据</h1>
          <p class="page-header-desc">平台核心价值与运行指标</p>
        </div>
      </div>
    </div>

    <!-- 核心指标 -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="kpi in kpis" :key="kpi.label" :style="{ borderTopColor: kpi.color }">
        <div class="kpi-top">
          <span class="kpi-label">{{ kpi.label }}</span>
          <span class="kpi-trend" :class="kpi.trend > 0 ? 'up' : 'down'">
            {{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }}%
          </span>
        </div>
        <div class="kpi-value" :style="{ color: kpi.color }">{{ kpi.value }}</div>
        <div class="kpi-desc">{{ kpi.desc }}</div>
      </div>
    </div>

    <!-- 三列布局 -->
    <div class="triple-row">
      <!-- 模块协同 -->
      <div class="triple-card">
        <div class="card-header">
          <span class="card-title">模块协同</span>
        </div>
        <div class="module-list">
          <div class="module-item" v-for="m in modules" :key="m.name">
            <div class="mi-left">
              <span class="mi-icon">{{ m.icon }}</span>
              <div>
                <div class="mi-name">{{ m.name }}</div>
                <div class="mi-role">{{ m.role }}</div>
              </div>
            </div>
            <div class="mi-stat">
              <span class="mi-value">{{ m.value }}</span>
              <span class="mi-unit">{{ m.unit }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 效率对比 -->
      <div class="triple-card">
        <div class="card-header">
          <span class="card-title">效率提升</span>
        </div>
        <div class="compare-list">
          <div class="compare-item" v-for="c in compares" :key="c.label">
            <div class="ci-label">{{ c.label }}</div>
            <div class="ci-bars">
              <div class="ci-row">
                <span class="ci-tag old">传统</span>
                <div class="ci-bar old" :style="{ width: c.oldWidth }">{{ c.old }}</div>
              </div>
              <div class="ci-row">
                <span class="ci-tag new">本平台</span>
                <div class="ci-bar new" :style="{ width: c.newWidth }">{{ c.new }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 核心优势 -->
      <div class="triple-card">
        <div class="card-header">
          <span class="card-title">核心优势</span>
        </div>
        <div class="advantage-list">
          <div class="adv-item" v-for="a in advantages" :key="a.title">
            <span class="adv-icon">{{ a.icon }}</span>
            <div>
              <div class="adv-title">{{ a.title }}</div>
              <div class="adv-desc">{{ a.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const kpis = [
  { label: '效率提升', value: '80%', color: '#409eff', trend: 12, desc: '对比传统审批流程' },
  { label: '流程上线', value: '分钟级', color: '#67c23a', trend: 35, desc: '从数天缩短到分钟级' },
  { label: '全链路追踪', value: '100%', color: '#e6a23c', trend: 0, desc: '每一步都有迹可循' },
  { label: '自动化执行', value: '24/7', color: '#909399', trend: 8, desc: '全天候自动处理' },
]

const modules = [
  { icon: '📋', name: '流程办理', role: '面向普通用户', value: '5', unit: '个子模块' },
  { icon: '⚙️', name: '流程配置', role: '面向管理员', value: '4', unit: '步向导' },
  { icon: '⚡', name: '任务平台', role: '面向自动化', value: '2', unit: '种执行模式' },
]

const compares = [
  { label: '流程上线周期', old: '3~5 天', new: '< 10 分钟', oldWidth: '80%', newWidth: '15%' },
  { label: '审批处理时间', old: '2~8 小时', new: '5~15 分钟', oldWidth: '70%', newWidth: '12%' },
  { label: '人工介入步骤', old: '5~10 步', new: '1 步', oldWidth: '75%', newWidth: '8%' },
]

const advantages = [
  { icon: '🎯', title: '零代码配置', desc: '业务人员无需开发，拖拽式搭建审批流程' },
  { icon: '🔗', title: '开放集成', desc: 'RESTful API + Webhook，无缝对接现有系统' },
  { icon: '📊', title: '全链路追踪', desc: '从发起到执行，每一步都有迹可循' },
  { icon: '🔒', title: '安全合规', desc: 'JWT 认证 + RBAC 权限 + 事件审计' },
]
</script>

<style scoped lang="scss">
.value-dashboard { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; display: flex; flex-direction: column; }

.page-header {
  display: flex; align-items: center; background: #fff;
  border-bottom: 1px solid #e5e6eb; padding: 14px 24px; flex-shrink: 0;
}
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header-icon {
  width: 36px; height: 36px; border-radius: 10px; background: #f0f9eb;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.page-header h1 { font-size: 17px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 12px; color: #86909c; margin: 1px 0 0; }

/* KPI 卡片 */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 16px 24px 0; }
.kpi-card {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  border: 1px solid #f2f3f5; border-top: 3px solid;
}
.kpi-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.kpi-label { font-size: 12px; color: #86909c; }
.kpi-trend { font-size: 11px; font-weight: 600;
  &.up { color: #67c23a; }
  &.down { color: #f56c6c; }
}
.kpi-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.kpi-desc { font-size: 11px; color: #c9cdd4; }

/* 三列布局 */
.triple-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 12px 24px 24px; flex: 1; }
.triple-card {
  background: #fff; border: 1px solid #f2f3f5; border-radius: 10px;
  display: flex; flex-direction: column; overflow: hidden;
}
.card-header {
  padding: 12px 16px; border-bottom: 1px solid #f2f3f5;
}
.card-title { font-size: 14px; font-weight: 600; color: #1d2129; }

/* 模块协同 */
.module-list { padding: 8px 16px; flex: 1; }
.module-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid #f7f8fa;
  &:last-child { border-bottom: none; }
}
.mi-left { display: flex; align-items: center; gap: 10px; }
.mi-icon { font-size: 20px; }
.mi-name { font-size: 13px; font-weight: 600; color: #1d2129; }
.mi-role { font-size: 11px; color: #86909c; }
.mi-stat { text-align: right; }
.mi-value { font-size: 18px; font-weight: 700; color: #409eff; }
.mi-unit { font-size: 11px; color: #86909c; margin-left: 2px; }

/* 效率对比 */
.compare-list { padding: 12px 16px; flex: 1; }
.compare-item { margin-bottom: 14px; &:last-child { margin-bottom: 0; } }
.ci-label { font-size: 12px; color: #4e5969; margin-bottom: 6px; font-weight: 500; }
.ci-bars { display: flex; flex-direction: column; gap: 4px; }
.ci-row { display: flex; align-items: center; gap: 6px; }
.ci-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 3px; width: 32px; text-align: center;
  &.old { background: #fef0f0; color: #f56c6c; }
  &.new { background: #f0f9eb; color: #67c23a; }
}
.ci-bar {
  font-size: 11px; padding: 3px 8px; border-radius: 4px; color: #fff; white-space: nowrap;
  &.old { background: #f56c6c; }
  &.new { background: #67c23a; }
}

/* 核心优势 */
.advantage-list { padding: 8px 16px; flex: 1; }
.adv-item {
  display: flex; gap: 10px; padding: 10px 0;
  border-bottom: 1px solid #f7f8fa;
  &:last-child { border-bottom: none; }
}
.adv-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.adv-title { font-size: 13px; font-weight: 600; color: #1d2129; margin-bottom: 2px; }
.adv-desc { font-size: 11px; color: #86909c; line-height: 1.4; }
</style>
