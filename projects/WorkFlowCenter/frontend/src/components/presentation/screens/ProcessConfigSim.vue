<template>
  <div class="process-definition-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">⚙</span>
        </div>
        <div>
          <h1>流程配置</h1>
          <p class="page-header-desc">管理和配置业务流程模版</p>
        </div>
      </div>
      <button class="btn-primary">
        <span class="btn-icon">+</span> 新建流程
      </button>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>状态</label>
          <div class="el-select"><div class="el-input__inner">全部</div><span class="el-input__suffix">▼</span></div>
        </div>
        <div class="filter-item">
          <label>关键词</label>
          <div class="el-input"><div class="el-input__inner">搜索流程名称</div></div>
        </div>
        <div class="filter-actions">
          <button class="btn-primary btn-sm">🔍 搜索</button>
          <button class="btn-default">重置</button>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div class="table-card-header">
        <div class="table-card-title">流程列表 <span class="table-count">4 条</span></div>
      </div>

      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table><thead><tr>
            <th><div class="cell">流程名称</div></th>
            <th><div class="cell">唯一标识</div></th>
            <th><div class="cell">描述</div></th>
            <th><div class="cell">版本</div></th>
            <th><div class="cell">状态</div></th>
            <th><div class="cell">分类</div></th>
            <th><div class="cell">创建时间</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in tableData" :key="row.key">
              <td><div class="cell"><span class="ticket-link">{{ row.name }}</span></div></td>
              <td><div class="cell"><code class="cap-code">{{ row.key }}</code></div></td>
              <td><div class="cell"><span class="desc-text">{{ row.description }}</span></div></td>
              <td><div class="cell"><span class="version-text">v{{ row.version }}</span></div></td>
              <td><div class="cell"><span class="status-tag" :class="'status-tag--' + row.status"><span class="status-tag__dot"></span>{{ row.statusLabel }}</span></div></td>
              <td><div class="cell"><span class="category-tag">{{ row.category }}</span></div></td>
              <td><div class="cell"><span class="time-text">{{ row.created_at }}</span></div></td>
              <td><div class="cell action-group">
                <button class="link-btn">编辑</button>
                <button v-if="row.status === 'draft'" class="link-btn link-btn--success">发布</button>
                <button v-if="row.status === 'published'" class="link-btn link-btn--warning">停用</button>
                <button class="link-btn link-btn--danger">删除</button>
              </div></td>
            </tr>
          </tbody></table>
        </div>
      </div>

      <div class="pagination-container">
        <span class="pagination-info">共 <strong>4</strong> 条</span>
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
  { name: '服务器申请', key: 'server_request', description: '申请服务器资源，支持 CPU、内存等配置', version: 3, status: 'published', statusLabel: '已发布', category: 'IT 运维', created_at: '2026-08-01 10:00' },
  { name: '采购申请', key: 'purchase_request', description: '设备采购流程，含财务审批', version: 2, status: 'published', statusLabel: '已发布', category: '行政', created_at: '2026-07-20 14:30' },
  { name: '请假申请', key: 'leave_request', description: '员工请假审批流程', version: 1, status: 'draft', statusLabel: '草稿', category: '人事', created_at: '2026-08-05 09:00' },
  { name: '报销申请', key: 'expense_request', description: '费用报销审批流程', version: 1, status: 'disabled', statusLabel: '已停用', category: '财务', created_at: '2026-07-10 16:20' },
]
</script>

<style scoped lang="scss">
.process-definition-list { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px; }
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(64,158,255,0.1); display: flex; align-items: center; justify-content: center; }
.icon-symbol { font-size: 18px; }
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }
.btn-primary { padding: 8px 20px; background: #409eff; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; &:hover { background: #337ecc; } }
.btn-icon { font-size: 14px; }
.btn-sm { padding: 6px 16px; font-size: 13px; }
.btn-default { padding: 6px 16px; background: #fff; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 13px; color: #606266; cursor: pointer; &:hover { border-color: #409eff; color: #409eff; } }

.filter-card { margin: 16px 24px 0; background: #fff; border-radius: 12px; padding: 16px 20px; }
.filter-row { display: flex; align-items: flex-end; gap: 16px; }
.filter-item { display: flex; flex-direction: column; gap: 6px; label { font-size: 13px; color: #4e5969; font-weight: 500; } }
.el-select, .el-input { display: flex; align-items: center; border: 1px solid #dcdfe6; border-radius: 6px; height: 32px; min-width: 160px; }
.el-input__inner { padding: 0 12px; font-size: 13px; color: #4e5969; flex: 1; }
.el-input__suffix { padding-right: 8px; font-size: 10px; color: #c0c4cc; }
.filter-actions { display: flex; gap: 8px; margin-left: auto; }

.table-card { margin: 16px 24px 24px; background: #fff; border-radius: 12px; padding: 20px; }
.table-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table-card-title { font-size: 15px; font-weight: 600; color: #1d2129; display: flex; align-items: center; gap: 8px; }
.table-count { font-size: 12px; color: #86909c; font-weight: 400; }

.el-table { width: 100%; border-collapse: collapse; th { background: #fafbfc; color: #86909c; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0; text-align: left; border-bottom: 1px solid #e5e6eb; } td { padding: 14px 0; border-bottom: 1px solid #f2f3f5; font-size: 14px; color: #4e5969; } .cell { padding: 0 12px; } }
.ticket-link { color: #409eff; cursor: pointer; &:hover { color: #337ecc; } }
.cap-code { font-family: 'SF Mono', monospace; font-size: 12px; color: #8b5cf6; background: #f5f3ff; padding: 2px 8px; border-radius: 4px; }
.desc-text { font-size: 13px; color: #86909c; }
.version-text { font-size: 13px; color: #86909c; }
.category-tag { font-size: 12px; padding: 2px 8px; background: #f2f3f5; border-radius: 4px; color: #4e5969; }
.status-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; }
.status-tag--published { background: #e8ffea; color: #00b42a; .status-tag__dot { background: #00b42a; } }
.status-tag--draft { background: #f2f3f5; color: #86909c; .status-tag__dot { background: #86909c; } }
.status-tag--disabled { background: #ffece8; color: #f53f3f; .status-tag__dot { background: #f53f3f; } }
.time-text { font-size: 13px; color: #86909c; }
.action-group { display: flex; gap: 4px; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 6px; &:hover { opacity: 0.8; } &--success { color: #67c23a; } &--warning { color: #e6a23c; } &--danger { color: #f56c6c; } }

.pagination-container { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f2f3f5; }
.pagination-info { font-size: 13px; color: #86909c; strong { color: #4e5969; } }
.pagination { display: flex; gap: 4px; }
.pagination-btn { width: 32px; height: 32px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; font-size: 13px; color: #606266; cursor: pointer; display: flex; align-items: center; justify-content: center; &.is-active { background: #409eff; color: #fff; border-color: #409eff; } &.is-disabled { color: #c0c4cc; cursor: not-allowed; } }
</style>
