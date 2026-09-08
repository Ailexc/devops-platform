<template>
  <div class="knowledge-docs">
    <PageHeader title="系统文档" desc="项目复盘与总结：架构 / 技术点 / 设计，点击卡片进入阅读">
      <template #actions>
        <span class="doc-count" v-if="items.length">📚 {{ items.length }} 篇文档 · {{ categories.length }} 个分类</span>
      </template>
    </PageHeader>

    <!-- 分类筛选 -->
    <div class="filter-bar" v-if="categories.length">
      <button class="filter-chip" :class="{ active: filter === 'all' }" @click="filter = 'all'">全部 <span class="fc-num">{{ items.length }}</span></button>
      <button
        v-for="cat in categories"
        :key="cat"
        class="filter-chip"
        :class="{ active: filter === cat }"
        @click="filter = cat"
      >{{ cat }} <span class="fc-num">{{ items.filter(d => d.category === cat).length }}</span></button>
    </div>

    <!-- 卡片网格 -->
    <div v-if="filtered.length" class="card-grid">
      <div
        v-for="(d, i) in filtered"
        :key="d.id"
        class="doc-card"
        :style="{ '--accent': accentOf(d.category) }"
        @click="router.push(`/knowledge/docs/${d.id}`)"
      >
        <div class="dc-top">
          <span class="dc-index">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="dc-cat">{{ d.category }}</span>
        </div>
        <div class="dc-icon">{{ iconOf(d.category) }}</div>
        <div class="dc-title">{{ d.title }}</div>
        <div class="dc-summary">{{ d.summary }}</div>
        <div class="dc-foot">
          <span class="dc-read">阅读 →</span>
          <span class="dc-id mono">{{ d.id }}</span>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">该分类下暂无文档</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const items = ref<any[]>([])
const categories = ref<string[]>([])
const filter = ref('all')

const filtered = computed(() =>
  filter.value === 'all' ? items.value : items.value.filter(d => d.category === filter.value)
)

const catMeta: Record<string, { icon: string; accent: string }> = {
  '架构设计': { icon: '🏗️', accent: '#2f6fed' },
  '核心技术': { icon: '⚡', accent: '#16a34a' },
  '业务设计': { icon: '📦', accent: '#d97706' },
  '工程实践': { icon: '🔍', accent: '#0891b2' },
}

function iconOf(cat: string) { return catMeta[cat]?.icon || '📄' }
function accentOf(cat: string) { return catMeta[cat]?.accent || '#6b7280' }

async function load() {
  try {
    const d: any = await api.knowledgeDocs()
    items.value = d.items || []
    categories.value = d.categories || []
  } catch (e: any) {
    ElMessage.error(e.message || '加载文档目录失败')
  }
}

onMounted(load)
</script>

<style scoped>
.knowledge-docs { padding: 0 24px 40px; }
.doc-count { font-size: 12px; color: var(--text-tertiary); }
.filter-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.filter-chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border: 1px solid var(--border); border-radius: 18px; background: var(--bg-card); color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.filter-chip:hover { border-color: var(--brand); color: var(--brand); }
.filter-chip.active { background: var(--brand); color: #fff; border-color: var(--brand); }
.fc-num { font-size: 11px; opacity: 0.75; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.doc-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; position: relative; overflow: hidden; }
.doc-card:hover { transform: translateY(-3px); border-color: var(--accent); box-shadow: 0 8px 24px rgba(0,0,0,.08); }
.doc-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent); opacity: 0; transition: opacity .2s; }
.doc-card:hover::before { opacity: 1; }
.dc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.dc-index { font-size: 12px; font-weight: 700; color: var(--text-tertiary); font-family: var(--font-mono); }
.dc-cat { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 12px; color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }
.dc-icon { font-size: 34px; margin-bottom: 12px; }
.dc-title { font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 8px; line-height: 1.4; }
.dc-summary { font-size: 12px; color: var(--text-secondary); line-height: 1.6; flex: 1; }
.dc-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); }
.dc-read { font-size: 12px; font-weight: 600; color: var(--accent); }
.dc-id { font-size: 11px; color: var(--text-tertiary); font-family: var(--font-mono); }
.empty-state { padding: 60px; text-align: center; color: var(--text-tertiary); font-size: 14px; }
</style>
