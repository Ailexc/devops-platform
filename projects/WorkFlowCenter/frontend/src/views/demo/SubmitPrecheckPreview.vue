<template>
  <div class="precheck-preview">
    <!-- 头部 -->
    <div class="preview-header">
      <div>
        <h2>提单预检与流程预演（Demo）</h2>
        <p class="preview-sub">
          基于表单数据做「预检 + 审批路径计算 + DRY 模拟执行」，提单前发现问题，避免运行期报错打回
        </p>
      </div>
      <div class="scenario-switch">
        <span class="switch-label">切换场景：</span>
        <el-button
          v-for="s in scenarioList"
          :key="s.key"
          size="small"
          :type="scenario === s.key ? 'primary' : 'default'"
          @click="scenario = s.key"
        >
          {{ s.label }}
        </el-button>
        <el-button size="small" text @click="runPrecheck">
          <el-icon><RefreshRight /></el-icon>
          重新预检
        </el-button>
      </div>
    </div>

    <!-- 汇总横幅 -->
    <div
      v-if="summary"
      class="summary-banner"
      :class="'summary-banner--' + (summary.errors > 0 ? 'error' : summary.warnings > 0 ? 'warning' : 'ok')"
    >
      <el-icon class="summary-icon">
        <CircleCheckFilled v-if="summary.errors === 0 && summary.warnings === 0" />
        <WarningFilled v-else-if="summary.errors === 0" />
        <CircleCloseFilled v-else />
      </el-icon>
      <div class="summary-text">
        <span class="summary-title">
          {{
            summary.errors > 0
              ? `预检未通过（${summary.errors} 个错误）`
              : summary.warnings > 0
              ? `预检通过（有 ${summary.warnings} 个警告）`
              : '预检全部通过'
          }}
        </span>
        <span class="summary-desc">
          {{
            summary.errors > 0
              ? '存在错误项，提交将被拦截，请按下方建议修改后重新预检'
              : summary.warnings > 0
              ? '可提交，但建议关注下方警告项'
              : '表单数据与流程配置均正常，可放心提交'
          }}
        </span>
      </div>
      <div class="summary-stats">
        <span class="stat"><b>{{ summary.total }}</b> 检查项</span>
        <span class="stat stat--ok"><b>{{ summary.passed }}</b> 通过</span>
        <span class="stat stat--warn"><b>{{ summary.warnings }}</b> 警告</span>
        <span class="stat stat--err"><b>{{ summary.errors }}</b> 错误</span>
      </div>
    </div>

    <!-- 主体：表单 + 预检 -->
    <el-row :gutter="16" class="preview-body">
      <el-col :xs="24" :lg="9">
        <el-card class="pcard" shadow="never">
          <template #header>
            <div class="card-title">
              <span class="card-title__bar"></span>
              表单内容（提交回显）
            </div>
          </template>
          <div class="form-echo">
            <div class="form-echo__title">申请标题</div>
            <div class="form-echo__value">{{ current.title }}</div>
            <el-divider />
            <div
              v-for="f in formFields"
              :key="f.name"
              class="form-echo__row"
              :class="{ 'is-error': f.issue }"
            >
              <div class="form-echo__label">
                {{ f.label }}
                <el-tag v-if="f.issue" size="small" type="danger" effect="light">{{ f.issue }}</el-tag>
              </div>
              <div class="form-echo__value">{{ f.display }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="15">
        <!-- 预检结果 -->
        <el-card class="pcard" shadow="never">
          <template #header>
            <div class="card-title">
              <span class="card-title__bar"></span>
              提单预检
              <el-tooltip content="必填 / 类型 / 范围 / 枚举 / 条件联动 / 格式 / 路径可达" placement="top">
                <el-icon class="card-title__tip"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div v-if="!checks.length" v-loading="true" class="precheck-loading" />
          <template v-else>
            <div v-for="cat in checks" :key="cat.name" class="check-category">
              <div class="check-category__head">
                <span class="check-category__name">{{ cat.name }}</span>
                <el-tag
                  size="small"
                  :type="cat.passed ? 'success' : cat.hasError ? 'danger' : 'warning'"
                  effect="light"
                >
                  {{ cat.hasError ? '有问题' : cat.passed ? '通过' : '有风险' }}
                </el-tag>
              </div>
              <div class="check-item" v-for="c in cat.checks" :key="c.name">
                <el-icon class="check-item__icon" :class="'is-' + c.status">
                  <CircleCheckFilled v-if="c.status === 'passed'" />
                  <WarningFilled v-else-if="c.status === 'warning'" />
                  <CircleCloseFilled v-else />
                </el-icon>
                <div class="check-item__body">
                  <div class="check-item__name">{{ c.name }}</div>
                  <div class="check-item__message">{{ c.message }}</div>
                </div>
                <span class="check-item__tag" :class="'is-' + c.status">
                  {{ c.status === 'passed' ? '通过' : c.status === 'warning' ? '有风险' : '有问题' }}
                </span>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主体：路径 + DRY 执行 -->
    <el-row :gutter="16" class="preview-body">
      <el-col :xs="24" :lg="9">
        <el-card class="pcard" shadow="never">
          <template #header>
            <div class="card-title">
              <span class="card-title__bar"></span>
              审批路径预览
            </div>
          </template>
          <div class="flow-preview">
            <template v-for="(node, idx) in path" :key="node.key">
              <div class="preview-node" :class="'preview-node--' + node.type">
                <div class="preview-node__icon">
                  <el-icon :size="16"><component :is="nodeIcon(node.type)" /></el-icon>
                </div>
                <div class="preview-node__info">
                  <div class="preview-node__name">{{ node.name }}</div>
                  <div class="preview-node__meta">
                    <span class="preview-node__type">{{ node.type_label }}</span>
                    <span v-if="node.summary" class="preview-node__summary">{{ node.summary }}</span>
                  </div>
                </div>
              </div>
              <div v-if="idx < path.length - 1" class="preview-line"></div>
            </template>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="15">
        <!-- DRY 模拟执行 -->
        <el-card class="pcard" shadow="never">
          <template #header>
            <div class="card-title">
              <span class="card-title__bar"></span>
              DRY 模拟执行（Mock 能力 · 输入 / 输出 / 日志）
              <el-tag size="small" type="success" effect="light" class="dry-badge">DRY 模式 · 无副作用</el-tag>
            </div>
          </template>
          <div v-for="(action, i) in dryrun" :key="action.key" class="dry-task">
            <div class="dry-task__head">
              <span class="dry-task__seq">{{ i + 1 }}</span>
              <span class="dry-task__name">{{ action.name }}</span>
              <el-tag size="small" effect="plain">{{ action.capability }}</el-tag>
              <el-tag
                size="small"
                :type="action.status === 'success' ? 'success' : action.status === 'warning' ? 'warning' : 'danger'"
              >
                {{ action.statusText }}
              </el-tag>
            </div>
            <el-row :gutter="12" class="dry-task__body">
              <el-col :span="8">
                <div class="dry-block">
                  <div class="dry-block__title">输入（字段绑定）</div>
                  <div class="dry-block__kv" v-for="(v, k) in action.input" :key="k">
                    <span class="k">{{ k }}</span>
                    <span class="v">{{ v }}</span>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="dry-block">
                  <div class="dry-block__title">输出</div>
                  <div class="dry-block__kv" v-for="(v, k) in action.output" :key="k">
                    <span class="k">{{ k }}</span>
                    <span class="v">{{ v }}</span>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="dry-block">
                  <div class="dry-block__title">执行日志</div>
                  <div class="dry-log" v-for="(l, li) in action.logs" :key="li">
                    <span class="dry-log__time">{{ l.time }}</span>
                    <span class="dry-log__msg" :class="'is-' + l.level">{{ l.msg }}</span>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
          <el-empty v-if="!dryrun.length" description="无自动任务" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <div class="preview-foot">
      <span>说明：本页为演示原型（模拟数据，未接入真实后端）。「提单预检 + DRY 模拟执行」可落地为发起申请的第 4 步，后端负责权威校验。</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  CircleCheckFilled, CircleCloseFilled, WarningFilled, InfoFilled, RefreshRight
} from '@element-plus/icons-vue'

