<template>
  <div class="home-page">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-left">
        <h1>工作台</h1>
        <p class="welcome-desc">欢迎回来，admin！这是你的工作台概览。</p>
      </div>
      <button class="btn-primary">
        <span class="btn-icon">+</span> 发起申请
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" :class="{ highlight: focus === 'stats' }" v-for="stat in stats" :key="stat.label">
        <div class="stat-card-top">
          <span class="stat-label">{{ stat.label }}</span>
          <div class="stat-icon" :class="stat.iconClass">{{ stat.icon }}</div>
        </div>
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-footer">{{ stat.footer }}</div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="section-card" :class="{ highlight: focus === 'shortcuts' }">
      <div class="section-header">
        <div class="section-title">
          <span class="section-title__bar"></span>
          快捷入口
        </div>
      </div>
      <div class="quick-grid">
        <div class="quick-item" v-for="s in shortcuts" :key="s.label">
          <div class="quick-icon" :class="s.iconClass">{{ s.icon }}</div>
          <span class="quick-label">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- 最近工单 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <span class="section-title__bar"></span>
          最近工单
        </div>
        <button class="link-btn">查看更多 →</button>
      </div>
      <div class="el-table">
        <div class="el-table__header-wrapper">
          <table><thead><tr>
            <th><div class="cell">工单标题</div></th>
            <th><div class="cell">流程</div></th>
            <th><div class="cell">状态</div></th>
            <th><div class="cell">创建时间</div></th>
            <th><div class="cell">操作</div></th>
          </tr></thead></table>
        </div>
        <div class="el-table__body-wrapper">
          <table><tbody>
            <tr v-for="row in recentTickets" :key="row.title">
              <td><div class="cell"><span class="ticket-link">{{ row.title }}</span></div></td>
              <td><div class="cell">{{ row.def }}</div></td>
              <td><div class="cell"><span class="status-tag" :class="'status-tag--' + row.status"><span class="status-tag__dot"></span>{{ row.statusLabel }}</span></div></td>
              <td><div class="cell"><span class="time-text">{{ row.time }}</span></div></td>
              <td><div class="cell"><button class="link-btn">查看</button></div></td>
            </tr>
          </tbody></table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()

const stats = [
  { label: '待办任务', value: 3, icon: '📋', iconClass: 'stat-icon--primary', footer: '需要你处理的审批' },
  { label: '已办任务', value: 12, icon: '✅', iconClass: 'stat-icon--success', footer: '已完成的审批' },
  { label: '我发起的', value: 5, icon: '🚀', iconClass: 'stat-icon--warning', footer: '我的流程申请' },
  { label: '抄送我的', value: 2, icon: '📬', iconClass: 'stat-icon--danger', footer: '与你相关的通知' },
]

const shortcuts = [
  { icon: '+', label: '发起申请', iconClass: 'quick-icon--blue' },
  { icon: '✓', label: '待办审批', iconClass: 'quick-icon--orange' },
  { icon: '📄', label: '我的申请', iconClass: 'quick-icon--green' },
  { icon: '⚙', label: '流程配置', iconClass: 'quick-icon--purple' },
  { icon: '🔔', label: '通知中心', iconClass: 'quick-icon--red' },
]

const recentTickets = [
  { title: '申请服务器 - web-prod-02', def: '服务器申请', status: 'running', statusLabel: '运行中', time: '2026-08-08 10:30' },
  { title: '数据库扩容申请', def: '服务器申请', status: 'completed', statusLabel: '已完成', time: '2026-08-07 14:20' },
  { title: '网络设备采购', def: '采购申请', status: 'pending', statusLabel: '审批中', time: '2026-08-06 09:15' },
]
</script>

<style scoped lang="scss">
.home-page {
  width: 100%; height: 100%;
  background: #f5f7fa; padding: 24px; overflow-y: auto;
}
.welcome-section {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-radius: 12px; padding: 24px 28px; margin-bottom: 24px;
}
.welcome-left h1 { font-size: 24px; font-weight: 700; color: #1d2129; margin: 0 0 4px; }
.welcome-desc { font-size: 14px; color: #86909c; margin: 0; }
.btn-primary {
  padding: 10px 24px; background: #409eff; color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px; &:hover { background: #337ecc; }
}
.btn-icon { font-size: 16px; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: #fff; border-radius: 12px; padding: 20px; border: 2px solid transparent;
  transition: all 0.3s; cursor: pointer;
  &:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); transform: translateY(-2px); }
  &.highlight { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.15); }
}
.stat-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.stat-label { font-size: 14px; color: #86909c; }
.stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat-icon--primary { background: rgba(64,158,255,0.1); color: #409eff; }
.stat-icon--success { background: rgba(103,194,58,0.1); color: #67c23a; }
.stat-icon--warning { background: rgba(230,162,60,0.1); color: #e6a23c; }
.stat-icon--danger { background: rgba(245,108,108,0.1); color: #f56c6c; }
.stat-value { font-size: 32px; font-weight: 700; color: #1d2129; margin-bottom: 4px; }
.stat-footer { font-size: 12px; color: #c9cdd4; }

.section-card {
  background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 20px;
  border: 2px solid transparent; transition: all 0.3s;
  &.highlight { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.15); }
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-title {
  font-size: 16px; font-weight: 600; color: #1d2129;
  display: flex; align-items: center; gap: 8px;
}
.section-title__bar { display: inline-block; width: 4px; height: 16px; background: #409eff; border-radius: 2px; }
.link-btn { background: none; border: none; color: #409eff; font-size: 13px; cursor: pointer; padding: 4px 8px; &:hover { color: #337ecc; } }

.quick-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.quick-item {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 16px 8px; border-radius: 8px; cursor: pointer; transition: all 0.2s;
  &:hover { background: #f5f7fa; }
}
.quick-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.quick-icon--blue { background: rgba(64,158,255,0.1); color: #409eff; }
.quick-icon--orange { background: rgba(230,162,60,0.1); color: #e6a23c; }
.quick-icon--green { background: rgba(103,194,58,0.1); color: #67c23a; }
.quick-icon--purple { background: rgba(139,92,246,0.1); color: #8b5cf6; }
.quick-icon--red { background: rgba(245,108,108,0.1); color: #f56c6c; }
.quick-label { font-size: 13px; color: #4e5969; }

.el-table { width: 100%; border-collapse: collapse; th {
  background: #fafbfc; color: #86909c; font-weight: 600; font-size: 12px;
  text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 0; text-align: left;
  border-bottom: 1px solid #e5e6eb;
} td { padding: 14px 0; border-bottom: 1px solid #f2f3f5; font-size: 14px; color: #4e5969; } .cell { padding: 0 12px; } }
.ticket-link { color: #409eff; cursor: pointer; &:hover { color: #337ecc; } }
.status-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.status-tag__dot { width: 6px; height: 6px; border-radius: 50%; }
.status-tag--running { background: #e8f3ff; color: #1677ff; .status-tag__dot { background: #1677ff; } }
.status-tag--completed { background: #e8ffea; color: #00b42a; .status-tag__dot { background: #00b42a; } }
.status-tag--pending { background: #fff7e8; color: #ff7d00; .status-tag__dot { background: #ff7d00; } }
.time-text { font-size: 13px; color: #86909c; }
</style>
