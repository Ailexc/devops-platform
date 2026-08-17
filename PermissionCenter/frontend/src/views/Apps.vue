<template>
  <div class="apps-page">
    <PageHeader title="应用管理" desc="注册应用 → 同步 OpenAPI → 自动生成权限点">
      <template #actions>
        <router-link to="/apps/register" class="btn btn-primary">＋ 注册应用</router-link>
      </template>
    </PageHeader>

    <div class="app-grid">
      <div v-for="row in apps" :key="row.id" class="app-card" @click="selectApp(row)">
        <div class="card-head">
          <div class="card-icon">{{ appIcon(row) }}</div>
          <div class="card-info">
            <div class="card-name">{{ row.name }}</div>
            <div class="card-code mono">{{ row.code }}</div>
          </div>
          <span class="tag" :class="row.type === 1 ? 'tag-blue' : 'tag-cyan'">{{ row.type === 1 ? 'API' : '数据' }}</span>
        </div>
        <div class="card-body">
          <div class="card-stat">
            <span class="stat-label">能力</span>
            <span class="stat-value">{{ capCounts[row.id] || 0 }}</span>
          </div>
          <div class="card-stat">
            <span class="stat-label">策略</span>
            <span class="stat-value">{{ policyCounts[row.id] || 0 }}</span>
          </div>
        </div>
        <div class="card-foot">
          <button class="btn btn-sm" @click.stop="sync(row)" :disabled="syncing">
            {{ syncing ? '同步中...' : '🔄 同步 OpenAPI' }}
          </button>
          <button class="btn btn-sm btn-outline" @click.stop="selectApp(row)">详情 →</button>
        </div>
      </div>
    </div>

    <div v-if="apps.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <div class="empty-text">暂无应用</div>
      <router-link to="/apps/register" class="btn btn-primary">注册第一个应用</router-link>
    </div>


  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const apps = ref<any[]>([])
const syncing = ref(false)
const capCounts = ref<Record<number, number>>({})
const policyCounts = ref<Record<number, number>>({})

function appIcon(a: any) {
  const map: Record<string, string> = { cmdb: '🖥️', itsm: '📋', cloudportal: '☁️', monitor: '📈', 'ops-tool': '🛠️' }
  return map[a.code] || '📦'
}

async function load() {
  const data = await api.apps()
  apps.value = (data as any).items || data || []
  
  // 加载每个应用的能力和策略数量
  for (const app of apps.value) {
    try {
      const [caps, policies] = await Promise.all([
        api.capabilities(app.id).catch(() => ({ items: [] })),
        api.templates(app.id).catch(() => ({ items: [] }))
      ])
      capCounts.value[app.id] = (caps as any).items?.length || 0
      policyCounts.value[app.id] = (policies as any).items?.length || 0
    } catch {}
  }
}

onMounted(load)



async function selectApp(row: any) {
  router.push(`/apps/${row.id}`)
}

async function sync(row: any) {
  syncing.value = true
  try {
    const res = await api.syncApp(row.id)
    ElMessage.success(`同步完成：${(res as any).actions} 个权限点`)
    load()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    syncing.value = false
  }
}
</script>

<style scoped>
.app-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.app-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px;
  cursor: pointer;
  transition: all .2s;
  box-shadow: var(--shadow-sm);
}
.app-card:hover {
  border-color: var(--brand);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--brand-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}
.card-info { flex: 1; min-width: 0; }
.card-name {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 2px;
}
.card-code {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-body {
  display: flex;
  gap: 24px;
  padding: 12px 0;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
  margin-bottom: 14px;
}
.card-stat { display: flex; flex-direction: column; }
.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.card-foot {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  transition: all .15s;
}
.btn:hover { background: var(--bg-hover); }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-primary:hover { background: var(--brand-strong); }
.btn-sm { height: 28px; padding: 0 10px; font-size: 11px; }
.btn-outline { background: transparent; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.tag {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
}
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-cyan { background: var(--info-bg); color: var(--info); }

.mono { font-family: var(--font-mono); }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--text-tertiary);
}
.empty-icon { font-size: 48px; }
.empty-text { font-size: 14px; }

/* 注册表单 */
.register-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label {
  font-size: 13px;
  font-weight: 600;
}
.required { color: var(--danger); }
.optional { color: var(--text-tertiary); font-weight: 400; font-size: 12px; }
.field-hint { font-size: 11px; color: var(--text-tertiary); }
.input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text);
  font-size: 13px;
  transition: border-color .15s;
}
.input:focus { border-color: var(--brand); outline: none; }

.type-options {
  display: flex;
  gap: 12px;
}
.type-option {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 2px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all .15s;
}
.type-option:hover { border-color: var(--brand); }
.type-option.selected { border-color: var(--brand); background: var(--brand-soft); }
.type-option input { display: none; }
.type-icon { font-size: 24px; }
.type-name { font-size: 13px; font-weight: 600; }
.type-desc { font-size: 11px; color: var(--text-tertiary); }
</style>
