<template>
  <div class="user-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><User /></el-icon>
        </div>
        <div>
          <h1>用户管理</h1>
          <p class="page-header-desc">组织账号来自统一身份源（LDAP / Okta 同步），本页为演示 / 管理用</p>
        </div>
      </div>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建用户
      </el-button>
    </div>

    <el-alert
      class="sync-alert"
      type="info"
      show-icon
      :closable="false"
      title="组织数据来自统一身份源（LDAP / Okta）同步"
      description="真实环境中用户由身份源同步维护，本系统不做独立账号体系；本页用于演示环境与本地管理。"
    />
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <!-- 即将支持的功能提示 -->
      <el-alert
        title="权限中心接入"
        description="企业级权限中心（LDAP / AD / OAuth2）对接即将上线。届时可在此配置统一认证源，实现用户同步和单点登录。当前版本仅支持本地用户管理。"
        type="info"
        show-icon
        :closable="true"
        style="margin-bottom: 16px;"
      />
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="部门">
          <el-select v-model="filterForm.department_id" placeholder="全部" clearable>
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索用户名/姓名"
            clearable
            @keyup.enter="fetchData"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="fetchData">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="department_name" label="部门" width="120" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag v-for="role in row.roles" :key="role.id" style="margin-right: 4px">
              {{ role.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :active-value="true"
              :inactive-value="false"
              :disabled="row.username === 'admin'"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editItem(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="deleteItem(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新建用户'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="角色" prop="role_ids">
          <el-select v-model="form.role_ids" multiple placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, User } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, createUser, updateUser, deleteUser, getDepartments, getRoles } from '@/api/modules/admin'

const loading = ref(false)
const tableData = ref([])
const departments = ref([])
const roles = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const formRef = ref(null)

const filterForm = reactive({
  department_id: '',
  status: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  username: '',
  password: '',
  name: '',
  email: '',
  department_id: '',
  role_ids: []
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  department_id: [
    { required: true, message: '请选择部门', trigger: 'change' }
  ]
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filterForm
    }
    
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    
    const response = await getUsers(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取部门列表
const fetchDepartments = async () => {
  try {
    const response = await getDepartments({ page: 1, page_size: 100 })
    const data = response?.data ?? response
    departments.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取部门失败:', error)
  }
}

// 获取角色列表
const fetchRoles = async () => {
  try {
    const response = await getRoles({ page: 1, page_size: 100 })
    const data = response?.data ?? response
    roles.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取角色失败:', error)
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.department_id = ''
  filterForm.status = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.username = ''
  form.password = ''
  form.name = ''
  form.email = ''
  form.department_id = ''
  form.role_ids = []
  dialogVisible.value = true
}

// 编辑
const editItem = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.username = row.username
  form.name = row.name
  form.email = row.email
  form.department_id = row.department_id
  form.role_ids = row.roles?.map(r => r.id) || []
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateUser(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createUser(form)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

// 状态变更
const handleStatusChange = async (row) => {
  try {
    await updateUser(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error) {
    console.error('状态更新失败:', error)
    row.is_active = !row.is_active
  }
}

// 删除
const deleteItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

onMounted(() => {
  fetchData()
  fetchDepartments()
  fetchRoles()
})
</script>

<style scoped>
.user-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}
</style>