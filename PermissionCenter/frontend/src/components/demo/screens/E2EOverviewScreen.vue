<template>
  <div class="mock-screen overview-screen">
    <div class="overview-content">
      <div class="celebrate-icon">🎯</div>
      <h2 class="overview-title">端到端完整链路</h2>
      <p class="overview-sub">从应用注册到权限生效，系统核心能力一览</p>

      <div class="chain-flow">
        <div class="chain-item blue">
          <div class="ci-num">01</div>
          <div class="ci-body">
            <div class="ci-name">注册应用</div>
            <div class="ci-desc">Owner 创建应用，声明身份</div>
          </div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-item violet">
          <div class="ci-num">02</div>
          <div class="ci-body">
            <div class="ci-name">发布能力</div>
            <div class="ci-desc">声明接口 + 预设 + 上架审批</div>
          </div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-item green">
          <div class="ci-num">03</div>
          <div class="ci-body">
            <div class="ci-name">申请能力</div>
            <div class="ci-desc">市场浏览 + 选主体 + 数据范围</div>
          </div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-item amber">
          <div class="ci-num">04</div>
          <div class="ci-body">
            <div class="ci-name">审批授权</div>
            <div class="ci-desc">多级审批 + SoD + 策略自动创建</div>
          </div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-item cyan">
          <div class="ci-num">05</div>
          <div class="ci-body">
            <div class="ci-name">网关鉴权</div>
            <div class="ci-desc">Casbin + OpenFGA 双引擎实时校验</div>
          </div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-item red">
          <div class="ci-num">06</div>
          <div class="ci-body">
            <div class="ci-name">审计追踪</div>
            <div class="ci-desc">TraceID 贯穿，全链路溯源</div>
          </div>
        </div>
      </div>

      <div class="feature-grid">
        <div class="feat"><span>📦</span><span>能力包声明式管理：接口 + 数据模型 + 预设</span></div>
        <div class="feat"><span>🏪</span><span>市场化申请：浏览 → 选预设 → 选主体 → 数据范围</span></div>
        <div class="feat"><span>🔒</span><span>审批即策略：审批通过自动创建策略，无手动配置</span></div>
        <div class="feat"><span>🌐</span><span>实时鉴权：网关双引擎，读允许/写拒绝即时生效</span></div>
        <div class="feat"><span>📊</span><span>全链路可观测：从请求到决策，TraceID 完整溯源</span></div>
        <div class="feat"><span>🔄</span><span>可回收：下架/回收即时删除策略，权限立即失效</span></div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--brand-soft) 0%, var(--bg) 40%, var(--success-bg) 100%); }
.overview-content { text-align: center; max-width: 58%; }
.celebrate-icon { font-size: 40px; margin-bottom: 6px; }
.overview-title { font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.overview-sub { font-size: 12px; color: var(--text-secondary); margin-bottom: 16px; }
.chain-flow { display: flex; align-items: center; justify-content: center; gap: 3px; margin-bottom: 16px; flex-wrap: wrap; }
.chain-item { padding: 8px 8px; border-radius: 8px; text-align: center; min-width: 72px; }
.chain-item.blue { background: rgba(47,111,237,0.1); border: 1px solid var(--brand); }
.chain-item.violet { background: rgba(124,58,237,0.1); border: 1px solid var(--purple); }
.chain-item.green { background: rgba(22,163,74,0.1); border: 1px solid var(--success); }
.chain-item.amber { background: rgba(217,119,6,0.1); border: 1px solid var(--warning); }
.chain-item.cyan { background: rgba(8,145,178,0.1); border: 1px solid var(--info); }
.chain-item.red { background: rgba(220,38,38,0.1); border: 1px solid var(--danger); }
.ci-num { font-size: 10px; font-weight: 700; color: var(--text-tertiary); margin-bottom: 2px; }
.ci-name { font-size: 11px; font-weight: 600; color: var(--text); }
.ci-desc { font-size: 8px; color: var(--text-secondary); line-height: 1.3; }
.chain-arrow { font-size: 12px; color: var(--text-tertiary); }
.feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }
.feat { display: flex; align-items: center; gap: 5px; padding: 5px 8px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 5px; font-size: 10px; color: var(--text); }
</style>
