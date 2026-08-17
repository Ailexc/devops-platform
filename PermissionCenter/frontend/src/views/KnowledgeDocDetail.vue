<template>
  <div class="doc-detail">
    <!-- 顶栏：返回 + 标题 + 上一篇/下一篇 -->
    <div class="dd-head">
      <button class="back-btn" @click="router.push('/knowledge/docs')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        返回文档列表
      </button>
      <div class="dd-head-info">
        <span class="dd-cat">{{ doc?.category || '' }}</span>
        <h1 class="dd-title">{{ doc?.title || '加载中…' }}</h1>
      </div>
      <div class="dd-head-right">
        <button class="nav-doc" v-if="prevDoc" @click="router.push(`/knowledge/docs/${prevDoc.id}`)">← {{ prevDoc.title }}</button>
        <button class="nav-doc" v-if="nextDoc" @click="router.push(`/knowledge/docs/${nextDoc.id}`)">{{ nextDoc.title }} →</button>
      </div>
    </div>

    <div class="dd-body">
      <!-- 左：当前文章目录（自动生成，可点击跳转） -->
      <aside class="dd-toc">
        <div class="toc-head">📑 本文目录</div>
        <div class="toc-body">
          <div
            v-for="t in toc"
            :key="t.id"
            class="toc-item"
            :class="{ active: activeId === t.id, ['lv-' + t.level]: true }"
            :title="t.text"
            @click="scrollTo(t.id)"
          >{{ t.text }}</div>
          <div v-if="!toc.length" class="toc-empty">本文暂无目录</div>
        </div>
      </aside>

      <!-- 右：文章内容（iframe 隔离样式） -->
      <main class="dd-main">
        <iframe ref="frameEl" class="dd-frame" :srcdoc="docHtml" @load="onFrameLoad" title="文档内容"></iframe>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()

const doc = ref<any>(null)
const toc = ref<{ id: string; text: string; level: number }[]>([])
const docHtml = ref('')
const activeId = ref('')
const frameEl = ref<HTMLIFrameElement | null>(null)
const allDocs = ref<any[]>([])

const idx = computed(() => allDocs.value.findIndex(d => d.id === route.params.id))
const prevDoc = computed(() => idx.value > 0 ? allDocs.value[idx.value - 1] : null)
const nextDoc = computed(() => idx.value >= 0 && idx.value < allDocs.value.length - 1 ? allDocs.value[idx.value + 1] : null)

// 解析 HTML：给标题加 id + 提取目录 + 注入高亮样式
function processHtml(html: string) {
  const docEl = new DOMParser().parseFromString(html, 'text/html')
  const list: { id: string; text: string; level: number }[] = []
  let n = 0
  docEl.querySelectorAll('h1, h2, h3').forEach(h => {
    const id = 'sec-' + (++n)
    h.id = id
    list.push({ id, text: (h.textContent || '').trim(), level: Number(h.tagName[1]) })
  })
  const style = docEl.createElement('style')
  style.textContent = '.toc-target { background: rgba(217,119,6,.14) !important; border-left: 4px solid #d97706; padding-left: 6px; scroll-margin-top: 8px; }'
  docEl.head.appendChild(style)
  return { html: '<!DOCTYPE html>' + docEl.documentElement.outerHTML, toc: list }
}

async function load() {
  const id = String(route.params.id || '')
  try {
    if (!allDocs.value.length) {
      const d: any = await api.knowledgeDocs()
      allDocs.value = d.items || []
    }
    const meta = allDocs.value.find(x => x.id === id)
    const d: any = await api.knowledgeDoc(id)
    doc.value = { id, title: meta?.title || '', category: meta?.category || '', summary: meta?.summary || '', html: d.html || '' }
    const r = processHtml(doc.value.html)
    docHtml.value = r.html
    toc.value = r.toc
    activeId.value = r.toc[0]?.id || ''
  } catch (e: any) {
    ElMessage.error(e.message || '加载文档失败')
  }
}

function onFrameLoad() {
  const d = frameEl.value?.contentDocument
  if (!d) return
  d.addEventListener('scroll', onFrameScroll, { passive: true })
}

function onFrameScroll() {
  const d = frameEl.value?.contentDocument
  if (!d) return
  const y = d.scrollingElement?.scrollTop || 0
  let current = toc.value[0]?.id || ''
  for (const t of toc.value) {
    const el = d.getElementById(t.id)
    if (el && el.offsetTop <= y + 16) current = t.id
  }
  activeId.value = current
}

function scrollTo(id: string) {
  const d = frameEl.value?.contentDocument
  const el = d?.getElementById(id)
  if (!el) return
  d?.querySelectorAll('h1,h2,h3').forEach(h => h.classList.remove('toc-target'))
  el.classList.add('toc-target')
  el.scrollIntoView({ behavior: 'auto', block: 'start' })
  activeId.value = id
}

watch(() => route.params.id, () => { load() })

onMounted(load)
onUnmounted(() => {
  const d = frameEl.value?.contentDocument
  if (d) d.removeEventListener('scroll', onFrameScroll)
})
</script>

<style scoped>
.doc-detail { padding: 0 24px 0; display: flex; flex-direction: column; height: calc(100vh - 56px); }
.dd-head { display: flex; align-items: center; gap: 16px; padding: 14px 0 12px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
.back-btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; flex-shrink: 0; }
.back-btn:hover { border-color: var(--brand); color: var(--brand); }
.dd-head-info { flex: 1; min-width: 0; }
.dd-cat { display: inline-block; font-size: 11px; font-weight: 600; padding: 1px 10px; border-radius: 10px; background: var(--brand-soft); color: var(--brand); margin-bottom: 2px; }
.dd-title { font-size: 17px; font-weight: 700; color: var(--text); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dd-head-right { display: flex; gap: 8px; flex-shrink: 0; }
.nav-doc { padding: 6px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text-secondary); font-size: 12px; cursor: pointer; transition: all 0.15s; max-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-doc:hover { border-color: var(--brand); color: var(--brand); }

.dd-body { display: flex; gap: 16px; flex: 1; min-height: 0; padding-top: 14px; }
.dd-toc { width: 260px; flex-shrink: 0; border: 1px solid var(--border); border-radius: 12px; background: var(--bg-card); display: flex; flex-direction: column; overflow: hidden; }
.toc-head { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; font-weight: 600; color: var(--text); flex-shrink: 0; }
.toc-body { flex: 1; overflow: auto; padding: 8px; }
.toc-item { padding: 6px 10px; border-radius: 6px; font-size: 12px; color: var(--text-secondary); cursor: pointer; line-height: 1.4; transition: all 0.12s; }
.toc-item:hover { background: var(--bg-secondary); color: var(--text); }
.toc-item.active { background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.toc-item.lv-1 { font-weight: 600; color: var(--text); padding-left: 10px; }
.toc-item.lv-2 { padding-left: 24px; }
.toc-item.lv-3 { padding-left: 38px; font-size: 11px; }
.toc-empty { padding: 20px; text-align: center; color: var(--text-tertiary); font-size: 12px; }

.dd-main { flex: 1; min-width: 0; border: 1px solid var(--border); border-radius: 12px; background: #fff; overflow: hidden; }
.dd-frame { width: 100%; height: 100%; border: none; background: #fff; }
</style>
