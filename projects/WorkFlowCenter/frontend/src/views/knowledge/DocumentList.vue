<template>
  <div class="doc-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><Reading /></el-icon></div>
        <div>
          <h1>系统文档</h1>
          <p class="page-header-desc">系统架构、技术栈、核心设计与复盘总结，一文读懂整个平台</p>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="doc-body">
      <!-- 按分类分组 -->
      <div v-for="group in groups" :key="group.category" class="doc-group">
        <div class="doc-group__head">
          <span class="doc-group__dot"></span>
          <span class="doc-group__title">{{ group.category }}</span>
          <span class="doc-group__count">{{ group.docs.length }} 篇</span>
        </div>
        <div class="doc-grid">
          <div
            v-for="doc in group.docs"
            :key="doc.id"
            class="doc-card"
            @click="openDoc(doc)"
          >
            <div class="doc-card__icon"><el-icon><component :is="iconOf(doc.icon)" /></el-icon></div>
            <div class="doc-card__main">
              <div class="doc-card__title">{{ doc.title }}</div>
              <div class="doc-card__summary">{{ doc.summary }}</div>
            </div>
            <div class="doc-card__arrow"><el-icon><ArrowRight /></el-icon></div>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && !docs.length" description="暂无系统文档" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Reading, ArrowRight, Connection, Cpu, SetUp, Operation, View, Grid, Finished
} from '@element-plus/icons-vue'
import { getDocs } from '@/api/modules/knowledge'

const router = useRouter()
const loading = ref(false)
const docs = ref([])

const ICONS = {
  Connection, Cpu, SetUp, Operation, View, Grid, Finished
}

const iconOf = (name) => ICONS[name] || Reading

const groups = computed(() => {
  const map = new Map()
  docs.value.forEach(doc => {
    const cat = doc.category || '其他'
    if (!map.has(cat)) map.set(cat, [])
    map.get(cat).push(doc)
  })
  return Array.from(map.entries()).map(([category, docs]) => ({ category, docs }))
})

const openDoc = (doc) => router.push(`/knowledge/docs/${doc.key}`)

const fetchDocs = async () => {
  loading.value = true
  try {
    const response = await getDocs({ page_size: 100 })
    const data = response?.data ?? response
    docs.value = Array.isArray(data) ? data : (data?.documents || [])
  } catch (error) {
    console.error('获取系统文档失败:', error)
    ElMessage.error('获取系统文档失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchDocs)
</script>

<style scoped>
.doc-list { padding: 24px; background: #f7f8fa; min-height: 100%; max-width: 1100px; margin: 0 auto; }
.page-header { margin-bottom: 22px; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.page-header-icon { width: 44px; height: 44px; border-radius: 10px; background: linear-gradient(135deg, #409eff, #2563eb); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.page-header h1 { margin: 0 0 4px; font-size: 22px; color: #1d2129; }
.page-header-desc { margin: 0; font-size: 13px; color: #86909c; }

.doc-body { display: flex; flex-direction: column; gap: 26px; }
.doc-group__head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.doc-group__dot { width: 8px; height: 8px; border-radius: 2px; background: #409eff; }
.doc-group__title { font-size: 16px; font-weight: 600; color: #1d2129; }
.doc-group__count { font-size: 12px; color: #86909c; }

.doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.doc-card { display: flex; align-items: flex-start; gap: 12px; background: #fff; border: 1px solid #e5e6eb; border-radius: 12px; padding: 16px; cursor: pointer; transition: all .2s; }
.doc-card:hover { border-color: #409eff; box-shadow: 0 4px 16px rgba(64,158,255,.14); transform: translateY(-2px); }
.doc-card__icon { width: 40px; height: 40px; border-radius: 8px; background: #ecf5ff; color: #409eff; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.doc-card__main { flex: 1; min-width: 0; }
.doc-card__title { font-size: 15px; font-weight: 600; color: #1d2129; }
.doc-card__summary { font-size: 12px; color: #86909c; line-height: 1.6; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.doc-card__arrow { color: #c9cdd4; margin-top: 10px; flex-shrink: 0; }
</style>
