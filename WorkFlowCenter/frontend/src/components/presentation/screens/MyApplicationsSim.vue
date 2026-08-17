<template>
  <div class="my-applications">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">📄</span>
        </div>
        <div>
          <h1>我的申请</h1>
          <p class="page-header-desc">管理你发起的所有流程申请</p>
        </div>
      </div>
      <button class="el-button--primary">
        <span class="btn-icon">+</span> 发起申请
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-card-top">
          <span class="stat-label">{{ stat.label }}</span>
          <div class="stat-icon" :class="stat.iconClass">
            <span>{{ stat.icon }}</span>
          </div>
        </div>
        <div class="stat-value">{{ stat.value }}</div>
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
            <div class="el-input__inner">搜索单号 / 标题...</div>
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
          申请列表
          <span class="table-count">5 条</span>
        </div>
        <button class="refresh-btn">🔄 刷新</button>
      </div>

      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table>
            <colgroup><col style="width:160px" /><col style="width:140px" /><col /><col style="width:110px" /><col style="width:120px" /><col style="width:160px" /><col style="width:100px" /></colgroup>
            <thead>
              <tr>
                <th><div class="cell">单号</div></th>
                <th><div class="cell">流程</div></th>
                <th><div class="cell">标题</div></th>
                <th><div class="cell">状态</div></th>
                <th><div class="cell">当前节点</div></th>
                <th><div class="cell">发起时间</div></th>
                <th><div class="cell">操作</div></th>
              </tr>
            </thead>
          </table>
        </div>
        <div class="el-table__body-wrapper">
          <table>
            <colgroup><col style="width:160px" /><col style="width:140px" /><col /><col style="width:110px" /><col style="width:120px" /><col style="width:160px" /><col style="width:100px" /></colgroup>
            <tbody>
              <tr v-for="row in tableData" :key="row.instance_no">
                <td><div class="cell"><span class="ticket-link">{{ row.instance_no }}</span></div></td>
                <td><div class="cell">{{ row.definition_name }}</div></td>
                <td><div class="cell"><span class="ticket-title-text">{{ row.title }}</span></div></td>
                <td><div class="cell"><span class="status-tag" :class="'status-tag--' + row.status"><span class="status-tag__dot"></span>{{ row.statusLabel }}</span></div></td>
                <td><div class="cell">{{ row.current_node }}</div></td>
                <td><div class="cell"><span class="time-text">{{ row.started_at }}</span></div></td>
                <td><div class="cell"><button class="link-btn">详情</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="pagination-container">
        <span class="pagination-info">共 <strong>5</strong> 条记录</span>
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
  { label: '运行中', value: 2, icon: '⏳', iconClass: 'stat-icon--primary' },
  { label: '已挂起', value: 1, icon: '⏸', iconClass: 'stat-icon--warning' },
  { label: '已完成', value: 18, icon: '✅', iconClass: 'stat-icon--success' },
  { label: '已终止', value: 0, icon: '❌', iconClass: 'stat-icon--danger' },
]

const tableData = [
  { instance_no: 'SRV-2026-003', definition_name: '服务器申请', title: '申请服务器 - web-prod-03', status: 'running', statusLabel: '运行中', current_node: '运维审批', started_at: '2026-08-08 10:30' },
  { instance_no: 'SRV-2026-002', definition_name: '服务器申请', title: '数据库扩容申请', status: 'suspended', statusLabel: '已挂起', current_node: '主管审批', started_at: '2026-08-07 14:20' },
  { instance_no: 'SRV-2026-001', definition_name: '服务器申请', title: '申请服务器 - web-prod-01', status: 'completed', statusLabel: '已完成', current_node: '已完成', started_at: '2026-08-05 09:15' },
  { instance_no: 'PUR-2026-005', definition_name: '采购申请', title: '网络设备采购', status: 'running', statusLabel: '运行中', current_node: '财务审批', started_at: '2026-08-06 16:40' },
  { instance_no: 'SRV-2026-004', definition_name: '服务器申请', title: '测试环境申请', status: 'completed', statusLabel: '已完成', current_node: '已完成', started_at: '2026-08-04 11:00' },
]
</script>

<style scoped lang="scss">
.my-applications {
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
  font-size: 20px;
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

.el-button--primary {
  padding: 8px 20px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  &:hover { background: #337ecc; }
}

.btn-icon { font-size: 14px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px 24px 0;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.stat-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stat-label { font-size: 14px; color: #86909c; }

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.stat-icon--primary { background: rgba(64, 158, 255, 0.1); color: #409eff; }
.stat-icon--success { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.stat-icon--warning { background: rgba(230, 162, 60, 0.1); color: #e6a23c; }
.stat-icon--danger { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
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

  label {
    font-size: 13px;
    color: #4e5969;
    font-weight: 500;
  }
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
  font-size: 13px;
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

.table-count {
  font-size: 12px;
  color: #86909c;
  font-weight: 400;
}

.refresh-btn {
  background: none;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 12px;
  color: #606266;
  cursor: pointer;
}

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

.ticket-link, .ticket-title-text {
  color: #409eff;
  cursor: pointer;
  &:hover { color: #337ecc; }
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

.status-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-tag--running { background: #e8f3ff; color: #1677ff; .status-tag__dot { background: #1677ff; } }
.status-tag--completed { background: #e8ffea; color: #00b42a; .status-tag__dot { background: #00b42a; } }
.status-tag--suspended { background: #fff7e8; color: #ff7d00; .status-tag__dot { background: #ff7d00; } }
.status-tag--pending { background: #fff7e8; color: #ff7d00; .status-tag__dot { background: #ff7d00; } }

.time-text { font-size: 13px; color: #86909c; }

.link-btn {
  background: none;
  border: none;
  color: #409eff;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  &:hover { color: #337ecc; }
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

.pagination {
  display: flex;
  gap: 4px;
}

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

  &.is-active {
    background: #409eff;
    color: #fff;
    border-color: #409eff;
  }

  &.is-disabled {
    color: #c0c4cc;
    cursor: not-allowed;
  }
}
</style>
