<template>
  <div class="process-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>📋</span></div>
        <div>
          <h1>流程办理</h1>
          <p class="page-header-desc">发起申请 · 追踪状态 · 审批处理</p>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs-bar">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <!-- 发起申请 -->
    <div v-if="activeTab === 'apply'" class="tab-content">
      <div class="steps-bar">
        <div class="step active">
          <div class="step__number">1</div>
          <span class="step__label">选择流程</span>
        </div>
        <div class="step__line"></div>
        <div class="step">
          <div class="step__number">2</div>
          <span class="step__label">填写表单</span>
        </div>
        <div class="step__line"></div>
        <div class="step">
          <div class="step__number">3</div>
          <span class="step__label">提交</span>
        </div>
      </div>
      <div class="content-card">
        <div class="content-card-header">
          <span class="content-card-bar"></span>
          <span class="content-card-title">选择流程模版</span>
        </div>
        <div class="content-card-body">
          <div class="flow-grid">
            <div v-for="flow in flowDefinitions" :key="flow.key" class="flow-card">
              <div class="flow-icon">{{ flow.icon }}</div>
              <div class="flow-info">
                <div class="flow-name">{{ flow.name }}</div>
                <div class="flow-desc">{{ flow.desc }}</div>
              </div>
              <div class="flow-meta">
                <span class="flow-category">{{ flow.category }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 我的申请 -->
    <div v-if="activeTab === 'my'" class="tab-content">
      <div class="stats-row">
        <div v-for="stat in myStats" :key="stat.label" class="stat-mini">
          <span class="stat-mini-icon" :style="{ color: stat.color }">{{ stat.icon }}</span>
          <span class="stat-mini-value">{{ stat.value }}</span>
          <span class="stat-mini-label">{{ stat.label }}</span>
        </div>
      </div>
      <div class="content-card">
        <div class="content-card-header">
          <span class="content-card-bar"></span>
          <span class="content-card-title">申请列表</span>
        </div>
        <div class="content-card-body no-padding">
          <table class="mini-table">
            <thead>
              <tr>
                <th>单号</th>
                <th>流程</th>
                <th>标题</th>
                <th>状态</th>
                <th>当前节点</th>
                <th>发起时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in myApplications" :key="row.no">
                <td><span class="link-text">{{ row.no }}</span></td>
                <td>{{ row.flow }}</td>
                <td>{{ row.title }}</td>
                <td><span class="status-tag" :class="'status-' + row.status">{{ row.statusLabel }}</span></td>
                <td>{{ row.node }}</td>
                <td class="time-col">{{ row.time }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 待办审批 -->
    <div v-if="activeTab === 'todo'" class="tab-content">
      <div class="stats-row">
        <div v-for="stat in todoStats" :key="stat.label" class="stat-mini">
          <span class="stat-mini-icon" :style="{ color: stat.color }">{{ stat.icon }}</span>
          <span class="stat-mini-value">{{ stat.value }}</span>
          <span class="stat-mini-label">{{ stat.label }}</span>
        </div>
      </div>
      <div class="content-card">
        <div class="content-card-header">
          <span class="content-card-bar"></span>
          <span class="content-card-title">待办任务</span>
        </div>
        <div class="content-card-body no-padding">
          <table class="mini-table">
            <thead>
              <tr>
                <th>申请标题</th>
                <th>节点</th>
                <th>类型</th>
                <th>发起人</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in todoList" :key="row.title">
                <td><span class="link-text">{{ row.title }}</span></td>
                <td>{{ row.node }}</td>
                <td>{{ row.type }}</td>
                <td>{{ row.applicant }}</td>
                <td class="time-col">{{ row.time }}</td>
                <td><button class="btn-action">办理</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ focus?: string }>()

const activeTab = ref('apply')

const tabs = [
  { key: 'apply', icon: '📝', label: '发起申请' },
  { key: 'my', icon: '📄', label: '我的申请' },
  { key: 'todo', icon: '✅', label: '待办审批' },
]

const flowDefinitions = [
  { icon: '🖥️', name: '服务器申请', desc: '申请云服务器资源', category: 'IT 运维', key: 'server_apply' },
  { icon: '🆕', name: '新增服务', desc: '申请新增业务服务', category: 'IT 运维', key: 'new_service' },
  { icon: '🔄', name: '服务器重启', desc: '程序自动触发重启', category: 'IT 运维', key: 'server_restart' },
  { icon: '🛒', name: '采购申请', desc: '设备及物资采购审批', category: '行政', key: 'purchase' },
  { icon: '🏖️', name: '请假申请', desc: '员工请假审批', category: '人事', key: 'leave' },
  { icon: '💰', name: '报销申请', desc: '费用报销审批', category: '财务', key: 'expense' },
]

const myStats = [
  { icon: '📊', label: '全部', value: 12, color: '#909399' },
  { icon: '⏳', label: '运行中', value: 3, color: '#e6a23c' },
  { icon: '⏸️', label: '已挂起', value: 1, color: '#f56c6c' },
  { icon: '✅', label: '已完成', value: 8, color: '#67c23a' },
]

const myApplications = [
  { no: 'SRV-2026-001', flow: '服务器申请', title: '申请测试服务器', status: 'running', statusLabel: '运行中', node: '运维审批', time: '08-08 10:00' },
  { no: 'SRV-2026-002', flow: '服务器申请', title: '申请生产服务器', status: 'done', statusLabel: '已完成', node: '-', time: '08-07 14:30' },
  { no: 'PUR-2026-001', flow: '采购申请', title: '采购开发笔记本', status: 'done', statusLabel: '已完成', node: '-', time: '08-05 09:00' },
  { no: 'SRV-2026-003', flow: '服务器申请', title: '申请预发布环境', status: 'running', statusLabel: '运行中', node: '自动办理', time: '08-06 16:20' },
  { no: 'LVE-2026-001', flow: '请假申请', title: '年假申请 3 天', status: 'suspended', statusLabel: '已挂起', node: '部门主管', time: '08-04 11:00' },
]

const todoStats = [
  { icon: '📋', label: '全部待办', value: 5, color: '#409eff' },
  { icon: '👤', label: '我的审批', value: 3, color: '#e6a23c' },
  { icon: '👥', label: '我的办理', value: 2, color: '#67c23a' },
]

const todoList = [
  { title: 'SRV-2026-001 申请测试服务器', node: '运维审批', type: '审批', applicant: '小明', time: '08-08 10:00' },
  { title: 'NEW-2026-001 申请新增服务', node: '部门主管', type: '审批', applicant: '小红', time: '08-08 09:30' },
  { title: 'PUR-2026-002 采购交换机', node: '财务审批', type: '审批', applicant: '小黄', time: '08-07 15:00' },
  { title: 'SRV-2026-003 申请预发布环境', node: 'CMDB 创建主机', type: '办理', applicant: '小明', time: '08-06 16:20' },
  { title: 'SRV-2026-004 申请测试环境', node: 'DNS 配置', type: '办理', applicant: '小李', time: '08-06 11:00' },
]
</script>

<style scoped lang="scss">
.process-overview {
  width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; display: flex; flex-direction: column;
}

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

/* 标签页 */
.tabs-bar {
  display: flex; gap: 4px; padding: 12px 24px 0; flex-shrink: 0;
}
.tab-item {
  display: flex; align-items: center; gap: 6px; padding: 10px 20px;
  border-radius: 8px 8px 0 0; cursor: pointer; font-size: 13px; font-weight: 500;
  color: #86909c; background: transparent; transition: all 0.2s;
  border: 1px solid transparent; border-bottom: none;
  &:hover { color: #1d2129; background: #fff; }
  &.active {
    color: #409eff; background: #fff; font-weight: 600;
    border-color: #e5e6eb;
  }
}
.tab-icon { font-size: 14px; }

/* 统计行 */
.stats-row {
  display: flex; gap: 12px; padding: 16px 24px 0;
}
.stat-mini {
  flex: 1; display: flex; align-items: center; gap: 8px;
  background: #fff; border-radius: 8px; padding: 12px 16px;
  border: 1px solid #f2f3f5;
}
.stat-mini-icon { font-size: 18px; }
.stat-mini-value { font-size: 20px; font-weight: 700; color: #1d2129; }
.stat-mini-label { font-size: 12px; color: #86909c; }

/* 内容卡片 */
.content-card {
  margin: 12px 24px 24px; background: #fff; border-radius: 10px;
  border: 1px solid #f2f3f5; overflow: hidden; flex: 1;
}
.content-card-header {
  padding: 14px 20px; border-bottom: 1px solid #f2f3f5;
  display: flex; align-items: center; gap: 8px;
}
.content-card-bar { display: inline-block; width: 3px; height: 14px; background: #409eff; border-radius: 2px; }
.content-card-title { font-size: 14px; font-weight: 600; color: #1d2129; }
.content-card-body { padding: 20px; }
.content-card-body.no-padding { padding: 0; }

/* 流程选择网格 */
.flow-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.flow-card {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  border: 1px solid #e5e6eb; border-radius: 10px; cursor: pointer;
  transition: all 0.2s; &:hover { border-color: #409eff; background: #f0f7ff; }
}
.flow-icon { font-size: 28px; }
.flow-info { flex: 1; }
.flow-name { font-size: 13px; font-weight: 600; color: #1d2129; }
.flow-desc { font-size: 11px; color: #86909c; margin-top: 2px; }
.flow-category {
  font-size: 11px; padding: 2px 8px; background: #f2f3f5;
  border-radius: 4px; color: #86909c; white-space: nowrap;
}

/* 步骤条 */
.steps-bar { display: flex; align-items: center; justify-content: center; padding: 16px 40px 0; }
.step { display: flex; align-items: center; gap: 6px; }
.step.active .step__number { background: #409eff; color: #fff; border-color: #409eff; }
.step__number {
  width: 24px; height: 24px; border-radius: 50%; border: 2px solid #dcdfe6;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #c0c4cc;
}
.step__label { font-size: 13px; color: #4e5969; }
.step__line { width: 60px; height: 2px; background: #e5e6eb; margin: 0 12px; }

/* 表格 */
.mini-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
  th {
    padding: 10px 16px; text-align: left; font-weight: 600;
    color: #86909c; background: #fafafa; border-bottom: 1px solid #f2f3f5;
    font-size: 12px;
  }
  td {
    padding: 12px 16px; border-bottom: 1px solid #f7f8fa; color: #1d2129;
  }
  tr:hover td { background: #f7f9fc; }
}
.time-col { color: #c9cdd4; font-size: 12px; }
.link-text { color: #409eff; cursor: pointer; font-weight: 500; }
.btn-action {
  padding: 4px 12px; border-radius: 6px; border: 1px solid #e6a23c;
  background: #fdf6ec; color: #e6a23c; font-size: 12px; cursor: pointer;
  &:hover { background: #faecd8; }
}

/* 状态标签 */
.status-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500;
}
.status-tag::before {
  content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%;
}
.status-running { background: #fdf6ec; color: #e6a23c; &::before { background: #e6a23c; } }
.status-done { background: #f0f9eb; color: #67c23a; &::before { background: #67c23a; } }
.status-suspended { background: #fef0f0; color: #f56c6c; &::before { background: #f56c6c; } }
</style>
