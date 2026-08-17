<template>
  <div class="mock-screen">
    <div class="mock-topbar"><div class="mock-breadcrumb">系统观测 / <b>Owner 巡检视图</b></div><div class="mock-user">👤 admin</div></div>
    <div class="mock-content">
      <h2 class="mock-title">🔍 Owner 巡检视图</h2>
      <p class="mock-sub">程序化兜底：应用 owner 失联提醒 → N 次无响应自动停用 → 新 owner 认领恢复</p>

      <div class="toolbar">
        <button class="btn-primary">🔄 手动触发巡检</button>
      </div>

      <div class="rule-tip">💡 巡检规则：owner 最近 7 天无活动 → 提醒计数 +1；达 3 次无响应 → 应用自动停用，可由新 owner 通过「认领」恢复。</div>

      <div class="section-label">失联中的 Owner（4）</div>
      <div class="section-card">
        <table class="mock-table">
          <thead><tr><th>应用</th><th>Owner</th><th>角色</th><th>提醒次数</th><th>应用状态</th></tr></thead>
          <tbody>
            <tr v-for="o in owners" :key="o.app">
              <td><span class="app-icon">📡</span> {{ o.app }}</td>
              <td>{{ o.owner }}</td>
              <td><span class="tag primary">主</span></td>
              <td class="mono warn">{{ o.remind }}/3</td>
              <td><span class="tag ok">运行中</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="key-point"><span>💡</span><span>Owner 巡检解决「应用失管」问题：owner 长期不活跃 → 系统自动提醒（app_owners.remind_count 递增）→ 达阈值停用 → 新 owner 认领后恢复，保障应用可持续治理。</span></div>
    </div>
  </div>
</template>
<script setup lang="ts">
const owners = [
  { app: 'monitor 监控告警中心', owner: '艾琳 (erin)', remind: 1 },
  { app: 'cloudportal 云管平台', owner: '艾琳 (erin)', remind: 2 },
  { app: 'itsm IT服务管理', owner: '管理员 (admin)', remind: 1 },
  { app: 'cmdb 配置管理数据库', owner: '爱丽丝 (alice)', remind: 1 },
]
</script>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 18px 22px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.mock-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }
.toolbar { display: flex; margin-bottom: 10px; }
.btn-primary { padding: 7px 16px; border: none; border-radius: 7px; background: var(--brand); color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; }
.rule-tip { padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; font-size: 11px; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.5; }
.section-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; }
.mock-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.mock-table th { text-align: left; padding: 6px 10px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); }
.mock-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); color: var(--text); }
.app-icon { font-size: 13px; }
.mono { font-family: var(--font-mono); }
.mono.warn { color: var(--warning); font-weight: 700; }
.tag { font-size: 10px; font-weight: 600; padding: 1px 8px; border-radius: 10px; }
.tag.ok { color: var(--success); background: var(--success-bg); }
.tag.primary { color: var(--brand); background: var(--brand-soft); }
.key-point { display: flex; gap: 8px; padding: 10px 14px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 12px; color: var(--info); line-height: 1.5; }
</style>
