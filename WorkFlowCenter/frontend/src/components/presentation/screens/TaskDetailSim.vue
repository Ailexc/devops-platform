<template>
  <div class="task-detail">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-back">←</div>
        <div>
          <h1>任务办理</h1>
          <p class="page-header-desc">申请服务器 - web-prod-01</p>
        </div>
      </div>
      <div class="task-meta">
        <span class="meta-tag meta-tag--primary">SRV-2026-001</span>
        <span class="meta-tag meta-tag--warning">待审批</span>
      </div>
    </div>

    <div class="task-body">
      <div class="task-main">
        <div class="info-card">
          <div class="card-title">申请信息</div>
          <el-alert v-if="focus === 'autoExecute'" type="success" :closable="false" show-icon title="自动执行成功" description="CMDB 已创建主机" class="abnormal-alert" />
          <div class="desc-grid">
            <div class="desc-item"><span class="desc-label">主机名</span><span class="desc-value">web-prod-01</span></div>
            <div class="desc-item"><span class="desc-label">CPU</span><span class="desc-value">8 核</span></div>
            <div class="desc-item"><span class="desc-label">内存</span><span class="desc-value">16 GB</span></div>
            <div class="desc-item"><span class="desc-label">操作系统</span><span class="desc-value">CentOS 7</span></div>
          </div>
          <div class="desc-item desc-item--full"><span class="desc-label">申请理由</span><span class="desc-value">线上扩容，支撑业务增长</span></div>
        </div>

        <div class="action-card" :class="{ highlight: focus === 'approval' || focus === 'approve' }">
          <div class="card-title">审批操作</div>
          <div class="opinion-input">
            <label>审批意见 <span class="required">*</span></label>
            <div class="el-textarea"><div class="el-textarea__inner">请输入审批意见...</div></div>
          </div>
          <div class="action-buttons">
            <button class="btn-danger">拒绝</button>
            <button class="btn-success">同意</button>
          </div>
        </div>

        <div v-if="focus === 'autoExecute'" class="execute-card highlight">
          <div class="card-title">⚡ 自动执行</div>
          <div class="exec-status success">
            <span class="exec-icon">✅</span>
            <div><div class="exec-title">CMDB 创建主机</div><div class="exec-detail">主机 ID: host-20260808-001 | IP: 10.0.1.100 | 状态: 运行中</div></div>
          </div>
        </div>
      </div>

      <div class="task-side">
        <div class="side-card">
          <div class="card-title">流程追踪</div>
          <div class="timeline">
            <div class="tl-item completed"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">发起申请</div><div class="tl-desc">小明 · 2026-08-08 10:30</div></div></div>
            <div class="tl-item active"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">运维审批</div><div class="tl-desc">小李 · 进行中</div></div></div>
            <div class="tl-item"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">自动开通</div><div class="tl-desc">待处理</div></div></div>
            <div class="tl-item"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">结束</div><div class="tl-desc">待处理</div></div></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<style scoped lang="scss">
.task-detail { width: 100%; height: 100%; display: flex; flex-direction: column; background: #f5f7fa; }
.page-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e6eb; padding: 16px 24px; }
.page-header-left { display: flex; align-items: center; gap: 16px; }
.page-header-back { width: 32px; height: 32px; border-radius: 8px; background: #f5f7fa; display: flex; align-items: center; justify-content: center; font-size: 16px; color: #4e5969; cursor: pointer; }
.page-header h1 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 13px; color: #86909c; margin: 2px 0 0; }
.task-meta { display: flex; gap: 8px; }
.meta-tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.meta-tag--primary { background: #e8f3ff; color: #1677ff; }
.meta-tag--warning { background: #fff7e8; color: #ff7d00; }

.task-body { flex: 1; display: flex; gap: 20px; padding: 20px 24px; overflow: hidden; }
.task-main { flex: 1; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
.task-side { width: 300px; flex-shrink: 0; }

.info-card, .action-card, .execute-card, .side-card {
  background: #fff; border-radius: 12px; padding: 20px;
  border: 2px solid transparent; transition: all 0.3s;
}
.info-card.highlight, .action-card.highlight, .execute-card.highlight { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.15); }
.card-title { font-size: 15px; font-weight: 600; color: #1d2129; margin-bottom: 16px; }

.abnormal-alert { margin-bottom: 16px; padding: 12px 16px; border-radius: 8px; background: #e8ffea; border: 1px solid #b7eb8f; }

.desc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0; }
.desc-item { padding: 12px 0; border-bottom: 1px solid #f2f3f5; &--full { grid-column: 1 / -1; } }
.desc-label { display: block; font-size: 12px; color: #86909c; margin-bottom: 4px; }
.desc-value { font-size: 14px; color: #1d2129; }

.opinion-input { margin-bottom: 16px; label { display: block; font-size: 13px; color: #4e5969; margin-bottom: 6px; font-weight: 500; } }
.required { color: #f56c6c; }
.el-textarea { border: 1px solid #dcdfe6; border-radius: 6px; }
.el-textarea__inner { padding: 10px 12px; font-size: 13px; color: #c0c4cc; min-height: 80px; }

.action-buttons { display: flex; gap: 12px; justify-content: flex-end; }
.btn-success { padding: 8px 20px; background: #67c23a; color: #fff; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; &:hover { background: #5daf34; } }
.btn-danger { padding: 8px 20px; background: #f56c6c; color: #fff; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; &:hover { background: #dd6161; } }

.execute-card.highlight { border-color: #67c23a !important; box-shadow: 0 0 0 3px rgba(103,194,58,0.15) !important; }
.exec-status { display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 8px; background: #f0fdf4; }
.exec-icon { font-size: 20px; }
.exec-title { font-size: 14px; font-weight: 600; color: #1d2129; }
.exec-detail { font-size: 12px; color: #86909c; margin-top: 4px; }

.side-card { height: 100%; }
.timeline { position: relative; padding-left: 24px; &::before { content: ''; position: absolute; left: 7px; top: 6px; bottom: 6px; width: 2px; background: #e5e6eb; } }
.tl-item { position: relative; padding-bottom: 24px; &:last-child { padding-bottom: 0; } }
.tl-dot { position: absolute; left: -21px; top: 5px; width: 12px; height: 12px; border-radius: 50%; background: #dcdfe6; border: 2px solid #fff; }
.tl-item.completed .tl-dot { background: #67c23a; }
.tl-item.active .tl-dot { background: #409eff; animation: pulse 2s infinite; }
.tl-title { font-size: 14px; font-weight: 500; color: #1d2129; }
.tl-desc { font-size: 12px; color: #86909c; margin-top: 4px; }

@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(64,158,255,0.4); } 50% { box-shadow: 0 0 0 6px rgba(64,158,255,0); } }
</style>
