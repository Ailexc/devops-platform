<template>
  <div class="capability-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">🔗</span>
        </div>
        <div>
          <h1>能力注册</h1>
          <p class="page-header-desc">注册和管理自动化执行能力</p>
        </div>
      </div>
      <button class="btn-primary">
        <span class="btn-icon">+</span> 新建能力
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
          <label>执行模式</label>
          <div class="el-select"><div class="el-input__inner">全部</div><span class="el-input__suffix">▼</span></div>
        </div>
        <div class="filter-item">
          <label>关键词</label>
          <div class="el-input"><div class="el-input__inner">搜索能力名称/编码</div></div>
        </div>
        <div class="filter-actions">
          <button class="btn-primary btn-sm">🔍 搜索</button>
          <button class="btn-default">重置</button>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card" :class="{ highlight: focus === 'actions' }">
      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table><thead><tr>
            <th><div class="cell">能力名称</div></th>
            <th><div class="cell">能力编码</div></th>
            <th><div class="cell">执行模式</div></th>
            <th><div class="cell">端点</div></th>
            <th><div class="cell">状态</div></th>
            <th><div class="cell">描述</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in tableData" :key="row.code">
              <td><div class="cell"><span class="ticket-link">{{ row.name }}</span></div></td>
              <td><div class="cell"><code class="cap-code">{{ row.code }}</code></div></td>
              <td><div class="cell"><span class="mode-tag">{{ row.mode }}</span></div></td>
              <td><div class="cell"><span class="endpoint-text">{{ row.endpoint }}</span></div></td>
              <td><div class="cell"><span class="switch-on">●</span></div></td>
              <td><div class="cell"><span class="desc-text">{{ row.desc }}</span></div></td>
              <td><div class="cell action-group"><button class="link-btn">详情</button><button class="link-btn">编辑</button><button class="link-btn link-btn--danger">删除</button></div></td>
            </tr>
          </tbody></table>
        </div>
      </div>
      <div class="pagination-container">
        <span class="pagination-info">共 <strong>4</strong> 条</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const tableData = [
  { name: 'CMDB 创建主机', code: 'cmdb.create_host', mode: '同步', endpoint: 'http://cmdb.local/api/hosts', desc: '在 CMDB 中创建主机记录' },
  { name: '发送通知邮件', code: 'mail.send', mode: '异步', endpoint: 'http://mail.local/api/send', desc: '发送邮件通知给相关人员' },
  { name: 'DNS 解析配置', code: 'dns.configure', mode: '同步', endpoint: 'Mock', desc: '配置 DNS A/CNAME 记录' },
  { name: '防火墙规则', code: 'firewall.add_rule', mode: '异步', endpoint: 'http://fw.local/api/rules', desc: '添加防火墙放行规则' },
]
</script>

<style scoped lang="scss">
.capability-list { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px;
}
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
.el-select, .el-input { display: flex; align-items: center; border: 1px solid #dcdfe6; border-radius: 6px; height: 32px; min-width: 140px; }
.el-input__inner { padding: 0 12px; font-size: 13px; color: #4e5969; flex: 1; }
.el-input__suffix { padding-right: 8px; font-size: 10px; color: #c0c4cc; }
.filter-actions { display: flex; gap: 8px; margin-left: auto; }

.table-card { margin: 16px 24px 24px; background: #fff; border-radius: 12px; padding: 20px; border: 2px solid transparent; transition: all 0.3s; &.highlight { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.15); } }
.el-table { width: 100%; border-collapse: collapse; th { background: #fafbfc; color: #86909c; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0; text-align: left; border-bottom: 1px solid #e5e6eb; } td { padding: 14px 0; border-bottom: 1px solid #f2f3f5; font-size: 14px; color: #4e5969; } .cell { padding: 0 12px; } }
.ticket-link { color: #409eff; cursor: pointer; &:hover { color: #337ecc; } }
.cap-code { font-family: 'SF Mono', monospace; font-size: 12px; color: #8b5cf6; background: #f5f3ff; padding: 2px 8px; border-radius: 4px; }
.mode-tag { font-size: 12px; color: #86909c; }
.endpoint-text { font-size: 13px; color: #86909c; }
.switch-on { color: #67c23a; font-size: 14px; }
.desc-text { font-size: 13px; color: #86909c; }
.action-group { display: flex; gap: 4px; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 6px; &:hover { color: #337ecc; } &--danger { color: #f56c6c; &:hover { color: #c45656; } } }
.pagination-container { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f2f3f5; }
.pagination-info { font-size: 13px; color: #86909c; strong { color: #4e5969; } }
</style>
