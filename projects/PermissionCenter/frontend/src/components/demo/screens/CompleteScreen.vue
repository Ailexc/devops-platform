<template>
  <div class="mock-screen complete-screen">
    <div class="complete-content">
      <div class="celebrate-icon">🎉</div>
      <h2 class="complete-title">发布流程完成！</h2>
      <p class="complete-desc">小黄成功完成了「主机监控」能力包的发布流程</p>

      <div class="flow-summary">
        <div class="flow-node" v-for="(f, i) in flows" :key="i">
          <div class="flow-emoji">{{ f.icon }}</div>
          <div class="flow-text">{{ f.label }}</div>
          <div v-if="i < flows.length - 1" class="flow-connector">→</div>
        </div>
      </div>

      <div class="arch-card">
        <div class="arch-title">🏗️ 核心架构</div>
        <div class="arch-row">
          <div class="arch-block pex">PEP<br><small>网关鉴权</small></div>
          <div class="arch-block pdp">PDP<br><small>策略决策</small></div>
          <div class="arch-block pap">PAP<br><small>策略管理</small></div>
          <div class="arch-block pip">PIP<br><small>身份解析</small></div>
        </div>
      </div>

      <div class="particle p1"></div>
      <div class="particle p2"></div>
      <div class="particle p3"></div>
      <div class="particle p4"></div>
      <div class="particle p5"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
const flows = [
  { icon: '📝', label: '声明能力' },
  { icon: '⚙️', label: '配置预设' },
  { icon: '🚀', label: '上架市场' },
  { icon: '✅', label: '审批通过' },
]
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--brand-soft) 0%, var(--bg) 50%, var(--success-bg) 100%); }
.complete-content { text-align: center; position: relative; z-index: 1; }
.celebrate-icon { font-size: 64px; margin-bottom: 16px; animation: bounce 1s ease infinite; }
.complete-title { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.complete-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 32px; }
.flow-summary { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 32px; }
.flow-node { display: flex; align-items: center; gap: 8px; }
.flow-emoji { font-size: 24px; }
.flow-text { font-size: 13px; font-weight: 600; color: var(--text); }
.flow-connector { font-size: 18px; color: var(--brand); margin: 0 4px; }
.arch-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; max-width: 45%; margin: 0 auto; }
.arch-title { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 14px; }
.arch-row { display: flex; gap: 12px; justify-content: center; }
.arch-block { flex: 1; padding: 14px 8px; border-radius: 8px; text-align: center; font-size: 14px; font-weight: 700; }
.arch-block small { display: block; font-size: 11px; font-weight: 400; margin-top: 2px; opacity: 0.8; }
.arch-block.pep { background: var(--info-bg); color: var(--info); }
.arch-block.pdp { background: var(--success-bg); color: var(--success); }
.arch-block.pap { background: var(--purple-bg); color: var(--purple); }
.arch-block.pip { background: var(--warning-bg); color: var(--warning); }

.particle { position: absolute; width: 8px; height: 8px; border-radius: 50%; animation: float 3s ease-in-out infinite; }
.p1 { background: var(--brand); top: 10%; left: 20%; animation-delay: 0s; }
.p2 { background: var(--success); top: 30%; right: 15%; animation-delay: 0.5s; }
.p3 { background: var(--warning); bottom: 20%; left: 10%; animation-delay: 1s; }
.p4 { background: var(--purple); top: 50%; right: 25%; animation-delay: 1.5s; }
.p5 { background: var(--danger); bottom: 30%; right: 10%; animation-delay: 2s; }

@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
@keyframes float { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.6; } 50% { transform: translateY(-20px) scale(1.2); opacity: 1; } }
</style>
