<template>
  <el-card>
    <template #header>
      <div class="h"><span>用户管理</span><el-button type="primary" size="small" @click="openCreate">新建用户</el-button></div>
    </template>
    <el-table :data="users" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }"><el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="100">
        <template #default="{ row }">{{ row.source === 1 ? '身份源同步' : '手工' }}</template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showCreate" title="新建用户" width="400">
      <el-form label-width="70">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const users = ref<any[]>([])
const showCreate = ref(false)
const form = reactive({ username: '', display_name: '', email: '', password: '' })

async function load() {
  const data = await api.users()
  users.value = (data as any).items
}
onMounted(load)

function openCreate() {
  Object.assign(form, { username: '', display_name: '', email: '', password: '' })
  showCreate.value = true
}
async function create() {
  try {
    await api.createUser({ ...form, attributes: {} })
    ElMessage.success('已创建')
    showCreate.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}
</script>
<style scoped>.h { display: flex; justify-content: space-between; align-items: center; }</style>