// 演示场景定义
const scenarios = {
  ok: {
    label: '正常提交',
    desc: '所有必填、范围、枚举、格式均正确',
  },
  invalid: {
    label: '越界 / 枚举错误',
    desc: '内存超上限、操作系统选了不存在的值',
  },
  missing: {
    label: '缺必填 / 联动缺失',
    desc: '未填主机名与邮箱、临时授权未填天数',
  },
}
const scenarioList = Object.entries(scenarios).map(([key, v]) => ({ key, label: v.label }))

// 场景数据（表单 + 预检 + 路径 + dry-run）
const data = {
  ok: {
    title: '生产服务器扩容申请',
    form: {
      hostname: 'web-prod-01', os: 'centos', cpu: 8, memory: 16, disk_size: 50,
      email: 'admin@company.com', reason: '业务扩容需要新增一台服务器',
    },
    checks: [
      {
        name: '必填校验', passed: true, hasError: false,
        checks: [
          { name: '主机名', status: 'passed', message: '已填写：web-prod-01' },
          { name: '操作系统', status: 'passed', message: '已选择' },
          { name: '通知邮箱', status: 'passed', message: '已填写' },
          { name: '申请理由', status: 'passed', message: '已填写' },
        ],
      },
      {
        name: '范围校验', passed: true, hasError: false,
        checks: [
          { name: 'CPU 核数', status: 'passed', message: '8 在允许范围 1-128 内' },
          { name: '内存 (GB)', status: 'passed', message: '16 在允许范围 1-512 内' },
        ],
      },
      {
        name: '枚举 / 类型校验', passed: true, hasError: false,
        checks: [
          { name: '操作系统', status: 'passed', message: 'centos 是合法选项' },
        ],
      },
      {
        name: '条件联动', passed: true, hasError: false,
        checks: [
          { name: '数据盘 / 可用区', status: 'passed', message: '无依赖约束冲突' },
        ],
      },
      {
        name: '格式校验', passed: true, hasError: false,
        checks: [{ name: '通知邮箱', status: 'passed', message: '邮箱格式正确' }],
      },
      {
        name: '路径可达', passed: true, hasError: false,
        checks: [{ name: '审批路径', status: 'passed', message: '已计算唯一审批路径（低配分支）' }],
      },
    ],
    path: [
      { key: 'start', name: '发起人', type: 'start', type_label: '发起', summary: '' },
      { key: 'ops', name: '运维审批', type: 'approve', type_label: '审批', summary: '小李' },
      { key: 'auto', name: '自动创建主机', type: 'handle', type_label: '办理', summary: '自动执行（串行，2 个动作）' },
      { key: 'end', name: '结束', type: 'end', type_label: '结束', summary: '' },
    ],
    dryrun: [
      {
        key: 'a1', name: '创建主机', capability: 'cmdb.create_host', status: 'success', statusText: '预检通过',
        input: { hostname: 'web-prod-01', cpu: 8, memory: 16, os: 'centos' },
        output: { host_id: 'host_8f2a', ip: '10.0.1.10', status: 'success' },
        logs: [
          { time: '10:00:01', level: 'info', msg: '校验输入参数 ... 通过' },
          { time: '10:00:02', level: 'info', msg: 'Mock 执行：创建主机 web-prod-01' },
          { time: '10:00:03', level: 'success', msg: '返回 host_id=host_8f2a' },
        ],
      },
      {
        key: 'a2', name: '发送创建通知', capability: 'mail.send', status: 'success', statusText: '预检通过',
        input: { to: 'admin@company.com', subject: '服务器创建完成通知' },
        output: { mail_id: 'mail_001', status: 'success' },
        logs: [
          { time: '10:00:04', level: 'info', msg: '校验收件人邮箱格式 ... 通过' },
          { time: '10:00:05', level: 'success', msg: '通知已发送（Mock）' },
        ],
      },
    ],
  },

  invalid: {
    title: '生产服务器扩容申请',
    form: {
      hostname: 'web-prod-01', os: 'centos8.9', cpu: 8, memory: 999, disk_size: 50,
      email: 'admin@company.com', reason: '业务扩容需要新增一台服务器',
    },
    checks: [
      {
        name: '必填校验', passed: true, hasError: false,
        checks: [
          { name: '主机名', status: 'passed', message: '已填写：web-prod-01' },
          { name: '操作系统', status: 'passed', message: '已选择' },
          { name: '通知邮箱', status: 'passed', message: '已填写' },
          { name: '申请理由', status: 'passed', message: '已填写' },
        ],
      },
      {
        name: '范围校验', passed: false, hasError: true,
        checks: [
          { name: 'CPU 核数', status: 'passed', message: '8 在允许范围 1-128 内' },
          { name: '内存 (GB)', status: 'error', message: '999 超出允许范围 1-512，建议调整后重新预检' },
        ],
      },
      {
        name: '枚举 / 类型校验', passed: false, hasError: true,
        checks: [
          { name: '操作系统', status: 'error', message: 'centos8.9 不在合法选项内（CentOS 7.9 / Ubuntu 22.04 / Debian 12 / Windows 2022）' },
        ],
      },
      {
        name: '条件联动', passed: true, hasError: false,
        checks: [{ name: '数据盘 / 可用区', status: 'passed', message: '无依赖约束冲突' }],
      },
      {
        name: '格式校验', passed: true, hasError: false,
        checks: [{ name: '通知邮箱', status: 'passed', message: '邮箱格式正确' }],
      },
      {
        name: '路径可达', passed: false, hasError: true,
        checks: [{ name: 'DRY 预演', status: 'error', message: '自动任务「创建主机」输入参数 memory=999 超出能力约束，执行存在风险' }],
      },
    ],
    path: [
      { key: 'start', name: '发起人', type: 'start', type_label: '发起', summary: '' },
      { key: 'ops', name: '运维审批', type: 'approve', type_label: '审批', summary: '小李' },
      { key: 'auto', name: '自动创建主机', type: 'handle', type_label: '办理', summary: '自动执行（串行，2 个动作）' },
      { key: 'end', name: '结束', type: 'end', type_label: '结束', summary: '' },
    ],
    dryrun: [
      {
        key: 'a1', name: '创建主机', capability: 'cmdb.create_host', status: 'error', statusText: '预检失败',
        input: { hostname: 'web-prod-01', cpu: 8, memory: 999, os: 'centos8.9' },
        output: {},
        logs: [
          { time: '10:00:01', level: 'info', msg: '校验输入参数 ...' },
          { time: '10:00:02', level: 'error', msg: 'memory=999 超出能力允许范围 1-512' },
          { time: '10:00:03', level: 'error', msg: 'os=centos8.9 不在能力枚举值内' },
        ],
      },
      {
        key: 'a2', name: '发送创建通知', capability: 'mail.send', status: 'warning', statusText: '待确认',
        input: { to: 'admin@company.com', subject: '服务器创建完成通知' },
        output: {},
        logs: [
          { time: '10:00:04', level: 'warn', msg: '前序动作失败，本动作跳过执行' },
        ],
      },
    ],
  },

  missing: {
    title: '生产服务器扩容申请',
    form: {
      hostname: '', os: 'centos', cpu: 8, memory: 16, disk_size: 50,
      email: '', reason: '', duration_type: 'temporary', duration_days: null,
    },
    checks: [
      {
        name: '必填校验', passed: false, hasError: true,
        checks: [
          { name: '主机名', status: 'error', message: '未填写，请补充主机名' },
          { name: '操作系统', status: 'passed', message: '已选择' },
          { name: '通知邮箱', status: 'error', message: '未填写，请补充通知邮箱' },
          { name: '申请理由', status: 'error', message: '未填写，请补充申请理由' },
        ],
      },
      {
        name: '范围校验', passed: true, hasError: false,
        checks: [
          { name: 'CPU 核数', status: 'passed', message: '8 在允许范围 1-128 内' },
          { name: '内存 (GB)', status: 'passed', message: '16 在允许范围 1-512 内' },
        ],
      },
      {
        name: '枚举 / 类型校验', passed: true, hasError: false,
        checks: [{ name: '操作系统', status: 'passed', message: 'centos 是合法选项' }],
      },
      {
        name: '条件联动', passed: false, hasError: true,
        checks: [
          { name: '临时授权天数', status: 'error', message: '有效期类型为「临时」，必须填写临时有效天数' },
        ],
      },
      {
        name: '格式校验', passed: false, hasError: true,
        checks: [{ name: '通知邮箱', status: 'error', message: '邮箱为空或格式不正确' }],
      },
      {
        name: '路径可达', passed: false, hasError: true,
        checks: [{ name: 'DRY 预演', status: 'error', message: '自动任务「创建主机」缺少必填参数 hostname，无法执行' }],
      },
    ],
    path: [
      { key: 'start', name: '发起人', type: 'start', type_label: '发起', summary: '' },
      { key: 'ops', name: '运维审批', type: 'approve', type_label: '审批', summary: '小李' },
      { key: 'auto', name: '自动创建主机', type: 'handle', type_label: '办理', summary: '自动执行（串行，2 个动作）' },
      { key: 'end', name: '结束', type: 'end', type_label: '结束', summary: '' },
    ],
    dryrun: [
      {
        key: 'a1', name: '创建主机', capability: 'cmdb.create_host', status: 'error', statusText: '预检失败',
        input: { hostname: '', cpu: 8, memory: 16, os: 'centos' },
        output: {},
        logs: [
          { time: '10:00:01', level: 'error', msg: '必填参数 hostname 为空' },
          { time: '10:00:02', level: 'error', msg: '执行中止' },
        ],
      },
      {
        key: 'a2', name: '发送创建通知', capability: 'mail.send', status: 'warning', statusText: '待确认',
        input: { to: '', subject: '服务器创建完成通知' },
        output: {},
        logs: [
          { time: '10:00:03', level: 'warn', msg: '收件人为空，且前序动作失败，跳过执行' },
        ],
      },
    ],
  },
}

