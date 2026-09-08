<script setup lang="ts">
// 应用中心成本管理 + 预算工单闭环模拟
// 流程：环境成本 Tab → 申请增加预算 → 生成 apply_quota 工单 → 审批通过即生效
const appInfo = { name: '订单中心', org: '研发组', stack: 'Spring Boot 3.2', envs: 2, level: 'P0' }
const envCost = [
  { label: '本月成本', value: '¥20,316.93' },
  { label: '环比上月', value: '-14%', color: '#10b981' },
  { label: '预算使用率', value: '10.2%', color: '#7c3aed' },
  { label: '本月预算', value: '¥200,000' },
  { label: '费用记录', value: '70 条' },
]

const steps = [
  { icon: '💰', title: '环境成本 Tab', desc: '资源级费用明细 + 概览条，点击「📝 申请增加预算」', active: true },
  { icon: '📝', title: '生成预算申请工单', desc: 'apply_quota 工单：WO20260813-0007 · 申请 ¥30,000', active: true },
  { icon: '✅', title: '审批通过即生效', desc: '工单审批通过 → 预算更新 ¥200,000 → ¥230,000', active: false },
]

const ticket = {
  no: 'WO20260813-0007',
  type: '预算申请',
  app: '订单中心',
  amount: '¥30,000',
  status: '待审批',
  applicant: '只读用户',
  createdAt: '2026-08-13 10:24',
}
</script>

<template>
  <div class="app-cost-sim">
    <!-- 应用信息 -->
    <div class="app-header">
      <span class="app-icon">🛒</span>
      <div class="app-info">
        <div class="app-name">订单中心 <span class="level">P0</span></div>
        <div class="app-meta">{{ appInfo.org }} · {{ appInfo.stack }} · {{ appInfo.envs }} 个环境</div>
      </div>
      <div class="env-select">选择环境：<span class="env-pill">dev（开发）</span></div>
    </div>

    <!-- 环境成本概览 -->
    <div class="overview-bar">
      <div v-for="o in envCost" :key="o.label" class="ov-item">
        <div class="ov-label">{{ o.label }}</div>
        <div class="ov-value" :style="{ color: o.color || '#0f172a' }">{{ o.value }}</div>
      </div>
      <span class="btn-budget active">📝 申请增加预算</span>
    </div>

    <!-- 闭环流程 -->
    <div class="flow-card">
      <div class="flow-title">🔗 预算变更工单闭环</div>
      <div class="flow-steps">
        <div v-for="(s, i) in steps" :key="s.title" class="flow-step">
          <div class="flow-icon" :class="{ active: s.active }">{{ s.icon }}</div>
          <div class="flow-body">
            <div class="flow-name">{{ s.title }}</div>
            <div class="flow-desc">{{ s.desc }}</div>
          </div>
          <span v-if="i < steps.length - 1" class="flow-arrow">→</span>
        </div>
      </div>
    </div>

    <!-- 工单记录 -->
    <div class="table-card">
      <div class="card-header">
        <h3>🧾 工单中心 · 预算申请</h3>
        <span class="card-hint">预算走工单审批闭环，非直接改数据库</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>工单号</th><th>类型</th><th>应用</th><th>申请金额</th><th>申请人</th><th>创建时间</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr>
              <td class="mono">{{ ticket.no }}</td>
              <td><span class="type-tag">预算申请</span></td>
              <td>{{ ticket.app }}</td>
              <td class="amount">{{ ticket.amount }}</td>
              <td>{{ ticket.applicant }}</td>
              <td>{{ ticket.createdAt }}</td>
              <td><span class="status-tag">待审批</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-cost-sim { padding: 16px 20px; background: #f6f7fb; height: 100%; overflow-y: auto; }
.app-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #fff; border: 1px solid #eef0f4; border-radius: 10px; margin-bottom: 12px; }
.app-icon { font-size: 28px; }
.app-name { font-size: 16px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 8px; }
.level { padding: 1px 8px; background: #fef2f2; color: #dc2626; border-radius: 4px; font-size: 11px; }
.app-meta { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.env-select { margin-left: auto; font-size: 12px; color: #64748b; }
.env-pill { padding: 4px 12px; background: #ecfdf5; color: #059669; border-radius: 6px; font-weight: 600; font-size: 12px; }
.overview-bar { display: flex; align-items: center; gap: 26px; padding: 12px 16px; background: #fff; border: 1px solid #f0ecff; border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.ov-label { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
.ov-value { font-size: 17px; font-weight: 700; }
.btn-budget { margin-left: auto; padding: 7px 14px; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: #fff; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3); }
.flow-card { background: #fff; border: 1px solid #eef0f4; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.flow-title { font-size: 13px; font-weight: 600; color: #0f172a; margin-bottom: 12px; }
.flow-steps { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }
.flow-step { display: flex; align-items: flex-start; gap: 10px; flex: 1; min-width: 200px; position: relative; }
.flow-icon {
  width: 34px; height: 34px; border-radius: 8px;
  background: #f1f5f9; display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;
}
.flow-icon.active { background: #faf5ff; box-shadow: 0 0 0 1px #e9d5ff inset; }
.flow-name { font-size: 13px; font-weight: 600; color: #0f172a; }
.flow-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; line-height: 1.4; }
.flow-arrow { position: absolute; right: -4px; top: 10px; color: #cbd5e1; font-size: 16px; }
.table-card { background: #fff; border: 1px solid #eef0f4; border-radius: 10px; padding: 12px 14px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-header h3 { font-size: 13px; font-weight: 600; color: #0f172a; margin: 0; }
.card-hint { font-size: 11px; color: #94a3b8; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 8px 10px; color: #64748b; font-weight: 500; background: #f8fafc; border-bottom: 1px solid #eef0f4; }
td { padding: 8px 10px; border-bottom: 1px solid #f6f7fb; color: #334155; }
.mono { font-family: monospace; font-size: 11px; color: #64748b; }
.type-tag { padding: 2px 8px; background: #faf5ff; color: #7c3aed; border-radius: 4px; font-size: 11px; }
.amount { color: #059669; font-weight: 600; }
.status-tag { padding: 2px 8px; background: #fff7ed; color: #ea580c; border-radius: 4px; font-size: 11px; }
</style>
