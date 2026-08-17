<template>
  <div class="docs-page">
    <!-- 文档列表 -->
    <div v-if="!activeDoc">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <div>正在加载文档列表...</div>
      </div>
      <div v-else-if="loadError" style="text-align:center;padding:12px;font-size:11px;color:var(--coral);border:1px solid rgba(239,68,68,.2);border-radius:8px;background:rgba(239,68,68,.05)">⚠️ {{ loadError }}</div>
      <div v-else-if="docs.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">暂无文档，请将 HTML 文件放入 /app/docs/ 目录</div>
      </div>

      <div v-else class="doc-grid">
        <div v-for="(doc, i) in docs" :key="doc.filename" class="doc-card" @click="openDoc(doc)">
          <div class="dc-icon">📄</div>
          <div class="dc-info">
            <div class="dc-title">{{ doc.title }}</div>
            <div class="dc-meta">
              <span class="dc-size">{{ doc.size_human }}</span>
              <span class="dc-date">{{ doc.modified }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 文档内容 -->
    <div v-else class="doc-viewer">
      <div class="dv-header">
        <button class="btn-back" @click="closeDoc">← 返回文档列表</button>
        <span class="dv-title">{{ activeDoc.title }}</span>
        <span class="dv-meta">{{ activeDoc.filename }} · {{ activeDoc.size_human }}</span>
      </div>
      <iframe ref="docFrame" class="dv-iframe" :srcdoc="docContent" sandbox="allow-same-origin allow-scripts"></iframe>
    </div>
  </div>
</template>

<script>
import { fetchDocList, fetchDocContent } from '../api/index.js'

export default {
  name: 'SystemDocs',
  data() {
    return {
      loading: true,
      loadError: '',
      docs: [],
      activeDoc: null,
      docContent: '',
    }
  },
  async mounted() {
    await this.loadDocs()
  },
  methods: {
    async loadDocs() {
      this.loading = true
      this.loadError = ''
      try {
        const res = await fetchDocList()
        this.docs = res.data?.docs || []
      } catch (e) {
        console.error('加载文档列表失败:', e)
        this.loadError = '加载文档列表失败'
      } finally {
        this.loading = false
      }
    },
    async openDoc(doc) {
      this.activeDoc = doc
      this.docContent = ''
      try {
        const res = await fetchDocContent(doc.filename)
        this.docContent = res.data?.content || ''
      } catch (e) {
        console.error('加载文档内容失败:', e)
        this.docContent = `<html><body style="text-align:center;padding:40px;font-family:sans-serif;color:#c0392b">❌ 加载文档内容失败: ${e.message || e}</body></html>`
      }
    },
    closeDoc() {
      this.activeDoc = null
      this.docContent = ''
    },
  },
}
</script>

<style scoped>
.docs-page { padding: 0; }

/* Header */
.fl {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: white;
}
.fl-title { font-size: 14px; font-weight: 700; color: white; }
.fl-count {
  font-size: 11px;
  color: rgba(255,255,255,.8);
  margin-left: auto;
  background: rgba(255,255,255,.2);
  padding: 4px 10px;
  border-radius: 12px;
}

/* Card grid */
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.doc-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  transition: all .2s ease;
  position: relative;
  overflow: hidden;
}
.doc-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--purple));
  opacity: 0;
  transition: opacity .2s;
}
.doc-card:hover {
  border-color: var(--blue);
  box-shadow: 0 4px 12px rgba(67,97,238,.15);
  transform: translateY(-2px);
}
.doc-card:hover::before { opacity: 1; }

.dc-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.dc-info { flex: 1; min-width: 0; }
.dc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.dc-meta {
  font-size: 11px;
  color: var(--t2);
  display: flex;
  align-items: center;
  gap: 8px;
}
.dc-meta span {
  display: flex;
  align-items: center;
  gap: 3px;
}
.dc-size {
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.dc-date {
  color: #999;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--t2);
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-text { font-size: 14px; }

/* Document viewer */
.doc-viewer {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,.05);
}
.dv-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}
.dv-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.dv-meta {
  font-size: 11px;
  color: var(--t2);
  margin-left: auto;
}
.dv-iframe {
  width: 100%;
  height: calc(100vh - 180px);
  border: none;
  background: #fff;
}

/* Back button */
.btn-back {
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all .15s;
  color: var(--text);
}
.btn-back:hover {
  background: var(--blue);
  color: white;
  border-color: var(--blue);
}

/* Loading */
.loading-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--t2);
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e0e0;
  border-top-color: var(--blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
