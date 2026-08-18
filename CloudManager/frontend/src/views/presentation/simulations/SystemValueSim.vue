<script setup lang="ts">
const values = [
  {
    icon: '🎯',
    title: '统一管控',
    desc: '多云资源统一视图，告别多控制台切换',
    metrics: '3个云平台 · 79个资源 · 1个入口',
  },
  {
    icon: '⚡',
    title: '效率提升',
    desc: '自动化工单审批，减少人工干预',
    metrics: '审批效率 ↑ 60% · 人工操作 ↓ 80%',
  },
  {
    icon: '🔒',
    title: '安全合规',
    desc: '所有操作留痕，权限精细化控制',
    metrics: '100% 操作审计 · RBAC 权限',
  },
  {
    icon: '💰',
    title: '成本优化',
    desc: '多维成本分析，智能优化建议',
    metrics: '月度费用 ↓ 8% · 资源利用率 ↑ 15%',
  },
  {
    icon: '📊',
    title: '数据驱动',
    desc: 'CMDB 唯一数据源，决策有据可依',
    metrics: '数据一致性 100% · 实时同步',
  },
  {
    icon: '🚀',
    title: '快速交付',
    desc: '标准化流程，资源申请分钟级交付',
    metrics: '交付时间 ↓ 70% · 自动化率 90%',
  },
]
</script>

<template>
  <div class="value-sim">
    <div class="value-card">
      <h3>🎯 系统价值</h3>
      <p class="subtitle">多云管理平台为企业带来的核心价值</p>
      
      <div class="value-grid">
        <div v-for="item in values" :key="item.title" class="value-item">
          <div class="value-icon">{{ item.icon }}</div>
          <div class="value-content">
            <div class="value-title">{{ item.title }}</div>
            <div class="value-desc">{{ item.desc }}</div>
            <div class="value-metrics">{{ item.metrics }}</div>
          </div>
        </div>
      </div>

      <div class="value-summary">
        <div class="summary-item">
          <span class="summary-value">3</span>
          <span class="summary-label">云平台统一管理</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">79</span>
          <span class="summary-label">资源统一纳管</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">60%</span>
          <span class="summary-label">效率提升</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">100%</span>
          <span class="summary-label">操作可追溯</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.value-sim {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  background: #f8fafc;
}

.value-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px 0;
  text-align: center;
}

.subtitle {
  font-size: 13px;
  color: #64748b;
  text-align: center;
  margin: 0 0 20px 0;
}

.value-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.value-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: #f8fafc;
  border-radius: 10px;
  transition: all 0.2s;
}

.value-item:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

.value-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.value-content {
  flex: 1;
}

.value-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.value-desc {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
  line-height: 1.4;
}

.value-metrics {
  font-size: 11px;
  color: #667eea;
  font-weight: 500;
}

.value-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.summary-item {
  text-align: center;
}

.summary-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #667eea;
}

.summary-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}
</style>
