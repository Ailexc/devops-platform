<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="interview-page">
    <div class="page-header fade-in">
      <div class="header-content">
        <div class="header-icon">🎯</div>
        <div>
          <h1 class="page-title">面试题库</h1>
          <p class="page-subtitle">面向面试的架构 / 技术 / 设计问题与要点题库</p>
        </div>
      </div>
    </div>

    <div class="placeholder-card fade-in delay-1">
      <span class="placeholder-icon">🚧</span>
      <h2>面试题库 · 建设中</h2>
      <p>该模块已预留，后续将整理项目涉及的面试题与回答要点：</p>
      <ul class="preview-list">
        <li>🏗️ 架构类：四层架构 / CMDB 唯一数据源 / 工单闭环</li>
        <li>⚙️ 技术类：多态资源建模 / 云适配层 / 规则引擎注册表</li>
        <li>💡 设计类：三角关系标签主线 / 数据权限后端强制 / 异步最终一致</li>
        <li>💰 成本类：规则引擎 / 成本分摊 / 预算工单闭环</li>
      </ul>
      <button class="btn-back" @click="router.push('/knowledge/docs')">
        ← 先看看系统文档
      </button>
    </div>
  </div>
</template>

<style scoped>
.interview-page {
  padding: 20px 24px;
  background: var(--cm-bg, #f6f7fb);
  min-height: 100%;
}
.page-header { margin-bottom: 20px; }
.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f59e0b, #f97316);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--cm-text, #1a1a2e);
  margin: 0;
}
.page-subtitle {
  font-size: 13px;
  color: var(--cm-text-secondary, #64748b);
  margin: 2px 0 0;
}
.placeholder-card {
  max-width: 720px;
  background: #fff;
  border: 1px solid var(--cm-border, #eef0f4);
  border-radius: 14px;
  padding: 48px;
  text-align: center;
}
.placeholder-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}
.placeholder-card h2 {
  font-size: 18px;
  font-weight: 700;
  color: var(--cm-text, #1a1a2e);
  margin: 0 0 8px;
}
.placeholder-card p {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 20px;
}
.preview-list {
  text-align: left;
  display: inline-block;
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  font-size: 13px;
  color: #475569;
  line-height: 2.2;
}
.btn-back {
  padding: 10px 20px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
  transition: all 0.2s;
}
.btn-back:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
}
</style>
