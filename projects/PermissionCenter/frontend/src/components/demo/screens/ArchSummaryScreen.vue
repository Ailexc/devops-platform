<template>
  <div class="mock-screen arch-screen">
    <div class="arch-content">
      <h2 class="arch-title">🏗️ 去中心化 IAM 架构总结</h2>
      <p class="arch-sub">Permission Center — 面向下一代的权限管理平台</p>

      <div class="arch-grid">
        <div class="arch-box pep"><div class="ab-icon">🌐</div><div class="ab-name">PEP</div><div class="ab-desc">策略执行点<br>Traefik 网关鉴权</div></div>
        <div class="arch-box pdp"><div class="ab-icon">🧠</div><div class="ab-name">PDP</div><div class="ab-desc">策略决策点<br>Casbin + OpenFGA 双引擎</div></div>
        <div class="arch-box pap"><div class="ab-icon">📋</div><div class="ab-name">PAP</div><div class="ab-desc">策略管理点<br>审批即策略，授权全闭环</div></div>
        <div class="arch-box pip"><div class="ab-icon">🔍</div><div class="ab-name">PIP</div><div class="ab-desc">策略信息点<br>身份解析 + 组织链路</div></div>
      </div>

      <div class="feature-grid">
        <div class="feat"><span>🔑</span><span>组即角色（删 Role）</span></div>
        <div class="feat"><span>📋</span><span>授权即审批（SoD）</span></div>
        <div class="feat"><span>🔗</span><span>双引擎（Casbin + OpenFGA）</span></div>
        <div class="feat"><span>📦</span><span>能力包（声明式权限）</span></div>
        <div class="feat"><span>🔄</span><span>策略分发（Agent + Bundle）</span></div>
        <div class="feat"><span>📊</span><span>全链路可观测（TraceID）</span></div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--brand-soft) 0%, var(--bg) 50%, var(--purple-bg) 100%); }
.arch-content { text-align: center; max-width: 55%; }
.arch-title { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.arch-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; }
.arch-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
.arch-box { padding: 14px 8px; border-radius: 10px; text-align: center; }
.arch-box.pep { background: var(--info-bg); }
.arch-box.pdp { background: var(--success-bg); }
.arch-box.pap { background: var(--purple-bg); }
.arch-box.pip { background: var(--warning-bg); }
.ab-icon { font-size: 24px; margin-bottom: 4px; }
.ab-name { font-size: 14px; font-weight: 700; color: var(--text); }
.ab-desc { font-size: 10px; color: var(--text-secondary); margin-top: 4px; line-height: 1.4; }
.feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.feat { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; font-size: 12px; font-weight: 500; color: var(--text); }
</style>
