<template>
  <div class="mock-screen approval-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">审批流程</div>
      <div class="mock-user">⚙️ 系统自动</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">📋 审批流程</h2>

      <div class="flow-container">
        <div class="flow-step done" v-for="(s, i) in steps" :key="i">
          <div class="flow-icon">{{ s.icon }}</div>
          <div class="flow-info">
            <div class="flow-name">{{ s.name }}</div>
            <div class="flow-desc">{{ s.desc }}</div>
          </div>
          <div class="flow-status">
            <span class="status-ok" v-if="s.status === 'done'">✅ 已通过</span>
            <span class="status-wait" v-else-if="s.status === 'waiting'">⏳ 等待中</span>
            <span class="status-pending" v-else>⬜ 待处理</span>
          </div>
          <div v-if="i < steps.length - 1" class="flow-arrow">↓</div>
        </div>
      </div>

      <div class="result-banner success">
        <span class="result-icon">🎉</span>
        <span>审批通过！预设「只读监控」已上架到能力市场</span>
      </div>

      <div class="note-banner">
        <div class="note-title">💡 演示说明</div>
        <div class="note-text">在生产环境中，上架审批工单会推送至外部工单平台，由安全团队和平台管理员多级审批，审批结果自动回执并更新预设状态。此处为演示完整性，内置了简化的审批闭环。</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const steps = [
  { icon: '🚀', name: '上架申请', desc: '小黄提交预设上架申请', status: 'done' },
  { icon: '👤', name: 'Owner 确认', desc: '应用 Owner 小黄确认', status: 'done' },
  { icon: '🛡️', name: '平台复核', desc: '平台管理员 admin 审核', status: 'done' },
  { icon: '✅', name: '上架完成', desc: '预设状态变为 published', status: 'done' },
]
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px; }
.flow-container { max-width: 40%; margin: 0 auto; }
.flow-step { display: flex; align-items: center; gap: 14px; padding: 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px; position: relative; }
.flow-step.done { border-color: var(--success); background: var(--success-bg); }
.flow-icon { font-size: 24px; flex-shrink: 0; }
.flow-info { flex: 1; }
.flow-name { font-size: 14px; font-weight: 600; color: var(--text); }
.flow-desc { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.flow-status { flex-shrink: 0; }
.status-ok { font-size: 12px; font-weight: 600; color: var(--success); }
.status-wait { font-size: 12px; color: var(--warning); }
.status-pending { font-size: 12px; color: var(--text-tertiary); }
.flow-arrow { text-align: center; color: var(--text-tertiary); font-size: 16px; padding: 4px 0; }
.result-banner { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; margin-top: 20px; }
.result-banner.success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
.note-banner { margin-top: 14px; padding: 14px 18px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 10px; }
.note-title { font-size: 13px; font-weight: 600; color: var(--info); margin-bottom: 4px; }
.note-text { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
.result-icon { font-size: 20px; }
</style>