const scenario = ref('ok')
const current = computed(() => data[scenario.value])
const summary = computed(() => {
  const checks = current.value.checks
  const all = checks.flatMap(c => c.checks)
  return {
    total: all.length,
    passed: all.filter(c => c.status === 'passed').length,
    warnings: all.filter(c => c.status === 'warning').length,
    errors: all.filter(c => c.status === 'error').length,
  }
})
const checks = computed(() => current.value.checks)
const path = computed(() => current.value.path)
const dryrun = computed(() => current.value.dryrun)
const form = computed(() => current.value.form)

// 表单字段展示（标注问题）
const formFields = computed(() => {
  const f = form.value
  const issueMap = {}
  summary.value // 触发
  current.value.checks.forEach(cat => {
    cat.checks.forEach(c => {
      if (c.status !== 'passed') issueMap[c.name] = c.status === 'error' ? '有问题' : '有风险'
    })
  })
  return [
    { name: 'hostname', label: '主机名', value: f.hostname, display: f.hostname || '（未填写）', issue: issueMap['主机名'] },
    { name: 'os', label: '操作系统', value: f.os, display: f.os || '（未选择）', issue: issueMap['操作系统'] },
    { name: 'cpu', label: 'CPU 核数', value: f.cpu, display: String(f.cpu ?? ''), issue: issueMap['CPU 核数'] },
    { name: 'memory', label: '内存 (GB)', value: f.memory, display: String(f.memory ?? ''), issue: issueMap['内存 (GB)'] },
    { name: 'disk_size', label: '系统盘 (GB)', value: f.disk_size, display: String(f.disk_size ?? ''), issue: '' },
    { name: 'email', label: '通知邮箱', value: f.email, display: f.email || '（未填写）', issue: issueMap['通知邮箱'] },
    { name: 'reason', label: '申请理由', value: f.reason, display: f.reason || '（未填写）', issue: issueMap['申请理由'] },
  ]
})

