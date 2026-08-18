<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { knowledgeApi, type DocDetail } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const doc = ref<DocDetail | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await knowledgeApi.detail(route.params.slug as string)
    doc.value = res.data
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/knowledge/docs')
}

onMounted(load)
</script>

<template>
  <div class="doc-detail-page">
    <!-- 页头 -->
    <div class="detail-header fade-in">
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"></path>
        </svg>
      </button>
      <div class="header-info">
        <h1 class="detail-title">{{ doc?.title || '文档详情' }}</h1>
        <p class="detail-subtitle" v-if="doc">
          {{ doc.category_name }} · 更新于 {{ new Date(doc.updated_at).toLocaleDateString() }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading-state fade-in">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="doc" class="doc-wrap fade-in delay-1">
      <!-- 文档头部信息 -->
      <div class="doc-meta">
        <span class="doc-type">{{ doc.category_name }}</span>
        <span v-for="t in (doc.tags || '').split(',')" :key="t" class="doc-tag">{{ t.trim() }}</span>
        <span class="doc-time">🕘 {{ new Date(doc.updated_at).toLocaleDateString('zh-CN') }}</span>
      </div>

      <!-- HTML 正文 -->
      <article class="doc-body" v-html="doc.html_content"></article>
    </div>
  </div>
</template>

<style scoped>
.doc-detail-page {
  padding: 20px 24px 40px;
  background: var(--cm-bg, #f6f7fb);
  min-height: 100%;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.back-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--cm-border, #e2e8f0);
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.15s;
  flex-shrink: 0;
}
.back-btn:hover {
  color: #7c3aed;
  border-color: #e9d5ff;
  background: #faf5ff;
}
.back-btn svg { width: 18px; height: 18px; }
.detail-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--cm-text, #1a1a2e);
  margin: 0;
}
.detail-subtitle {
  font-size: 12px;
  color: #94a3b8;
  margin: 2px 0 0;
}
.doc-wrap {
  background: #fff;
  border: 1px solid var(--cm-border, #eef0f4);
  border-radius: 14px;
  padding: 28px 36px;
  max-width: 900px;
}
.doc-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-bottom: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid #f1f5f9;
}
.doc-type {
  font-size: 12px;
  color: #7c3aed;
  background: #faf5ff;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 600;
}
.doc-tag {
  font-size: 12px;
  color: #475569;
  background: #f1f5f9;
  padding: 3px 10px;
  border-radius: 6px;
}
.doc-time {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
}
.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  padding: 80px 0;
  color: #94a3b8;
}
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e9d5ff;
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>

<!-- HTML 文档正文样式（作用于 v-html 渲染的内容） -->
<style scoped>
.doc-body :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 28px 0 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f3e8ff;
}
.doc-body :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin: 20px 0 8px;
}
.doc-body :deep(p) {
  font-size: 14px;
  color: #475569;
  line-height: 1.8;
  margin: 0 0 10px;
}
.doc-body :deep(ul), .doc-body :deep(ol) {
  margin: 0 0 12px;
  padding-left: 22px;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}
.doc-body :deep(li) {
  margin-bottom: 4px;
}
.doc-body :deep(b), .doc-body :deep(strong) {
  color: #7c3aed;
}
.doc-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0 18px;
  font-size: 13px;
}
.doc-body :deep(th) {
  text-align: left;
  background: #faf5ff;
  color: #4c1d95;
  font-weight: 600;
  padding: 10px 12px;
  border: 1px solid #f0ecff;
}
.doc-body :deep(td) {
  padding: 9px 12px;
  border: 1px solid #eef0f4;
  color: #475569;
}
.doc-body :deep(tr:nth-child(even) td) {
  background: #fafafa;
}
.doc-body :deep(code) {
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
  color: #7c3aed;
  background: #faf5ff;
  padding: 1px 6px;
  border-radius: 4px;
}
.doc-body :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px 18px;
  border-radius: 10px;
  overflow-x: auto;
  font-size: 12.5px;
  line-height: 1.7;
  margin: 12px 0 18px;
}
.doc-body :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}
.doc-body :deep(blockquote) {
  margin: 14px 0;
  padding: 12px 16px;
  background: #faf5ff;
  border-left: 4px solid #7c3aed;
  border-radius: 0 8px 8px 0;
  color: #4c1d95;
  font-size: 14px;
  line-height: 1.7;
}
.doc-body :deep(blockquote b) {
  color: #6d28d9;
}
</style>
