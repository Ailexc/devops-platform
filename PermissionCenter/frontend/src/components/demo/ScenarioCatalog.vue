<template>
  <div class="catalog">
    <div class="catalog-topbar">
      <button class="back-home" @click="router.push('/')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>
        返回主菜单
      </button>
    </div>
    <div class="catalog-header">
      <h1 class="catalog-title">🎬 系统演示</h1>
      <p class="catalog-desc">像 PPT 一样逐步展示系统能力，6 个场景覆盖核心亮点</p>
      <div class="catalog-stats">
        <span class="stat-pill">📊 {{ totalScenarios }} 个场景</span>
        <span class="stat-pill">📋 {{ totalSteps }} 个步骤</span>
        <span class="stat-pill">⌨️ 键盘快捷键支持</span>
      </div>
    </div>

    <div class="scenario-grid">
      <div
        v-for="(s, idx) in scenarioList"
        :key="s.slug"
        class="scenario-card"
        :style="{ '--accent': s.color }"
        @click="$emit('start', s.slug)"
      >
        <div class="card-number">{{ String(idx + 1).padStart(2, '0') }}</div>
        <div class="card-body">
          <div class="card-title">{{ s.title }}</div>
          <div class="card-desc">{{ s.desc }}</div>
          <div class="card-meta">
            <span>⏱️ {{ s.time }}</span>
            <span>📋 {{ s.steps }} 步</span>
          </div>
        </div>
        <div class="card-action">开始演示 →</div>
      </div>
    </div>

    <div class="catalog-footer">
      <div class="shortcut"><kbd>←</kbd><kbd>→</kbd> 翻页</div>
      <div class="shortcut"><kbd>ESC</kbd> 返回目录</div>
      <div class="shortcut"><kbd>Space</kbd> 下一步</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
defineEmits<{ start: [slug: string] }>()
const router = useRouter()

const scenarioList = [
  { slug: 'arch', title: '系统概览', desc: '六大板块能力介绍：工作台→个人权限→应用管理→打包能力→权限市场→审计观测→架构总结', time: '3 分钟', steps: 7, color: '#dc2626' },  { slug: 'org', title: '个人权限板块', desc: '个人权限 / 组织权限 / 自建组权限三维度解析，权限计算模型与授权来源追溯', time: '3 分钟', steps: 6, color: '#16a34a' },
  { slug: 'e2e', title: '发布与申请', desc: '注册应用→发布能力→申请能力→审批授权→网关鉴权→审计追踪，完整业务链路', time: '3 分钟', steps: 7, color: '#d97706' },
  { slug: 'policy', title: '授权与策略', desc: '策略全生命周期：业务触发→审批生成→网关执行→权限回收，审批即策略', time: '3 分钟', steps: 6, color: '#7c3aed' },
  { slug: 'audit', title: '审计与观测', desc: '链路追踪 / PEP 解析 / 决策日志 + 决策缓存工作台 / 指标面板 / 数据面图谱 / Owner 巡检，全链路可观测', time: '3 分钟', steps: 9, color: '#0891b2' },
  { slug: 'dual', title: '场景演示', desc: '小黄（应用 Owner）发布能力 + 小红（用户）申请权限，双视角沉浸式体验', time: '5 分钟', steps: 17, color: '#2f6fed' },
]

const totalScenarios = scenarioList.length
const totalSteps = scenarioList.reduce((sum, s) => sum + s.steps, 0)
</script>

<style scoped>
.catalog { max-width: 960px; margin: 0 auto; padding: 24px; }
.catalog-topbar { display: flex; justify-content: flex-end; margin-bottom: 8px; }
.back-home { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.back-home:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-soft); }
.catalog-header { text-align: center; margin-bottom: 36px; }
.catalog-title { font-size: 28px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.catalog-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 16px; }
.catalog-stats { display: flex; gap: 12px; justify-content: center; }
.stat-pill { font-size: 12px; padding: 4px 14px; border-radius: 20px; background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 500; }

.scenario-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 32px; }

.scenario-card {
  background: var(--bg-card);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  overflow: hidden;
}
.scenario-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
  opacity: 0;
  transition: opacity 0.2s;
}
.scenario-card:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.scenario-card:hover::before { opacity: 1; }

.card-number { font-size: 32px; font-weight: 800; color: var(--accent); opacity: 0.2; line-height: 1; }
.card-body { flex: 1; }
.card-title { font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.card-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 10px; }
.card-meta { display: flex; gap: 14px; font-size: 11px; color: var(--text-tertiary); }
.card-action {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.2s;
}
.scenario-card:hover .card-action { opacity: 1; }

.catalog-footer {
  display: flex;
  gap: 24px;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.shortcut { font-size: 12px; color: var(--text-tertiary); display: flex; align-items: center; gap: 4px; }
kbd {
  display: inline-block;
  padding: 2px 6px;
  font-size: 11px;
  font-family: var(--font-mono);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
}
</style>
