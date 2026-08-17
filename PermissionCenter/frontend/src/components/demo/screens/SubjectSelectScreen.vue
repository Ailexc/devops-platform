<template>
  <div class="mock-screen subject-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">能力市场 / 主机监控 / 选择预设 / <b>选择主体</b></div>
      <div class="mock-user">👤 小红</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">👤 选择授权主体</h2>
      <p class="mock-sub">选择谁需要此权限（支持多主体同时申请）</p>

      <div class="subject-list">
        <div class="subject-card selected">
          <div class="subject-icon">👤</div>
          <div class="subject-info">
            <div class="subject-name">小红</div>
            <div class="subject-type">人员身份 · 研发一部</div>
          </div>
          <div class="subject-check">✅</div>
        </div>

        <div class="subject-card selected">
          <div class="subject-icon">🔌</div>
          <div class="subject-info">
            <div class="subject-name">小红的数据分析</div>
            <div class="subject-type">程序身份 · client:data-analysis</div>
          </div>
          <div class="subject-check">✅</div>
        </div>

        <div class="subject-card">
          <div class="subject-icon">👥</div>
          <div class="subject-info">
            <div class="subject-name">研发一部</div>
            <div class="subject-type">组织身份 · 23 人</div>
          </div>
          <div class="subject-check">⬜</div>
        </div>
      </div>

      <div class="note-box">
        💡 选择「程序身份」时，将由人（小红）代理申请，审批通过后程序身份获得相应权限。
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.mock-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 20px; }
.subject-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.subject-card { display: flex; align-items: center; gap: 14px; padding: 14px 16px; border: 1.5px solid var(--border); border-radius: 10px; cursor: pointer; transition: all 0.15s; }
.subject-card.selected { border-color: var(--brand); background: var(--brand-softer); box-shadow: 0 0 0 3px var(--brand-soft); }
.subject-icon { font-size: 28px; flex-shrink: 0; }
.subject-info { flex: 1; }
.subject-name { font-size: 14px; font-weight: 600; color: var(--text); }
.subject-type { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.subject-check { font-size: 18px; flex-shrink: 0; }
.note-box { padding: 12px 16px; background: var(--info-bg); border: 1px solid var(--info); border-radius: 8px; font-size: 13px; color: var(--info); }
</style>
