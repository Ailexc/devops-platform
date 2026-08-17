<template>
  <div class="demo-summary">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>🎉</span></div>
        <div>
          <h1>演示完成</h1>
          <p class="page-header-desc">IT 运维自动化 · 端到端流程回顾</p>
        </div>
      </div>
    </div>

    <!-- 流程回顾 -->
    <div class="timeline-section">
      <div class="section-title">流程回顾</div>
      <div class="timeline">
        <div class="tl-item" v-for="(step, i) in timelineSteps" :key="i" :class="{ completed: step.done }">
          <div class="tl-left">
            <div class="tl-dot" :style="{ background: step.done ? '#67c23a' : '#dcdfe6' }">
              <span v-if="step.done">✓</span>
            </div>
            <div class="tl-line" v-if="i < timelineSteps.length - 1"></div>
          </div>
          <div class="tl-card">
            <div class="tl-header">
              <span class="tl-role">{{ step.role }}</span>
              <span class="tl-time">{{ step.time }}</span>
            </div>
            <div class="tl-title">{{ step.title }}</div>
            <div class="tl-desc">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 效率对比 -->
    <div class="compare-section">
      <div class="section-title">效率对比</div>
      <div class="compare-row">
        <div class="compare-card">
          <div class="cc-label">传统模式</div>
          <div class="cc-steps">
            <div class="cc-step" v-for="s in manualSteps" :key="s">{{ s }}</div>
          </div>
          <div class="cc-time">⏱️ 4~8 小时</div>
        </div>
        <div class="compare-arrow">→</div>
        <div class="compare-card green">
          <div class="cc-label">本平台</div>
          <div class="cc-steps">
            <div class="cc-step" v-for="s in autoSteps" :key="s">{{ s }}</div>
          </div>
          <div class="cc-time">⏱️ 5~15 分钟</div>
        </div>
      </div>
    </div>

    <!-- 关键数据 -->
    <div class="stats-section">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="sc-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="sc-label">{{ s.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const timelineSteps = [
  { role: '👤 小明（研发）', title: '发起申请', desc: '选择"服务器申请"流程，填写主机名、CPU、内存、操作系统', time: '10:00', done: true },
  { role: '📋 系统', title: '流程流转', desc: '提交后自动进入审批链路，通知运维审批人', time: '10:00', done: true },
  { role: '👤 小李（运维）', title: '审批通过', desc: '查看申请详情，确认资源充足，填写审批意见后通过', time: '10:05', done: true },
  { role: '⚡ 系统', title: '自动开通', desc: '自动调用 CMDB 创建主机、配置 DNS、发送通知邮件', time: '10:05:02', done: true },
  { role: '📊 系统', title: '事件记录', desc: '全链路事件写入日志，支持事后审计与排查', time: '10:05:03', done: true },
]

const manualSteps = ['发起申请', '人工审批', '人工创建主机', '人工配置 DNS', '人工通知']
const autoSteps = ['发起申请', '人工审批', '自动创建主机', '自动配置 DNS', '自动通知']

const stats = [
  { label: '人工步骤', value: '1 步', color: '#409eff' },
  { label: '总耗时', value: '5 min', color: '#67c23a' },
  { label: '自动执行', value: '3 项', color: '#e6a23c' },
  { label: '效率提升', value: '80%', color: '#f56c6c' },
]
</script>

<style scoped lang="scss">
.demo-summary { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }

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

.section-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }

/* 时间线 */
.timeline-section { padding: 16px 24px; }
.timeline { padding-left: 0; }
.tl-item { display: flex; gap: 12px; position: relative; }
.tl-left { display: flex; flex-direction: column; align-items: center; width: 24px; flex-shrink: 0; }
.tl-dot {
  width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 12px; color: #fff; font-weight: 600; z-index: 1; flex-shrink: 0;
}
.tl-line { width: 2px; flex: 1; background: #e5e6eb; margin: 4px 0; }
.tl-item.completed .tl-line { background: #67c23a; }
.tl-card {
  flex: 1; background: #fff; border: 1px solid #f2f3f5; border-radius: 8px;
  padding: 10px 14px; margin-bottom: 8px;
}
.tl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.tl-role { font-size: 11px; color: #86909c; }
.tl-time { font-size: 11px; color: #c0c4cc; font-family: monospace; }
.tl-title { font-size: 13px; font-weight: 600; color: #1d2129; }
.tl-desc { font-size: 12px; color: #86909c; margin-top: 2px; }

/* 对比 */
.compare-section { padding: 0 24px; }
.compare-row { display: flex; align-items: stretch; gap: 12px; }
.compare-card {
  flex: 1; background: #fff; border: 1px solid #f2f3f5; border-radius: 10px; padding: 14px;
  border-top: 3px solid #f56c6c;
  &.green { border-top-color: #67c23a; }
}
.cc-label { font-size: 12px; font-weight: 600; color: #86909c; margin-bottom: 8px; }
.cc-steps { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.cc-step { font-size: 12px; color: #4e5969; padding: 4px 8px; background: #f5f7fa; border-radius: 4px; }
.compare-card.green .cc-step { background: #f0f9eb; }
.cc-time { font-size: 13px; font-weight: 600; color: #1d2129; padding-top: 8px; border-top: 1px solid #f2f3f5; }
.compare-arrow { display: flex; align-items: center; font-size: 20px; color: #c9cdd4; }

/* 统计 */
.stats-section { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 16px 24px 24px; }
.stat-card {
  background: #fff; border: 1px solid #f2f3f5; border-radius: 10px;
  padding: 14px; text-align: center;
}
.sc-value { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.sc-label { font-size: 12px; color: #86909c; }
</style>
