<template>
  <div class="webhook-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <span class="icon-symbol">🔗</span>
        </div>
        <div>
          <h1>Webhook 订阅</h1>
          <p class="page-header-desc">配置事件推送和回调通知</p>
        </div>
      </div>
      <button class="btn-primary">
        <span class="btn-icon">+</span> 新建订阅
      </button>
    </div>

    <!-- 警告提示 -->
    <div class="alert-card">
      <div class="alert-content">
        <span class="alert-icon">ℹ️</span>
        <div>
          <div class="alert-title">Webhook 签名验证</div>
          <div class="alert-desc">HMAC 签名验证功能即将上线，届时回调请求将携带 X-Webhook-Signature 头部，用于验证请求来源的合法性。当前版本暂不支持。</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table><thead><tr>
            <th><div class="cell">订阅名称</div></th>
            <th><div class="cell">回调 URL</div></th>
            <th><div class="cell">订阅事件</div></th>
            <th><div class="cell">启用</div></th>
            <th><div class="cell">投递记录</div></th>
            <th><div class="cell">创建时间</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in tableData" :key="row.name">
              <td><div class="cell">{{ row.name }}</div></td>
              <td><div class="cell"><span class="endpoint-text">{{ row.url }}</span></div></td>
              <td><div class="cell"><span class="event-tag" v-for="evt in row.events" :key="evt">{{ evt }}</span></div></td>
              <td><div class="cell"><span class="switch-on">●</span></div></td>
              <td><div class="cell"><button class="link-btn">查看</button></div></td>
              <td><div class="cell"><span class="time-text">{{ row.created_at }}</span></div></td>
              <td><div class="cell action-group"><button class="link-btn">编辑</button><button class="link-btn link-btn--danger">删除</button></div></td>
            </tr>
          </tbody></table>
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
  { name: '通知外部审批系统', url: 'https://approval.example.com/hook', events: ['process.started', 'task.created'], created_at: '2026-08-01 10:00' },
  { name: '运维监控推送', url: 'https://monitor.internal/api/events', events: ['process.completed', 'process.terminated'], created_at: '2026-07-20 14:30' },
  { name: '数据同步回调', url: 'https://sync.example.com/callback', events: ['ticket.created'], created_at: '2026-08-05 09:15' },
]
</script>

<style scoped lang="scss">
.webhook-list { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px; }
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(64,158,255,0.1); display: flex; align-items: center; justify-content: center; }
.icon-symbol { font-size: 18px; }
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }
.btn-primary { padding: 8px 20px; background: #409eff; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; &:hover { background: #337ecc; } }
.btn-icon { font-size: 14px; }

.alert-card { margin: 16px 24px 0; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 14px 16px; }
.alert-content { display: flex; align-items: flex-start; gap: 10px; }
.alert-icon { font-size: 16px; margin-top: 1px; }
.alert-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.alert-desc { font-size: 13px; color: #86909c; line-height: 1.6; }

.table-card { margin: 16px 24px 24px; background: #fff; border-radius: 12px; padding: 20px; }
.el-table { width: 100%; border-collapse: collapse; th { background: #fafbfc; color: #86909c; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0; text-align: left; border-bottom: 1px solid #e5e6eb; } td { padding: 14px 0; border-bottom: 1px solid #f2f3f5; font-size: 14px; color: #4e5969; } .cell { padding: 0 12px; } }
.endpoint-text { font-size: 13px; color: #86909c; }
.event-tag { font-size: 11px; padding: 2px 6px; background: #f2f3f5; border-radius: 4px; color: #4e5969; margin-right: 4px; }
.switch-on { color: #67c23a; font-size: 14px; }
.time-text { font-size: 13px; color: #86909c; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 6px; &:hover { color: #337ecc; } &--danger { color: #f56c6c; &:hover { color: #c45656; } } }
.action-group { display: flex; gap: 4px; }

.pagination-container { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f2f3f5; }
.pagination-info { font-size: 13px; color: #86909c; strong { color: #4e5969; } }
.pagination { display: flex; gap: 4px; }
.pagination-btn { width: 32px; height: 32px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; font-size: 13px; color: #606266; cursor: pointer; display: flex; align-items: center; justify-content: center; &.is-active { background: #409eff; color: #fff; border-color: #409eff; } &.is-disabled { color: #c0c4cc; cursor: not-allowed; } }
</style>
