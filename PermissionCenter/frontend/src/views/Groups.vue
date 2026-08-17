<template>
  <div class="groups-page">
    <header class="page-header">
      <h1>组织 / 组</h1>
      <span class="page-desc">组织架构树与自建组管理（物化路径）</span>
    </header>

    <div class="panel">
      <div class="panel-toolbar">
        <button class="btn btn-primary" @click="showCreate = true">新建组</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>物化路径</th>
            <th>类型</th>
            <th>来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in groups" :key="g.id" class="clickable" @click="openGroup(g)">
            <td class="mono">{{ g.id }}</td>
            <td>{{ g.name }}</td>
            <td class="mono text-secondary">{{ g.path }}</td>
            <td><span class="tag">{{ g.type === 1 ? '组织' : '自建' }}</span></td>
            <td class="text-secondary">{{ g.source === 1 ? '身份源' : '手工' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="groups.length === 0" class="empty-state">暂无数据</div>
    </div>

    <el-dialog v-model="showCreate" title="新建组" width="420">
      <el-form label-width="70">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="父组">
          <el-select v-model="form.parent_id" clearable filterable>
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showCreate = false">取消</button>
        <button class="btn btn-primary" @click="create">创建</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const router = useRouter()
const groups = ref<any[]>([])
const showCreate = ref(false)
const form = reactive({ name: '', parent_id: undefined as number | undefined })

async function load() {
  const data = await api.groups()
  groups.value = (data as any).items
}
onMounted(load)

async function create() {
  await api.createGroup({ name: form.name, parent_id: form.parent_id, type: 2 })
  ElMessage.success('已创建')
  showCreate.value = false
  load()
}

function openGroup(row: any) {
  router.push(`/groups/${row.id}`)
}
</script>

<style scoped>
.groups-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.panel { border: 1px solid var(--border); background: var(--bg); }
.panel-toolbar { display: flex; justify-content: flex-end; padding: 12px 16px; border-bottom: 1px solid var(--border); }

.btn { padding: 6px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-primary:hover { opacity: 0.9; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 16px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); }
.data-table tr:hover td { background: var(--bg-hover); }
.data-table tr.clickable { cursor: pointer; }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
