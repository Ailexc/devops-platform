<template>
  <div class="event-log-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">📋</span>
        </div>
        <div>
          <h1>事件日志</h1>
          <p class="page-header-desc">查看系统事件和操作日志</p>
        </div>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>事件类型</label>
          <div class="el-select" style="width:220px"><div class="el-input__inner">全部</div><span class="el-input__suffix">▼</span></div>
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
            <th><div class="cell">事件类型</div></th>
            <th><div class="cell">流程单号</div></th>
            <th><div class="cell">任务</div></th>
            <th><div class="cell">工单</div></th>
            <th><div class="cell">时间</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in tableData" :key="row.type + row.time">
              <td><div class="cell"><span class="event-tag">{{ row.type }}</span></div></td>
              <td><div class="cell">{{ row.instance_no }}</div></td>
              <td><div class="cell"><span class="desc-text">{{ row.task }}</span></div></td>
              <td><div class="cell"><span class="desc-text">{{ row.ticket }}</span></div></td>
              <td><div class="cell"><span class="time-text">{{ row.time }}</span></div></td>
              <td><div class="cell"><button class="link-btn">详情</button></div></td>
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

const tableData = [
  { type: 'process.started', instance_no: 'SRV-2026-003', task: '-', ticket: '申请服务器 - web-prod-03', time: '2026-08-08 10:30:00' },
  { type: 'task.created', instance_no: 'SRV-2026-003', task: '运维审批', ticket: '申请服务器 - web-prod-03', time: '2026-08-08 10:30:01' },
  { type: 'process.started', instance_no: 'PUR-2026-005', task: '-', ticket: '网络设备采购', time: '2026-08-06 16:40:00' },
  { type: 'task.completed', instance_no: 'SRV-2026-001', task: '运维审批', ticket: '申请服务器 - web-prod-01', time: '2026-08-05 14:30:00' },
  { type: 'process.completed', instance_no: 'SRV-2026-001', task: '-', ticket: '申请服务器 - web-prod-01', time: '2026-08-05 14:32:00' },
]
</script>

<style scoped lang="scss">
.event-log-list { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px; }
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(64,158,255,0.1); display: flex; align-items: center; justify-content: center; }
.icon-symbol { font-size: 18px; }
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }

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
.event-tag { font-size: 12px; padding: 2px 8px; background: #f2f3f5; border-radius: 4px; color: #4e5969; font-family: 'SF Mono', monospace; }
.desc-text { font-size: 13px; color: #86909c; }
.time-text { font-size: 13px; color: #86909c; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 6px; &:hover { color: #337ecc; } }

.pagination-container { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f2f3f5; }
.pagination-info { font-size: 13px; color: #86909c; strong { color: #4e5969; } }
.pagination { display: flex; gap: 4px; }
.pagination-btn { width: 32px; height: 32px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; font-size: 13px; color: #606266; cursor: pointer; display: flex; align-items: center; justify-content: center; &.is-active { background: #409eff; color: #fff; border-color: #409eff; } &.is-disabled { color: #c0c4cc; cursor: not-allowed; } }
</style>
