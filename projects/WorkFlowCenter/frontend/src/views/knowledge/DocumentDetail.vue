<template>
  <div class="doc-detail">
    <div class="page-header">
      <div class="page-header-left">
        <el-button class="back-btn" circle @click="goBack"><el-icon><ArrowLeft /></el-icon></el-button>
        <div>
          <h1>{{ doc.title || '文档详情' }}</h1>
          <p class="page-header-desc">
            <el-tag size="small" effect="plain">{{ doc.category || '系统文档' }}</el-tag>
            <span class="doc-meta">左侧为本文目录，点击可快速跳转</span>
          </p>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="detail-body">
      <template v-if="doc.title">
        <!-- 左侧：当前文章目录 -->
        <aside class="doc-toc">
          <div class="toc-title">{{ doc.title }}</div>
          <div class="toc-sub">目录</div>
          <div
            v-for="item in toc"
            :key="item.id"
            class="toc-item"
            :class="['toc-level--' + item.level, { 'is-active': item.id === activeHeading }]"
            @click="scrollTo(item)"
          >
            {{ item.text }}
          </div>
          <div class="toc-back" @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回文档列表</div>
        </aside>

        <!-- 右侧：文档正文 -->
        <article class="doc-content">
          <div class="doc-article" v-html="doc.content"></div>
          <div class="doc-footer">
            <span>— 系统知识库 · {{ doc.title }} —</span>
          </div>
        </article>
      </template>
      <el-empty v-else-if="!loading" description="未找到该文档" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getDoc } from '@/api/modules/knowledge'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const doc = ref({})
const toc = ref([])
const activeHeading = ref('')
let headingsEl = []

const goBack = () => router.back()

// 页面实际滚动容器是 .app-main（非 window）
const getScroller = () => document.querySelector('.app-main') || window

// 从渲染后的正文提取标题，构建当前文章目录
const buildToc = async () => {
  await nextTick()
  const article = document.querySelector('.doc-article')
  if (!article) return
  const nodes = article.querySelectorAll('h2, h3')
  toc.value = []
  headingsEl = []
  nodes.forEach((el, i) => {
    const id = `sec-${i}`
    el.id = id
    el.setAttribute('data-toc', '1')
    toc.value.push({
      id,
      text: el.textContent.trim(),
      level: el.tagName === 'H2' ? 2 : 3
    })
    headingsEl.push(el)
  })
}

const scrollTo = (item) => {
  const el = document.getElementById(item.id)
  const scroller = getScroller()
  if (el && scroller) {
    activeHeading.value = item.id
    const top = el.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop - 90
    scroller.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
  }
}

const onScroll = () => {
  if (!headingsEl.length) return
  const scroller = getScroller()
  const containerTop = scroller.getBoundingClientRect().top
  const pos = 90
  let current = ''
  for (const el of headingsEl) {
    if (el.getBoundingClientRect().top - containerTop <= pos) current = el.id
    else break
  }
  if (!current) {
    // 页首：所有标题都在下方 → 高亮第一节；已滚到底 → 高亮最后一节
    const atBottom = scroller.scrollTop >= scroller.scrollHeight - scroller.clientHeight - 10
    current = atBottom ? headingsEl[headingsEl.length - 1].id : headingsEl[0].id
  }
  activeHeading.value = current
}

