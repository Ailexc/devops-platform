<template>
  <div class="approval-task-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">📋</span>
        </div>
        <div>
          <h1>待办审批</h1>
          <p class="page-header-desc">需要你处理的审批任务</p>
        </div>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>状态</label>
          <div class="el-select">
            <div class="el-input__inner">全部</div>
            <span class="el-input__suffix">▼</span>
          </div>
        </div>
        <div class="filter-item">
          <label>关键词</label>
          <div class="el-input">
            <div class="el-input__inner">搜索节点名称</div>
          </div>
        </div>
        <div class="filter-actions">
          <button class="el-button--primary">🔍 搜索</button>
          <button class="el-button--default">重置</button>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div class="table-card-header">
        <div class="table-card-title">
          任务列表
          <span class="table-count">3 条</span>
        </div>
      </div>

      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table>
            <colgroup><col /><col style="width:120px" /><col style="width:90px" /><col style="width:100px" /><col style="width:100px" /><col style="width:160px" /><col style="width:110px" /></colgroup>
            <thead>
              <tr>
                <th><div class="cell">申请标题</div></th>
                <th><div class="cell">节点</div></th>
                <th><div class="cell">类型</div></th>
                <th><div class="cell">处理人</div></th>
                <th><div class="cell">状态</div></th>
                <th><div class="cell">创建时间</div></th>
                <th><div class="cell">操作</div></th>
              </tr>
            </thead>
          </table>
        </div>
        <div class="el-table__body-wrapper">
          <table>
            <colgroup><col /><col style="width:120px" /><col style="width:90px" /><col style="width:100px" /><col style="width:100px" /><col style="width:160px" /><col style="width:110px" /></colgroup>
            <tbody>
              <tr v-for="row in tableData" :key="row.instance_no">
                <td><div class="cell"><span class="ticket-link">{{ row.title }}</span></div></td>
                <td><div class="cell">{{ row.node_name }}</div></td>
                <td><div class="cell"><span class="type-text">{{ row.node_type }}</span></div></td>
                <td><div class="cell">{{ row.assignee }}</div></td>
                <td><div class="cell"><span class="status-tag" :class="'status-tag--' + row.status"><span class="status-tag__dot"></span>{{ row.statusLabel }}</span></div></td>
                <td><div class="cell"><span class="time-text">{{ row.created_at }}</span></div></td>
                <td><div class="cell"><button class="link-btn link-btn--warning">办理</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="pagination-container">
        <span class="pagination-info">共 <strong>3</strong> 条</span>
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
  { title: '申请服务器 - web-prod-03', node_name: '运维审批', node_type: '审批', assignee: '小李', status: 'pending', statusLabel: '待处理', created_at: '2026-08-08 10:35' },
  { title: '数据库扩容申请', node_name: '主管审批', node_type: '审批', assignee: 'admin', status: 'pending', statusLabel: '待处理', created_at: '2026-08-07 14:25' },
  { title: '网络设备采购', node_name: '财务审批', node_type: '审批', assignee: '王会计', status: 'pending', statusLabel: '待处理', created_at: '2026-08-06 16:45' },
]
</script>

<style scoped lang="scss">
.approval-task-list {
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  overflow-y: auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
  padding: 16px 24px;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(64, 158, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-symbol { font-size: 18px; }

.page-header h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}

.page-header-desc {
  font-size: 13px;
  color: #86909c;
  margin: 2px 0 0;
}

.filter-card {
  margin: 16px 24px 0;
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  label { font-size: 13px; color: #4e5969; font-weight: 500; }
}

.el-select, .el-input {
  display: flex;
  align-items: center;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  height: 32px;
  min-width: 160px;
}

.el-input__inner {
  padding: 0 12px;
  font-size: 13px;
  color: #4e5969;
  flex: 1;
}

.el-input__suffix {
  padding-right: 8px;
  font-size: 10px;
  color: #c0c4cc;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.el-button--primary {
  padding: 6px 16px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  &:hover { background: #337ecc; }
}

.el-button--default {
  padding: 6px 16px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  &:hover { border-color: #409eff; color: #409eff; }
}

.table-card {
  margin: 16px 24px 24px;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.table-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-count { font-size: 12px; color: #86909c; font-weight: 400; }

.el-table {
  width: 100%;
  border-collapse: collapse;

  th {
    background: #fafbfc;
    color: #86909c;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 0;
    text-align: left;
    border-bottom: 1px solid #e5e6eb;
  }

  td {
    padding: 14px 0;
    border-bottom: 1px solid #f2f3f5;
    font-size: 14px;
    color: #4e5969;
  }

  .cell { padding: 0 12px; }
}

.ticket-link {
  color: #409eff;
  cursor: pointer;
  &:hover { color: #337ecc; }
}

.type-text {
  font-size: 12px;
  color: #86909c;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; }
.status-tag--pending { background: #fff7e8; color: #ff7d00; .status-tag__dot { background: #ff7d00; } }
.status-tag--running { background: #e8f3ff; color: #1677ff; .status-tag__dot { background: #1677ff; } }
.status-tag--completed { background: #e8ffea; color: #00b42a; .status-tag__dot { background: #00b42a; } }

.time-text { font-size: 13px; color: #86909c; }

.link-btn {
  background: none;
  border: none;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  &--warning { color: #e6a23c; }
  &:hover { opacity: 0.8; }
}

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f2f3f5;
}

.pagination-info {
  font-size: 13px;
  color: #86909c;
  strong { color: #4e5969; }
}

.pagination { display: flex; gap: 4px; }

.pagination-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  &.is-active { background: #409eff; color: #fff; border-color: #409eff; }
  &.is-disabled { color: #c0c4cc; cursor: not-allowed; }
}
</style>
