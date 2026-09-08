<template>
  <div class="department-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><OfficeBuilding /></el-icon></div><div><h1>部门管理</h1><p class="page-header-desc">组织架构来自统一身份源同步，本页为演示 / 管理用</p></div></div>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建部门
      </el-button>
    </div>

    <el-alert
      class="sync-alert"
      type="info"
      show-icon
      :closable="false"
      title="组织架构来自统一身份源（LDAP / Okta）同步"
      description="真实环境中部门由身份源同步维护，本系统不做独立组织体系；本页用于演示环境与本地管理。"
    />
    
    <!-- 数据表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="treeData"
        row-key="id"
        border
        default-expand-all
        :tree-props="{ children: 'children' }"
      >
        <el-table-column prop="name" label="部门名称" min-width="200" />
        <el-table-column prop="leader" label="负责人" width="120">
          <template #default="{ row }">
            {{ row.leader_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="成员数" width="100" align="center">
          <template #default="{ row }">
            {{ row.member_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="addChild(row)">
              添加子部门
            </el-button>
            <el-button type="primary" link @click="editItem(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="deleteItem(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="上级部门">
          <el-tree-select
            v-model="form.parent_id"
            :data="treeData"
            :props="{ label: 'name', value: 'id' }"
            placeholder="无（一级部门）"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        
        <el-form-item label="部门编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入部门编码" :disabled="isEdit" />
        </el-form-item>
        
        <el-form-item label="负责人" prop="leader_id">
          <el-select v-model="form.leader_id" placeholder="请选择负责人" clearable style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">停用</el-radio>
          </el-radio-group>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, OfficeBuilding } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDepartments, createDepartment, updateDepartment, deleteDepartment, getUsers } from '@/api/modules/admin'

const loading = ref(false)
const tableData = ref([])
const users = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const formRef = ref(null)

const form = reactive({
  parent_id: '',
  name: '',
  code: '',
  leader_id: '',
  status: 'active'
})

const rules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '编码只能包含字母、数字和下划线', trigger: 'blur' }
  ]
}

// 计算属性：对话框标题
const dialogTitle = computed(() => {
  if (isEdit.value) return '编辑部门'
  return form.parent_id ? '添加子部门' : '新建部门'
})

// 构建树形数据
const buildTree = (items, parentId = null) => {
  const tree = []
  items.forEach(item => {
    if (item.parent_id === parentId) {
      const children = buildTree(items, item.id)
      tree.push({
        ...item,
        children: children.length > 0 ? children : undefined
      })
    }
  })
  return tree
}

// 计算属性：树形数据
const treeData = computed(() => {
  return buildTree(tableData.value)
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const response = await getDepartments({ page: 1, page_size: 1000 })
    const data = response?.data ?? response
    const items = Array.isArray(data) ? data : (data?.results || [])
    // API 字段映射：parent→parent_id（buildTree）、manager_name→leader_name、members_count→member_count、无 status 视为启用
    tableData.value = items.map((d) => ({
      ...d,
      parent_id: d.parent,
      leader_name: d.manager_name,
      member_count: d.members_count,
      status: 'active',
    }))
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await getUsers({ page: 1, page_size: 1000 })
    const data = response?.data ?? response
    users.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (error) {
    console.error('获取用户失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.parent_id = ''
  form.name = ''
  form.code = ''
  form.leader_id = ''
  form.status = 'active'
  dialogVisible.value = true
}

// 添加子部门
const addChild = (row) => {
  isEdit.value = false
  editingId.value = null
  form.parent_id = row.id
  form.name = ''
  form.code = ''
  form.leader_id = ''
  form.status = 'active'
  dialogVisible.value = true
}

// 编辑
const editItem = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.parent_id = row.parent_id || ''
  form.name = row.name
  form.code = row.code
  form.leader_id = row.leader_id || ''
  form.status = row.status
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    const data = {
      ...form,
      parent_id: form.parent_id || null,
      leader_id: form.leader_id || null
    }
    
    if (isEdit.value) {
      await updateDepartment(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createDepartment(data)
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

// 删除
const deleteItem = async (row) => {
  // 检查是否有子部门
  const hasChildren = tableData.value.some(item => item.parent_id === row.id)
  if (hasChildren) {
    ElMessage.warning('该部门下有子部门，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除部门"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await deleteDepartment(row.id)
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
  fetchUsers()
})
</script>

<style scoped>
.department-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #333;
}
</style>