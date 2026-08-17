<template>
  <div class="ticket-type-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><Collection /></el-icon></div><div><h1>工单类型</h1><p class="page-header-desc">配置工单分类和类型管理</p></div></div>
      <p>管理工单的业务分类与优先级策略</p>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建类型
      </el-button>
    </div>

    <el-card>
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="name" label="类型名称" min-width="150" />
        <el-table-column prop="code" label="类型编码" width="150" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="启用" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val) => toggleActive(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 创建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑类型' : '新建类型'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="类型名称" required>
          <el-input v-model="form.name" placeholder="如：服务器申请" />
        </el-form-item>
        <el-form-item label="类型编码" required>
          <el-input v-model="form.code" placeholder="如：server_apply" :disabled="editing" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="类型用途说明" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Collection } from '@element-plus/icons-vue'
import {
  getTicketTypes, createTicketType, updateTicketType, deleteTicketType
} from '@/api/modules/ticket-types'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const editing = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  description: '',
  is_active: true
})

const fetchData = async () => {
  loading.value = true
  try {
    const response = await getTicketTypes({ page: pagination.page, page_size: pagination.pageSize })
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取工单类型失败:', error)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  Object.assign(form, { name: '', code: '', description: '', is_active: true })
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = row
  Object.assign(form, {
    name: row.name,
    code: row.code,
    description: row.description || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const save = async () => {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写类型名称和编码')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateTicketType(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await createTicketType(form)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row, val) => {
  try {
    await updateTicketType(row.id, { ...row, is_active: val })
    ElMessage.success(val ? '已启用' : '已停用')
  } catch (error) {
    console.error('切换失败:', error)
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除工单类型「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTicketType(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.ticket-type-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 4px;
    color: #303133;
    font-size: 20px;
  }

  p {
    margin: 0 0 12px;
    font-size: 13px;
    color: #909399;
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
