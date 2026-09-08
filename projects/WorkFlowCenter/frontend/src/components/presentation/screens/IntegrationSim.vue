<template>
  <div class="integration-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>🔗</span></div>
        <div>
          <h1>集成中心</h1>
          <p class="page-header-desc">管理 API 密钥、Webhook 订阅和外部系统对接</p>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-top">
          <span class="stat-label">{{ stat.label }}</span>
          <span class="stat-icon" :style="{ background: stat.bg }">{{ stat.icon }}</span>
        </div>
        <div class="stat-value">{{ stat.value }}</div>
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
        {{ tab.label }}
      </div>
    </div>

    <!-- API 密钥 -->
    <div v-if="activeTab === 'api'" class="content-card">
      <div class="table-header">
        <span class="table-title">API 密钥管理</span>
        <button class="btn-primary-sm">+ 创建密钥</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>密钥名称</th>
            <th>API Key</th>
            <th>关联程序</th>
            <th>状态</th>
            <th>最后调用</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in apiKeys" :key="row.name">
            <td><span class="link-text">{{ row.name }}</span></td>
            <td><code class="key-text">{{ row.key }}</code></td>
            <td>{{ row.program }}</td>
            <td><span class="status-tag status-active">{{ row.status }}</span></td>
            <td class="time-col">{{ row.lastCall }}</td>
            <td>
              <div class="action-group">
                <button class="link-btn">编辑</button>
                <button class="link-btn danger">禁用</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Webhook 订阅 -->
    <div v-if="activeTab === 'webhook'" class="content-card">
      <div class="table-header">
        <span class="table-title">Webhook 订阅</span>
        <button class="btn-primary-sm">+ 新建订阅</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>订阅名称</th>
            <th>回调 URL</th>
            <th>事件类型</th>
            <th>状态</th>
            <th>投递成功率</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in webhooks" :key="row.name">
            <td><span class="link-text">{{ row.name }}</span></td>
            <td><code class="url-text">{{ row.url }}</code></td>
            <td>
              <span class="event-tag" v-for="evt in row.events" :key="evt">{{ evt }}</span>
            </td>
            <td><span class="status-tag status-active">启用</span></td>
            <td>
              <div class="success-rate">
                <div class="rate-bar"><div class="rate-fill" :style="{ width: row.rate + '%' }"></div></div>
                <span>{{ row.rate }}%</span>
              </div>
            </td>
            <td>
              <div class="action-group">
                <button class="link-btn">测试</button>
                <button class="link-btn">日志</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 事件日志 -->
    <div v-if="activeTab === 'log'" class="content-card">
      <div class="table-header">
        <span class="table-title">事件日志</span>
        <div class="filter-inline">
          <span class="filter-tag active">全部</span>
          <span class="filter-tag">流程事件</span>
          <span class="filter-tag">任务事件</span>
          <span class="filter-tag">系统事件</span>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>事件类型</th>
            <th>事件来源</th>
            <th>描述</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in eventLogs" :key="row.time">
            <td class="time-col">{{ row.time }}</td>
            <td><span class="type-tag" :class="'type-' + row.typeClass">{{ row.type }}</span></td>
            <td>{{ row.source }}</td>
            <td>{{ row.desc }}</td>
            <td><span class="status-tag" :class="'status-' + row.statusClass">{{ row.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ focus?: string }>()

const activeTab = ref('api')

const tabs = [
  { key: 'api', label: 'API 密钥' },
  { key: 'webhook', label: 'Webhook 订阅' },
  { key: 'log', label: '事件日志' },
]

const stats = [
  { icon: '🔑', label: 'API 密钥', value: 4, bg: '#e6f7ff' },
  { icon: '🔗', label: 'Webhook 订阅', value: 6, bg: '#f0f9eb' },
  { icon: '📡', label: '今日事件', value: 128, bg: '#fdf6ec' },
  { icon: '✅', label: '投递成功率', value: '99.2%', bg: '#f0f9eb' },
]

const apiKeys = [
  { name: 'CMDB 同步', key: 'cmdb_sync_****a3f2', program: 'CMDB 资产同步', status: '启用', lastCall: '08-08 10:32' },
  { name: 'IT 服务台', key: 'itsm_prod_****b7e1', program: 'IT 服务台', status: '启用', lastCall: '08-08 09:15' },
  { name: '监控平台', key: 'monitor_dev_****c4d8', program: '监控告警处理', status: '已禁用', lastCall: '08-01 14:00' },
  { name: '测试密钥', key: 'test_key_****e9f5', program: '-', status: '启用', lastCall: '08-07 16:40' },
]

const webhooks = [
  { name: '工单状态通知', url: 'https://itsm.corp/api/webhook', events: ['流程完成', '流程挂起'], rate: 100 },
  { name: '审批提醒推送', url: 'https://notify.corp/api/push', events: ['待办创建'], rate: 98 },
  { name: 'CMDB 同步回调', url: 'https://cmdb.corp/api/callback', events: ['任务完成', '任务失败'], rate: 97 },
]

const eventLogs = [
  { time: '10:35:12', type: '流程完成', typeClass: 'flow', source: 'SRV-2026-001', desc: '服务器申请流程审批通过并自动执行完成', status: '成功', statusClass: 'active' },
  { time: '10:32:08', type: '任务执行', typeClass: 'task', source: 'CMDB 创建主机', desc: '能力执行成功，返回主机 ID: host-20260808-042', status: '成功', statusClass: 'active' },
  { time: '10:30:45', type: '待办创建', typeClass: 'task', source: 'NEW-2026-001', desc: '新增服务申请进入运维审批节点，分配给小李', status: '成功', statusClass: 'active' },
  { time: '10:28:33', type: 'Webhook 投递', typeClass: 'system', source: '工单状态通知', desc: '回调 https://itsm.corp/api/webhook 状态码 200', status: '成功', statusClass: 'active' },
  { time: '10:25:10', type: '流程发起', typeClass: 'flow', source: 'PUR-2026-003', desc: '小黄发起采购申请，进入财务审批节点', status: '成功', statusClass: 'active' },
]
</script>

<style scoped lang="scss">
.integration-page { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; display: flex; flex-direction: column; }

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

.stats-row { display: flex; gap: 12px; padding: 16px 24px 0; }
.stat-card {
  flex: 1; background: #fff; border-radius: 10px; padding: 14px 18px;
  border: 1px solid #f2f3f5;
}
.stat-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.stat-label { font-size: 12px; color: #86909c; }
.stat-icon { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.stat-value { font-size: 22px; font-weight: 700; color: #1d2129; }

.tabs-bar { display: flex; gap: 4px; padding: 12px 24px 0; }
.tab-item {
  padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 500;
  color: #86909c; cursor: pointer; transition: all 0.2s;
  &:hover { color: #1d2129; background: #fff; }
  &.active { color: #409eff; background: #fff; font-weight: 600; border: 1px solid #e5e6eb; }
}

.content-card {
  margin: 12px 24px 24px; background: #fff; border-radius: 10px;
  border: 1px solid #f2f3f5; overflow: hidden; flex: 1;
}
.table-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid #f2f3f5;
}
.table-title { font-size: 14px; font-weight: 600; color: #1d2129; }
.btn-primary-sm {
  padding: 6px 14px; background: #409eff; color: #fff; border: none;
  border-radius: 6px; font-size: 12px; cursor: pointer;
  &:hover { background: #337ecc; }
}

.filter-inline { display: flex; gap: 6px; }
.filter-tag {
  padding: 4px 10px; border-radius: 4px; font-size: 12px; color: #86909c;
  background: #f5f7fa; cursor: pointer;
  &.active { color: #409eff; background: #ecf5ff; }
}

.data-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
  th {
    padding: 10px 16px; text-align: left; font-weight: 600;
    color: #86909c; background: #fafafa; border-bottom: 1px solid #f2f3f5; font-size: 12px;
  }
  td { padding: 12px 16px; border-bottom: 1px solid #f7f8fa; color: #1d2129; }
  tr:hover td { background: #f7f9fc; }
}
.time-col { color: #c9cdd4; font-size: 12px; }
.link-text { color: #409eff; cursor: pointer; font-weight: 500; }
.key-text, .url-text {
  font-size: 12px; padding: 2px 8px; background: #f5f7fa; border-radius: 4px;
  color: #4e5969; font-family: monospace;
}
.action-group { display: flex; gap: 8px; }
.link-btn {
  background: none; border: none; color: #409eff; font-size: 12px; cursor: pointer;
  &:hover { color: #337ecc; }
  &.danger { color: #f56c6c; &:hover { color: #cf1322; } }
}

.status-tag {
  display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px;
  border-radius: 10px; font-size: 12px; font-weight: 500;
}
.status-active { background: #f0f9eb; color: #67c23a; }

.event-tag {
  display: inline-block; padding: 2px 8px; background: #f5f7fa;
  border-radius: 4px; font-size: 11px; color: #4e5969; margin-right: 4px;
}

.success-rate { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #67c23a; }
.rate-bar { width: 60px; height: 6px; background: #f2f3f5; border-radius: 3px; overflow: hidden; }
.rate-fill { height: 100%; background: #67c23a; border-radius: 3px; }

.type-tag {
  padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;
}
.type-flow { background: #ecf5ff; color: #409eff; }
.type-task { background: #fdf6ec; color: #e6a23c; }
.type-system { background: #f0f9eb; color: #67c23a; }
</style>
