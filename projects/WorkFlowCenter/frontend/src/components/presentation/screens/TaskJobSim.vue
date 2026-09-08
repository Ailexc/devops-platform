<template>
  <div class="task-job-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">📊</span>
        </div>
        <div>
          <h1>任务中心</h1>
          <p class="page-header-desc">管理定时任务和异步作业</p>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-card-top">
          <span class="stat-label">{{ stat.label }}</span>
          <div class="stat-icon" :class="stat.iconClass">{{ stat.icon }}</div>
        </div>
        <div class="stat-value">{{ stat.value }}</div>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>状态</label>
          <div class="el-select"><div class="el-input__inner">全部</div><span class="el-input__suffix">▼</span></div>
        </div>
        <div class="filter-actions">
          <button class="btn-primary btn-sm">🔍 查询</button>
          <button class="btn-default">重置</button>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table><thead><tr>
            <th><div class="cell">Job ID</div></th>
            <th><div class="cell">能力</div></th>
            <th><div class="cell">流程单号</div></th>
            <th><div class="cell">状态</div></th>
            <th><div class="cell">耗时</div></th>
            <th><div class="cell">创建时间</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in tableData" :key="row.job_id">
              <td><div class="cell"><span class="ticket-link">{{ row.job_id }}</span></div></td>
              <td><div class="cell"><span class="mode-tag">{{ row.capability }}</span></div></td>
              <td><div class="cell">{{ row.instance_no }}</div></td>
              <td><div class="cell"><span class="status-tag" :class="'status-tag--' + row.status"><span class="status-tag__dot"></span>{{ row.statusLabel }}</span></div></td>
              <td><div class="cell"><span class="time-text">{{ row.duration }}</span></div></td>
              <td><div class="cell"><span class="time-text">{{ row.created_at }}</span></div></td>
              <td><div class="cell action-group"><button class="link-btn">详情</button></div></td>
            </tr>
          </tbody></table>
        </div>
      </div>
      <div class="pagination-container">
        <span class="pagination-info">共 <strong>5</strong> 条</span>
        <div class="pagination">
          <button class="pagination-btn is-disabled">‹</button>
          <button class="pagination-btn is-active">1</button>
          <button class="pagination-btn is-disabled">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const stats = [
  { label: '执行总数', value: 28, icon: '📋', iconClass: 'stat-icon--default' },
  { label: '成功', value: 24, icon: '✅', iconClass: 'stat-icon--success' },
  { label: '执行中', value: 2, icon: '⏳', iconClass: 'stat-icon--warning' },
  { label: '失败', value: 2, icon: '❌', iconClass: 'stat-icon--danger' },
]

const tableData = [
  { job_id: 'job-20260808-001', capability: 'CMDB 创建主机', instance_no: 'SRV-2026-001', status: 'succeeded', statusLabel: '成功', duration: '1.2s', created_at: '2026-08-08 10:32' },
  { job_id: 'job-20260808-002', capability: 'DNS 解析配置', instance_no: 'SRV-2026-001', status: 'succeeded', statusLabel: '成功', duration: '0.8s', created_at: '2026-08-08 10:33' },
  { job_id: 'job-20260808-003', capability: '发送通知邮件', instance_no: 'SRV-2026-001', status: 'running', statusLabel: '执行中', duration: '-', created_at: '2026-08-08 10:34' },
  { job_id: 'job-20260807-001', capability: '防火墙规则', instance_no: 'PUR-2026-003', status: 'failed', statusLabel: '失败', duration: '5.0s', created_at: '2026-08-07 15:10' },
  { job_id: 'job-20260807-002', capability: 'CMDB 创建主机', instance_no: 'SRV-2026-002', status: 'succeeded', statusLabel: '成功', duration: '1.5s', created_at: '2026-08-07 14:22' },
]
</script>

<style scoped lang="scss">
.task-job-list { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px; }
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(64,158,255,0.1); display: flex; align-items: center; justify-content: center; }
.icon-symbol { font-size: 18px; }
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 20px 24px 0; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; }
.stat-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.stat-label { font-size: 14px; color: #86909c; }
.stat-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat-icon--default { background: rgba(144,147,153,0.1); color: #909399; }
.stat-icon--success { background: rgba(103,194,58,0.1); color: #67c23a; }
.stat-icon--warning { background: rgba(230,162,60,0.1); color: #e6a23c; }
.stat-icon--danger { background: rgba(245,108,108,0.1); color: #f56c6c; }
.stat-value { font-size: 28px; font-weight: 700; color: #1d2129; }

.filter-card { margin: 16px 24px 0; background: #fff; border-radius: 12px; padding: 16px 20px; }
.filter-row { display: flex; align-items: flex-end; gap: 16px; }
.filter-item { display: flex; flex-direction: column; gap: 6px; label { font-size: 13px; color: #4e5969; font-weight: 500; } }
.el-select, .el-input { display: flex; align-items: center; border: 1px solid #dcdfe6; border-radius: 6px; height: 32px; min-width: 160px; }
.el-input__inner { padding: 0 12px; font-size: 13px; color: #4e5969; flex: 1; }
.el-input__suffix { padding-right: 8px; font-size: 10px; color: #c0c4cc; }
.filter-actions { display: flex; gap: 8px; margin-left: auto; }
.btn-primary { padding: 6px 16px; background: #409eff; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; &:hover { background: #337ecc; } }
.btn-sm { padding: 6px 16px; font-size: 13px; }
.btn-default { padding: 6px 16px; background: #fff; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 13px; color: #606266; cursor: pointer; &:hover { border-color: #409eff; color: #409eff; } }

.table-card { margin: 16px 24px 24px; background: #fff; border-radius: 12px; padding: 20px; }
.el-table { width: 100%; border-collapse: collapse; th { background: #fafbfc; color: #86909c; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0; text-align: left; border-bottom: 1px solid #e5e6eb; } td { padding: 14px 0; border-bottom: 1px solid #f2f3f5; font-size: 14px; color: #4e5969; } .cell { padding: 0 12px; } }
.ticket-link { color: #409eff; cursor: pointer; &:hover { color: #337ecc; } }
.mode-tag { font-size: 12px; padding: 2px 8px; background: #f2f3f5; border-radius: 4px; color: #4e5969; }
.status-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; }
.status-tag--succeeded { background: #e8ffea; color: #00b42a; .status-tag__dot { background: #00b42a; } }
.status-tag--running { background: #fff7e8; color: #ff7d00; .status-tag__dot { background: #ff7d00; } }
.status-tag--failed { background: #ffece8; color: #f53f3f; .status-tag__dot { background: #f53f3f; } }
.time-text { font-size: 13px; color: #86909c; }
.action-group { display: flex; gap: 4px; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 6px; &:hover { color: #337ecc; } }

.pagination-container { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f2f3f5; }
.pagination-info { font-size: 13px; color: #86909c; strong { color: #4e5969; } }
.pagination { display: flex; gap: 4px; }
.pagination-btn { width: 32px; height: 32px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; font-size: 13px; color: #606266; cursor: pointer; display: flex; align-items: center; justify-content: center; &.is-active { background: #409eff; color: #fff; border-color: #409eff; } &.is-disabled { color: #c0c4cc; cursor: not-allowed; } }
</style>
