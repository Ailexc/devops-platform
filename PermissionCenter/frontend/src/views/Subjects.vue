<template>
  <div class="subjects-page">
    <header class="page-header">
      <h1>授权主体</h1>
      <span class="page-desc">用户、组与程序身份统一管理</span>
    </header>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'users' }" @click="tab = 'users'">用户</button>
      <button class="tab" :class="{ active: tab === 'groups' }" @click="tab = 'groups'">组</button>
      <button class="tab" :class="{ active: tab === 'clients' }" @click="tab = 'clients'">程序身份</button>
    </div>

    <!-- Users Tab -->
    <div v-if="tab === 'users'" class="panel">
      <div class="panel-toolbar">
        <button class="btn btn-primary" @click="showCreateUser = true">新建用户</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>显示名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="mono">{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.display_name }}</td>
            <td class="text-secondary">{{ u.email }}</td>
            <td><span class="tag" :class="u.status === 1 ? 'tag-success' : 'tag-danger'">{{ u.status === 1 ? '启用' : '停用' }}</span></td>
            <td class="text-secondary">{{ u.source === 1 ? '身份源' : '手工' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Groups Tab -->
    <div v-if="tab === 'groups'" class="panel">
      <div class="panel-toolbar">
        <button class="btn btn-primary" @click="showCreateGroup = true">新建组</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>物化路径</th>
            <th>类型</th>
            <th>来源</th>
            <th>TTL</th>
            <th style="width: 120px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in groups" :key="g.id">
            <td class="mono">{{ g.id }}</td>
            <td>{{ g.name }}</td>
            <td class="mono text-secondary">{{ g.path }}</td>
            <td><span class="tag">{{ g.type === 1 ? '组织' : '自建' }}</span></td>
            <td class="text-secondary">{{ g.source === 1 ? '身份源' : '手工' }}</td>
            <td class="mono text-secondary">{{ g.expires_at ? formatTime(g.expires_at) : '永久' }}</td>
            <td>
              <button class="btn btn-sm" @click="editGroupPerms(g)">配置权限</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Clients Tab -->
    <div v-if="tab === 'clients'" class="panel">
      <div class="panel-toolbar">
        <span class="text-secondary" style="font-size: 12px;">程序身份由应用 owner 在应用管理中创建</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Client ID</th>
            <th>所属应用</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in clients" :key="c.id">
            <td class="mono">{{ c.id }}</td>
            <td class="mono">{{ c.client_id }}</td>
            <td>{{ getAppName(c.app_id) }}</td>
            <td><span class="tag" :class="c.status === 1 ? 'tag-success' : 'tag-danger'">{{ c.status === 1 ? '启用' : '停用' }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-if="clients.length === 0" class="empty-state">暂无程序身份</div>
    </div>

    <!-- Create User Dialog -->
    <el-dialog v-model="showCreateUser" title="新建用户" width="420" :class="'bw-dialog'">
      <el-form label-width="70">
        <el-form-item label="用户名"><el-input v-model="userForm.username" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="userForm.display_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="userForm.email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="userForm.password" type="password" /></el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showCreateUser = false">取消</button>
        <button class="btn btn-primary" @click="createUser">创建</button>
      </template>
    </el-dialog>

    <!-- Create Group Dialog -->
    <el-dialog v-model="showCreateGroup" title="新建组" width="420">
      <el-form label-width="70">
        <el-form-item label="名称"><el-input v-model="groupForm.name" /></el-form-item>
        <el-form-item label="父组">
          <el-select v-model="groupForm.parent_id" clearable filterable>
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showCreateGroup = false">取消</button>
        <button class="btn btn-primary" @click="createGroup">创建</button>
      </template>
    </el-dialog>

    <!-- Group Permissions Dialog -->
    <el-dialog v-model="showGroupPerms" :title="`配置组权限：${editingGroup?.name || ''}`" width="520">
      <el-form label-width="90">
        <el-form-item label="权限点">
          <el-select v-model="groupPermForm.action_ids" multiple filterable placeholder="选择组可拥有的权限点">
            <el-option v-for="a in allActions" :key="a.id" :label="a.code" :value="a.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showGroupPerms = false">取消</button>
        <button class="btn btn-primary" @click="saveGroupPerms">保存（自动发布）</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const tab = ref<'users' | 'groups' | 'clients'>('users')
const users = ref<any[]>([])
const groups = ref<any[]>([])
const clients = ref<any[]>([])
const apps = ref<any[]>([])
const showCreateUser = ref(false)
const showCreateGroup = ref(false)
const userForm = reactive({ username: '', display_name: '', email: '', password: '' })
const groupForm = reactive({ name: '', parent_id: undefined as number | undefined })
const showGroupPerms = ref(false)
const editingGroup = ref<any>(null)
const allActions = ref<any[]>([])
const groupPermForm = reactive({ action_ids: [] as number[] })

function formatTime(t: string) {
  if (!t) return '—'
  try { return new Date(t).toLocaleDateString('zh-CN') } catch { return t }
}

function getAppName(appId: number) {
  const app = apps.value.find((a: any) => a.id === appId)
  return app ? app.name : String(appId)
}

async function load() {
  const u = await api.users()
  users.value = (u as any).items
  const g = await api.groups()
  groups.value = (g as any).items
  const c = await api.clients()
  clients.value = (c as any).items || []
  const a = await api.apps()
  apps.value = (a as any).items || []
}
onMounted(load)

async function createUser() {
  try {
    await api.createUser({ ...userForm, attributes: {} })
    ElMessage.success('已创建')
    showCreateUser.value = false
    load()
  } catch (e: any) { ElMessage.error(e.message) }
}

async function createGroup() {
  await api.createGroup({ name: groupForm.name, parent_id: groupForm.parent_id, type: 2 })
  ElMessage.success('已创建')
  showCreateGroup.value = false
  load()
}

async function editGroupPerms(group: any) {
  editingGroup.value = group
  showGroupPerms.value = true
  // 加载所有应用的权限点
  const a = await api.apps()
  const apps = (a as any).items || []
  let allActs: any[] = []
  for (const app of apps) {
    try {
      const d = await api.actions(app.id)
      allActs = allActs.concat((d as any).items || [])
    } catch { /* skip */ }
  }
  allActions.value = allActs
  // 加载当前组已有的权限
  try {
    const perms = await api.getGroupPermissions(group.id)
    groupPermForm.action_ids = (perms as any).action_ids || []
  } catch {
    groupPermForm.action_ids = []
  }
}

async function saveGroupPerms() {
  const res: any = await api.setGroupPermissions(editingGroup.value.id, groupPermForm.action_ids, '组权限调整（组长申请）')
  ElMessage.success(`已发起授权申请单 #${res.id}，待其他应用负责人审批后生效`)
  showGroupPerms.value = false
}
</script>

<style scoped>
.subjects-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.tabs {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  margin-bottom: 0;
  width: fit-content;
}

.tab {
  padding: 8px 20px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg);
  border: none;
  border-right: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.tab:last-child { border-right: none; }
.tab:hover { background: var(--bg-hover); color: var(--text); }
.tab.active { background: var(--accent); color: var(--accent-text); font-weight: 600; }

.panel {
  border: 1px solid var(--border);
  border-top: none;
  background: var(--bg);
}

.panel-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.btn {
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s;
}

.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-primary:hover { opacity: 0.9; }

/* Table */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 10px 16px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.data-table tr:hover td { background: var(--bg-hover); }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }

.tag {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-tertiary);
}

.tag-success { background: var(--success-bg); }
.tag-danger { background: var(--danger-bg); }

.empty-state {
  padding: 24px 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
