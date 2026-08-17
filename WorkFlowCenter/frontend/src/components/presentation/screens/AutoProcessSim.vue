<template>
  <div class="auto-process-sim">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>⚡</span></div>
        <div>
          <h1>自动办理配置</h1>
          <p class="page-header-desc">办理节点 · 程序代理自动通过</p>
        </div>
      </div>
    </div>

    <!-- 价值说明 -->
    <div class="value-banner">
      <div class="banner-icon">💡</div>
      <div class="banner-content">
        <div class="banner-title">什么是自动办理？</div>
        <div class="banner-desc">
          在办理节点允许<strong>程序代理</strong>代替人工自动完成审批/办理操作，无需等待人工介入，
          大幅缩短工单流转时间。适用于标准化、规则明确的场景（如资源开通、通知发送等）。
        </div>
      </div>
    </div>

    <!-- 对比展示 -->
    <div class="compare-section">
      <div class="compare-card before">
        <div class="card-badge">传统模式</div>
        <div class="card-title">人工逐级审批</div>
        <div class="flow-steps">
          <div class="step-item" v-for="(s, i) in manualSteps" :key="i">
            <div class="step-dot manual"></div>
            <div class="step-info">
              <div class="step-name">{{ s.name }}</div>
              <div class="step-time">{{ s.time }}</div>
            </div>
          </div>
        </div>
        <div class="card-total">平均耗时：<strong>4~8 小时</strong></div>
      </div>

      <div class="compare-arrow">→</div>

      <div class="compare-card after">
        <div class="card-badge green">自动办理</div>
        <div class="card-title">程序代理自动通过</div>
        <div class="flow-steps">
          <div class="step-item" v-for="(s, i) in autoSteps" :key="i">
            <div class="step-dot" :class="s.auto ? 'auto' : 'manual'"></div>
            <div class="step-info">
              <div class="step-name">{{ s.name }} <span v-if="s.auto" class="auto-tag">自动</span></div>
              <div class="step-time">{{ s.time }}</div>
            </div>
          </div>
        </div>
        <div class="card-total green">平均耗时：<strong>5~15 分钟</strong></div>
      </div>
    </div>

    <!-- 配置示例 -->
    <div class="config-section">
      <div class="section-title">配置示例：服务器申请流程</div>
      <table class="config-table">
        <thead>
          <tr>
            <th>办理节点</th>
            <th>绑定能力</th>
            <th>代理办理人</th>
            <th>自动通过条件</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in configExamples" :key="row.node">
            <td><span class="node-link">{{ row.node }}</span></td>
            <td><code class="cap-code">{{ row.capability }}</code></td>
            <td>{{ row.proxy }}</td>
            <td>{{ row.condition }}</td>
            <td><span class="status-tag" :class="'status-' + row.status">{{ row.statusLabel }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 执行记录 -->
    <div class="exec-section">
      <div class="section-title">最近自动执行记录</div>
      <div class="exec-list">
        <div class="exec-item" v-for="log in execLogs" :key="log.id">
          <div class="exec-left">
            <span class="exec-status-icon">{{ log.success ? '✅' : '❌' }}</span>
            <div>
              <div class="exec-title">{{ log.node }} → {{ log.capability }}</div>
              <div class="exec-meta">{{ log.instance }} · {{ log.time }}</div>
            </div>
          </div>
          <div class="exec-right">
            <span class="exec-duration">{{ log.duration }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const manualSteps = [
  { name: '发起申请', time: '10:00' },
  { name: '运维审批（人工）', time: '10:00 ~ 14:30' },
  { name: 'CMDB 开通（人工操作）', time: '14:30 ~ 15:00' },
  { name: 'DNS 配置（人工操作）', time: '15:00 ~ 15:30' },
  { name: '通知申请人', time: '15:30' },
]

const autoSteps = [
  { name: '发起申请', time: '10:00', auto: false },
  { name: '运维审批（人工）', time: '10:05', auto: false },
  { name: 'CMDB 开通（自动）', time: '10:05:02', auto: true },
  { name: 'DNS 配置（自动）', time: '10:05:03', auto: true },
  { name: '通知申请人（自动）', time: '10:05:04', auto: true },
]

const configExamples = [
  { node: 'CMDB 创建主机', capability: 'cmdb.create_host', proxy: '小李（审批人代理）', condition: '审批通过后自动执行', status: 'enabled', statusLabel: '已启用' },
  { node: 'DNS 解析配置', capability: 'dns.add_record', proxy: '小李（审批人代理）', condition: 'CMDB 创建成功后', status: 'enabled', statusLabel: '已启用' },
  { node: '发送通知邮件', capability: 'mail.send', proxy: '系统自动', condition: '所有节点完成后', status: 'enabled', statusLabel: '已启用' },
  { node: '防火墙规则', capability: 'fw.add_rule', proxy: '小李（审批人代理）', condition: '金额 > 10000 时', status: 'disabled', statusLabel: '未启用' },
]

const execLogs = [
  { id: 1, node: '自动开通', capability: 'CMDB 创建主机', instance: 'SRV-2026-001', time: '08-08 10:05', duration: '1.2s', success: true },
  { id: 2, node: 'DNS 配置', capability: 'DNS 添加记录', instance: 'SRV-2026-001', time: '08-08 10:05', duration: '0.8s', success: true },
  { id: 3, node: '发送通知', capability: '邮件发送', instance: 'SRV-2026-001', time: '08-08 10:05', duration: '0.5s', success: true },
  { id: 4, node: '自动开通', capability: 'CMDB 创建主机', instance: 'SRV-2026-002', time: '08-07 14:30', duration: '1.5s', success: true },
]
</script>

<style scoped lang="scss">
.auto-process-sim { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }

.page-header {
  display: flex; align-items: center; background: #fff;
  border-bottom: 1px solid #e5e6eb; padding: 14px 24px; flex-shrink: 0;
}
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header-icon {
  width: 36px; height: 36px; border-radius: 10px; background: #fdf6ec;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.page-header h1 { font-size: 17px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 12px; color: #86909c; margin: 1px 0 0; }

/* 价值说明 */
.value-banner {
  display: flex; gap: 12px; margin: 16px 24px 0; padding: 14px 18px;
  background: #ecf5ff; border: 1px solid #b3d8ff; border-radius: 10px;
}
.banner-icon { font-size: 24px; flex-shrink: 0; }
.banner-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.banner-desc { font-size: 12px; color: #4e5969; line-height: 1.6; }
.banner-desc strong { color: #409eff; }

/* 对比展示 */
.compare-section {
  display: flex; align-items: stretch; gap: 12px; padding: 16px 24px 0;
}
.compare-card {
  flex: 1; background: #fff; border: 1px solid #f2f3f5; border-radius: 10px; padding: 16px;
}
.compare-card.before { border-top: 3px solid #f56c6c; }
.compare-card.after { border-top: 3px solid #67c23a; }
.card-badge {
  display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px;
  background: #fef0f0; color: #f56c6c; font-weight: 500; margin-bottom: 8px;
  &.green { background: #f0f9eb; color: #67c23a; }
}
.card-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }
.compare-arrow { display: flex; align-items: center; font-size: 24px; color: #c9cdd4; }

.flow-steps { margin-bottom: 12px; }
.step-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; }
.step-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.step-dot.manual { background: #dcdfe6; }
.step-dot.auto { background: #67c23a; }
.step-name { font-size: 13px; color: #1d2129; }
.auto-tag { font-size: 10px; padding: 1px 6px; background: #f0f9eb; color: #67c23a; border-radius: 3px; margin-left: 4px; }
.step-time { font-size: 11px; color: #c0c4cc; }
.card-total { font-size: 13px; color: #86909c; padding-top: 8px; border-top: 1px solid #f2f3f5;
  strong { color: #1d2129; font-size: 15px; }
  &.green strong { color: #67c23a; }
}

/* 配置示例 */
.config-section, .exec-section { padding: 0 24px; margin-top: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 10px; }
.config-table {
  width: 100%; border-collapse: collapse; font-size: 13px; background: #fff;
  border-radius: 10px; overflow: hidden; border: 1px solid #f2f3f5;
  th { padding: 10px 14px; text-align: left; font-weight: 600; color: #86909c; background: #fafafa; font-size: 12px; }
  td { padding: 12px 14px; border-bottom: 1px solid #f7f8fa; color: #1d2129; }
}
.node-link { color: #409eff; cursor: pointer; font-weight: 500; }
.cap-code { font-size: 12px; padding: 2px 8px; background: #f5f7fa; border-radius: 4px; font-family: monospace; }
.status-tag { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.status-enabled { background: #f0f9eb; color: #67c23a; }
.status-disabled { background: #f5f7fa; color: #c0c4cc; }

/* 执行记录 */
.exec-list { background: #fff; border: 1px solid #f2f3f5; border-radius: 10px; overflow: hidden; }
.exec-item {
  display: flex; justify-content: space-between; align-items: center; padding: 12px 16px;
  border-bottom: 1px solid #f7f8fa; &:last-child { border-bottom: none; }
}
.exec-left { display: flex; align-items: center; gap: 10px; }
.exec-status-icon { font-size: 16px; }
.exec-title { font-size: 13px; font-weight: 500; color: #1d2129; }
.exec-meta { font-size: 11px; color: #c0cdd4; margin-top: 2px; }
.exec-duration { font-size: 12px; color: #86909c; font-family: monospace; }
</style>
