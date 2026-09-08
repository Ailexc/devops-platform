<template>
  <el-card>
    <template #header>
      <div class="h"><span>角色管理（板块式勾选权限点）</span>
        <el-button type="primary" size="small" @click="showCreate = true">新建角色</el-button>
      </div>
    </template>
    <el-table :data="roles" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="code" label="code" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="editRole(row)">配置权限</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建角色" width="400">
      <el-form label-width="70">
        <el-form-item label="code"><el-input v-model="form.code" placeholder="host-admin" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="应用">
          <el-select v-model="form.app_id" filterable>
            <el-option v-for="a in apps" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEdit" :title="`配置角色：${current?.name}`" width="620">
      <el-tree
        ref="treeRef"
        :data="actionTree"
        show-checkbox
        node-key="id"
        :props="{ label: 'label', children: 'children' }"
      />
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveRoleActions">保存（自动发布）</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const roles = ref<any[]>([])
const apps = ref<any[]>([])
const actionTree = ref<any[]>([])
const showCreate = ref(false)
const showEdit = ref(false)
const current = ref<any>(null)
const treeRef = ref<any>(null)
const form = reactive({ code: '', name: '', app_id: undefined as number | undefined })

async function load() {
  const r = await api.roles()
  roles.value = (r as any).items
  const a = await api.apps()
  apps.value = (a as any).items
}
onMounted(load)

async function create() {
  await api.createRole({ ...form, description: '' })
  ElMessage.success('已创建')
  showCreate.value = false
  load()
}

async function editRole(row: any) {
  current.value = row
  showEdit.value = true
  // 按板块构建权限点树
  const t = await api.templates(row.app_id)
  actionTree.value = (t as any).items.map((x: any) => ({
    id: `t${x.id}`,
    label: x.name,
    children: x.actions.map((a: any) => ({ id: a.id, label: `${a.code}（${a.name}）` })),
  }))
}

async function saveRoleActions() {
  const checked = treeRef.value.getCheckedKeys(true).filter((k: string) => typeof k === 'number') as number[]
  await api.setRoleActions(current.value.id, checked)
  ElMessage.success('已保存并发布')
  showEdit.value = false
}
</script>
<style scoped>.h { display: flex; justify-content: space-between; align-items: center; }</style>