const fetchDoc = async () => {
  loading.value = true
  try {
    const response = await getDoc(route.params.key)
    doc.value = response?.data ?? response ?? {}
    await buildToc()
    onScroll() // 初始即高亮当前章节
  } catch (error) {
    console.error('获取文档失败:', error)
    ElMessage.error('获取文档失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDoc()
  const scroller = getScroller()
  scroller.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  const scroller = getScroller()
  scroller.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.doc-detail { padding: 24px; background: #f7f8fa; min-height: 100%; }
.page-header { max-width: 1160px; margin: 0 auto 18px; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.back-btn { flex-shrink: 0; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; color: #1d2129; }
.page-header-desc { margin: 0; display: flex; align-items: center; gap: 10px; }
.doc-meta { font-size: 12px; color: #c9cdd4; }

.detail-body { max-width: 1160px; margin: 0 auto; display: flex; gap: 18px; align-items: flex-start; }

/* 左侧：当前文章目录 */
.doc-toc { width: 230px; flex-shrink: 0; background: #fff; border: 1px solid #e5e6eb; border-radius: 12px; padding: 16px 14px; position: sticky; top: 20px; max-height: calc(100vh - 120px); overflow: auto; }
.toc-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 2px; word-break: break-all; }
.toc-sub { font-size: 11px; color: #86909c; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #f2f3f5; }
.toc-item { padding: 6px 10px; border-radius: 6px; cursor: pointer; color: #4e5969; font-size: 13px; line-height: 1.5; transition: background .15s; }
.toc-item:hover { background: #f7f8fa; }
.toc-item.is-active { background: #ecf5ff; color: #165dff; font-weight: 600; }
.toc-level--2 { padding-left: 10px; }
.toc-level--3 { padding-left: 22px; font-size: 12px; color: #86909c; }
.toc-back { margin-top: 14px; padding-top: 12px; border-top: 1px solid #f2f3f5; display: flex; align-items: center; gap: 4px; font-size: 13px; color: #165dff; cursor: pointer; }
.toc-back:hover { opacity: .8; }

/* 右侧正文 */
.doc-content { flex: 1; min-width: 0; background: #fff; border: 1px solid #e5e6eb; border-radius: 12px; padding: 34px 44px; }
.doc-article { font-size: 15px; color: #2f3542; line-height: 1.85; }
.doc-article :deep(h2), .doc-article :deep(h3) { scroll-margin-top: 90px; }
.doc-article :deep(h1) { font-size: 26px; color: #1d2129; margin: 0 0 16px; padding-bottom: 12px; border-bottom: 2px solid #f0f1f3; }
.doc-article :deep(h2) { font-size: 19px; color: #1d2129; margin: 30px 0 12px; padding-left: 10px; border-left: 4px solid #409eff; }
.doc-article :deep(h3) { font-size: 16px; color: #1d2129; margin: 22px 0 8px; }
.doc-article :deep(p) { margin: 0 0 12px; }
.doc-article :deep(ul), .doc-article :deep(ol) { margin: 0 0 14px; padding-left: 22px; }
.doc-article :deep(li) { margin-bottom: 6px; }
.doc-article :deep(strong) { color: #1d2129; }
.doc-article :deep(code) { background: #f2f3f5; color: #c0392b; border-radius: 4px; padding: 1px 6px; font-size: 13px; font-family: ui-monospace, monospace; }
.doc-article :deep(pre) { background: #1d2129; color: #e8eaed; border-radius: 8px; padding: 14px 16px; overflow: auto; font-size: 13px; line-height: 1.7; margin: 0 0 14px; font-family: ui-monospace, monospace; }
.doc-article :deep(pre code) { background: transparent; color: inherit; padding: 0; font-size: inherit; }
.doc-article :deep(table) { width: 100%; border-collapse: collapse; margin: 0 0 16px; font-size: 14px; }
.doc-article :deep(th), .doc-article :deep(td) { border: 1px solid #e5e6eb; padding: 8px 12px; text-align: left; }
.doc-article :deep(th) { background: #fafbfc; color: #4e5969; font-weight: 600; }
.doc-article :deep(tr):nth-child(even) { background: #fafbfc; }
.doc-article :deep(blockquote) { border-left: 3px solid #409eff; background: #f7faff; margin: 0 0 14px; padding: 8px 14px; color: #4e5969; }
.doc-footer { margin-top: 34px; padding-top: 16px; border-top: 1px dashed #e5e6eb; text-align: center; color: #c9cdd4; font-size: 12px; }
</style>