const nodeIconMap = {
  start: 'Promotion', approve: 'Checked', cc: 'ChatDotRound', handle: 'Setting', end: 'CircleCheckFilled',
}
const nodeIcon = (type) => nodeIconMap[type] || 'Document'

const runPrecheck = () => {
  // 演示：切换即"重新预检"，这里保持响应式即可
}
</script>

<style scoped lang="scss">
.precheck-preview {
  padding: 24px;
  background: #f7f8fa;
  min-height: 100vh;
  max-width: 1280px;
  margin: 0 auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;

  h2 { margin: 0 0 4px; font-size: 20px; color: #1d2129; }
  .preview-sub { margin: 0; font-size: 13px; color: #86909c; }
}

.scenario-switch {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  .switch-label { font-size: 13px; color: #4e5969; }
}

.summary-banner {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 18px;
  border-radius: 10px;
  margin-bottom: 16px;
  border: 1px solid;
  background: #fff;

  &--ok { border-color: #b7eb8f; background: #f0f9eb; }
  &--warning { border-color: #e6d4a8; background: #fdf6ec; }
  &--error { border-color: #f3c1c1; background: #fef0f0; }

  .summary-icon { font-size: 24px; }
  &--ok .summary-icon { color: #67c23a; }
  &--warning .summary-icon { color: #e6a23c; }
  &--error .summary-icon { color: #f56c6c; }

  .summary-text { flex: 1; min-width: 0; }
  .summary-title { display: block; font-size: 15px; font-weight: 600; color: #1d2129; }
  .summary-desc { display: block; font-size: 12px; color: #4e5969; margin-top: 2px; }

  .summary-stats { display: flex; gap: 14px; }
  .stat { font-size: 12px; color: #86909c; b { color: #1d2129; font-size: 15px; margin-right: 2px; } }
  .stat--ok b { color: #67c23a; }
  .stat--warn b { color: #e6a23c; }
  .stat--err b { color: #f56c6c; }
}

.preview-body {
  margin-bottom: 16px;
}

.pcard {
  border-radius: 12px;
  border: 1px solid #e5e6eb;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  :deep(.el-card__header) { padding: 12px 16px; }
  :deep(.el-card__body) { padding: 14px 16px; }
}

.card-title {
  display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: #1d2129;
  .card-title__bar { width: 3px; height: 14px; background: #409eff; border-radius: 2px; }
  .card-title__tip { color: #c9cdd4; cursor: help; }
}

.dry-badge { margin-left: auto; }

/* 表单回显 */
.form-echo {
  .form-echo__title { font-size: 13px; color: #86909c; }
  .form-echo__value { font-size: 14px; color: #1d2129; margin-top: 2px; font-weight: 500; }
  .form-echo__row {
    display: flex; justify-content: space-between; align-items: center; gap: 8px;
    padding: 6px 0;
    &.is-error .form-echo__value { color: #f56c6c; }
  }
  .form-echo__label { font-size: 13px; color: #4e5969; display: flex; align-items: center; gap: 6px; }
  .form-echo__value { font-size: 13px; color: #1d2129; }
}

/* 预检分类 */
.check-category {
  margin-bottom: 14px;
  &:last-child { margin-bottom: 0; }
  .check-category__head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 6px;
    .check-category__name { font-size: 13px; font-weight: 600; color: #1d2129; }
  }
}
.check-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 7px 10px; border-radius: 8px; margin-bottom: 4px;
  background: #fafafa;
  .check-item__icon { font-size: 16px; margin-top: 2px; }
  .is-passed { color: #67c23a; }
  .is-warning { color: #e6a23c; }
  .is-error { color: #f56c6c; }
  .check-item__body { flex: 1; min-width: 0; }
  .check-item__name { font-size: 13px; color: #1d2129; font-weight: 500; }
  .check-item__message { font-size: 12px; color: #86909c; margin-top: 1px; }
  .check-item__tag { font-size: 12px; flex-shrink: 0; padding: 1px 8px; border-radius: 10px; }
  .is-passed { color: #67c23a; background: #f0f9eb; }
  .is-warning { color: #e6a23c; background: #fdf6ec; }
  .is-error { color: #f56c6c; background: #fef0f0; }
}

/* 审批路径 */
.flow-preview {
  display: flex; flex-direction: column; align-items: center; padding: 4px 0;
}
.preview-node {
  display: flex; align-items: center; gap: 12px;
  width: 100%; max-width: 360px;
  padding: 10px 14px; border: 1px solid #e5e6eb; border-radius: 10px; background: #fff;
  .preview-node__icon {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: #ecf5ff; color: #409eff;
  }
  &--end .preview-node__icon { background: #f0f9eb; color: #67c23a; }
  &--approve .preview-node__icon { background: #fff7e6; color: #e6a23c; }
  &--handle .preview-node__icon { background: #f4f0ff; color: #722ed1; }
  .preview-node__info { flex: 1; min-width: 0; }
  .preview-node__name { font-size: 14px; font-weight: 600; color: #1d2129; }
  .preview-node__meta { display: flex; gap: 6px; font-size: 12px; margin-top: 2px; }
  .preview-node__type { color: #86909c; }
  .preview-node__summary { color: #86909c; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
.preview-line { width: 2px; height: 18px; background: linear-gradient(to bottom, #c9cdd4, #e5e6eb); }

/* DRY 任务 */
.dry-task {
  border: 1px solid #e5e6eb; border-radius: 10px; padding: 12px; margin-bottom: 12px;
  &:last-child { margin-bottom: 0; }
  .dry-task__head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
  .dry-task__seq {
    width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
    background: #409eff; color: #fff; font-size: 12px;
    display: flex; align-items: center; justify-content: center;
  }
  .dry-task__name { font-size: 14px; font-weight: 600; color: #1d2129; }
  .dry-task__body { margin-top: 4px; }
}
.dry-block {
  background: #fafafa; border-radius: 8px; padding: 8px 10px; height: 100%;
  .dry-block__title { font-size: 12px; color: #86909c; margin-bottom: 6px; }
  .dry-block__kv { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; padding: 2px 0; }
  .dry-block__kv .k { color: #86909c; }
  .dry-block__kv .v { color: #1d2129; font-weight: 500; word-break: break-all; text-align: right; }
}
.dry-log { font-size: 12px; line-height: 1.7; font-family: monospace; }
.dry-log__time { color: #c9cdd4; margin-right: 6px; }
.dry-log__msg { color: #4e5969; }
.dry-log__msg.is-error { color: #f56c6c; }
.dry-log__msg.is-warn { color: #e6a23c; }
.dry-log__msg.is-success { color: #67c23a; }

.precheck-loading { min-height: 120px; }

.preview-foot {
  margin-top: 4px; font-size: 12px; color: #86909c; text-align: center;
}

@media (max-width: 768px) {
  .preview-header { flex-direction: column; }
  .summary-stats { flex-wrap: wrap; }
}
</style>
