<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi, type DocCategoryNode, type DocSummary } from '@/api'

const router = useRouter()
const loading = ref(false)
const categories = ref<DocCategoryNode[]>([])
const selectedCat = ref<number | null>(null)

const allDocs = computed<DocSummary[]>(() =>
  categories.value.flatMap(c => c.docs),
)

const filteredDocs = computed(() => {
  if (selectedCat.value == null) return allDocs.value
  const cat = categories.value.find(c => c.id === selectedCat.value)
  return cat ? cat.docs : []
})

const selectedName = computed(() => {
  if (selectedCat.value == null) return '全部文档'
  return categories.value.find(c => c.id === selectedCat.value)?.name || ''
})

async function load() {
  loading.value = true
  try {
    const res = await knowledgeApi.categories()
    categories.value = res.data.results
  } finally {
    loading.value = false
  }
}

function openDoc(doc: DocSummary) {
  router.push(`/knowledge/docs/${doc.slug}`)
}

onMounted(load)
</script>

<template>
  <div class="docs-page">
    <!-- 页面标题 -->
    <div class="page-header fade-in">
      <div class="header-content">
        <div class="header-icon">📚</div>
        <div>
          <h1 class="page-title">系统文档</h1>
          <p class="page-subtitle">项目架构 · 技术选型 · 核心机制 · 部署运维的复盘总结</p>
        </div>
        <div class="header-stats" v-if="!loading">
          <span class="stat-chip">{{ categories.length }} 个分类</span>
          <span class="stat-chip purple">{{ allDocs.length }} 篇文档</span>
        </div>
      </div>
    </div>

    <div class="docs-body fade-in delay-1">
      <!-- 左侧：分类目录 -->
      <aside class="doc-sidebar">
        <div class="sidebar-title">文档目录</div>
        <div
          class="cat-item"
          :class="{ active: selectedCat == null }"
          @click="selectedCat = null"
        >
          <span class="cat-icon">🗂️</span>
          <span class="cat-name">全部文档</span>
          <span class="cat-count">{{ allDocs.length }}</span>
        </div>
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="cat-item"
          :class="{ active: selectedCat === cat.id }"
          @click="selectedCat = cat.id"
        >
          <span class="cat-icon">{{ cat.icon }}</span>
          <span class="cat-name">{{ cat.name }}</span>
          <span class="cat-count">{{ cat.doc_count }}</span>
        </div>
      </aside>

      <!-- 右侧：文档列表 -->
      <main class="doc-content">
        <div class="content-header">
          <h2>{{ selectedName }}</h2>
          <span class="content-hint">点击文档卡片查看详情</span>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>加载中...</span>
        </div>

        <div v-else-if="filteredDocs.length === 0" class="empty-state">
          <span class="empty-icon">📄</span>
          <p>该分类暂无文档</p>
        </div>

        <div v-else class="doc-grid">
          <div
            v-for="doc in filteredDocs"
            :key="doc.id"
            class="doc-card"
            @click="openDoc(doc)"
          >
            <div class="doc-card-head">
              <span class="doc-type">{{ doc.category_name }}</span>
              <span class="doc-arrow">→</span>
            </div>
            <h3 class="doc-title">{{ doc.title }}</h3>
            <p class="doc-summary">{{ doc.summary }}</p>
            <div class="doc-tags" v-if="doc.tags">
              <span v-for="t in doc.tags.split(',')" :key="t" class="doc-tag">{{ t.trim() }}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.docs-page {
  padding: 20px 24px;
  background: var(--cm-bg, #f6f7fb);
  min-height: 100%;
}
.page-header {
  margin-bottom: 16px;
}
.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
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
.header-stats {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.stat-chip {
  padding: 4px 12px;
  background: #fff;
  border: 1px solid var(--cm-border, #e2e8f0);
  border-radius: 999px;
  font-size: 12px;
  color: #475569;
}
.stat-chip.purple {
  background: #faf5ff;
  border-color: #e9d5ff;
  color: #7c3aed;
  font-weight: 600;
}
.docs-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.doc-sidebar {
  width: 220px;
  background: #fff;
  border: 1px solid var(--cm-border, #eef0f4);
  border-radius: 12px;
  padding: 12px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
}
.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  padding: 4px 8px 10px;
}
.cat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
  color: #334155;
}
.cat-item:hover {
  background: var(--cm-hover, #f6f7fb);
}
.cat-item.active {
  background: #faf5ff;
  color: #7c3aed;
  font-weight: 600;
}
.cat-icon { font-size: 15px; }
.cat-name { flex: 1; }
.cat-count {
  font-size: 11px;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 999px;
  padding: 1px 8px;
}
.cat-item.active .cat-count {
  background: #7c3aed;
  color: #fff;
}
.doc-content {
  flex: 1;
  min-width: 0;
}
.content-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}
.content-header h2 {
  font-size: 16px;
  font-weight: 700;
  color: var(--cm-text, #1a1a2e);
  margin: 0;
}
.content-hint {
  font-size: 12px;
  color: #94a3b8;
}
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}
.doc-card {
  background: #fff;
  border: 1px solid var(--cm-border, #eef0f4);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.doc-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.1);
  border-color: #e9d5ff;
}
.doc-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.doc-type {
  font-size: 11px;
  color: #7c3aed;
  background: #faf5ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.doc-arrow {
  color: #cbd5e1;
  font-size: 14px;
  transition: transform 0.2s;
}
.doc-card:hover .doc-arrow {
  transform: translateX(3px);
  color: #7c3aed;
}
.doc-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--cm-text, #1a1a2e);
  margin: 0 0 6px;
}
.doc-summary {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.doc-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.doc-tag {
  font-size: 11px;
  color: #475569;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}
.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  padding: 60px 0;
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
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #94a3b8;
}
.empty-icon { font-size: 32px; display: block; margin-bottom: 8px; }
</style>
