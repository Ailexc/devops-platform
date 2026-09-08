<template>
  <div class="interview-bank">
    <PageHeader title="面试题库" desc="沉淀面试叙事要点：系统设计题 / 技术深挖 / 行为叙事（内容规划中）" />

    <div class="panel coming">
      <div class="coming-icon">🚧</div>
      <div class="coming-title">面试题库 · 建设中</div>
      <div class="coming-desc">
        该模块将沉淀本系统相关的面试准备素材：<br>
        · 系统设计题（如何设计一个权限中心 / 网关 PEP vs SDK 接入）<br>
        · 技术深挖（Casbin vs OpenFGA、决策缓存一致性、OAuth2 CC 流程）<br>
        · 项目叙事（以 STAR 方式组织项目经历与踩坑）
      </div>
      <div class="coming-tag">后续迭代预留</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
</script>

<style scoped>
.interview-bank { padding: 0 24px 40px; }
.panel { border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); padding: 60px 24px; }
.coming { display: flex; flex-direction: column; align-items: center; text-align: center; }
.coming-icon { font-size: 48px; margin-bottom: 14px; }
.coming-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 10px; }
.coming-desc { font-size: 13px; color: var(--text-secondary); line-height: 2; margin-bottom: 20px; }
.coming-tag { font-size: 12px; padding: 4px 14px; border-radius: 16px; background: var(--warning-bg); color: var(--warning); font-weight: 600; }
</style>
