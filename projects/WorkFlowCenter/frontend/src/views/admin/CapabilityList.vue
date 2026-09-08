<template>
  <div class="capability-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><Connection /></el-icon></div><div><h1>能力注册</h1><p class="page-header-desc">注册和管理自动化执行能力</p></div></div>
      <p>注册外部能力（连接器），供流程的办理节点调用</p>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建能力
      </el-button>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.is_active" placeholder="全部" clearable style="width: 110px">
            <el-option label="启用" value="true" />
            <el-option label="停用" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-select v-model="filterForm.execute_mode" placeholder="全部" clearable style="width: 110px">
            <el-option label="同步" value="sync" />
            <el-option label="异步" value="async" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索能力名称/编码"
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
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="name" label="能力名称" min-width="140">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">{{ row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="能力编码" width="160">
          <template #default="{ row }">
            <code class="cap-code">{{ row.code }}</code>
          </template>
        </el-table-column>
        <el-table-column label="执行模式" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">
              {{ row.execute_mode === 'sync' ? '同步' : '异步' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="endpoint" label="端点" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="endpoint-text">{{ row.endpoint || 'Mock' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button type="primary" link @click="editItem(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑能力' : '新建能力'" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="能力名称" prop="name">
          <el-input v-model="form.name" placeholder="如：CMDB 创建主机" />
        </el-form-item>
        <el-form-item label="能力编码" prop="code">
          <el-input v-model="form.code" placeholder="如：cmdb.create_host" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="执行模式" prop="execute_mode">
          <el-radio-group v-model="form.execute_mode">
            <el-radio value="sync">同步</el-radio>
            <el-radio value="async">异步</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="端点 URL">
          <el-input v-model="form.endpoint" placeholder="http://example.com/api（留空则使用 Mock 执行）" />
        </el-form-item>
        <el-form-item label="输入 Schema">
          <el-input
            v-model="form.input_schema"
            type="textarea"
            :rows="5"
            placeholder='{"type":"object","properties":{"hostname":{"type":"string","title":"主机名"}},"required":["hostname"]}'
          />
        </el-form-item>
        <el-form-item label="输出 Schema">
          <el-input
            v-model="form.output_schema"
            type="textarea"
            :rows="4"
            placeholder='{"type":"object","properties":{"host_id":{"type":"string"}}}'
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="能力用途说明" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Connection } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCapabilities, createCapability, updateCapability, deleteCapability
} from '@/api/modules/capability'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const filterForm = reactive({
  is_active: '',
  execute_mode: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  execute_mode: 'sync',
  endpoint: '',
  input_schema: '{}',
  output_schema: '{}',
  description: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入能力名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入能力编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_.]*$/, message: '编码只能包含字母、数字、点和下划线', trigger: 'blur' }
  ],
  execute_mode: [{ required: true, message: '请选择执行模式', trigger: 'change' }]
}

const parseJson = (text, fallback) => {
  try {
    return JSON.parse(text || '{}')
  } catch (e) {
    return fallback
  }
}

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
    const response = await getCapabilities(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.is_active = ''
  filterForm.execute_mode = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    name: '', code: '', execute_mode: 'sync', endpoint: '',
    input_schema: '{}', output_schema: '{}', description: '', is_active: true
  })
  dialogVisible.value = true
}

const editItem = (row) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    code: row.code,
    execute_mode: row.execute_mode || 'sync',
    endpoint: row.endpoint || '',
    input_schema: JSON.stringify(row.input_schema || {}, null, 2),
    output_schema: JSON.stringify(row.output_schema || {}, null, 2),
    description: row.description || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const inputSchema = parseJson(form.input_schema, null)
  const outputSchema = parseJson(form.output_schema, null)
  if (inputSchema === null) {
    ElMessage.error('输入 Schema 不是合法的 JSON')
    return
  }
  if (outputSchema === null) {
    ElMessage.error('输出 Schema 不是合法的 JSON')
    return
  }

  submitting.value = true
  try {
    const data = {
      name: form.name,
      code: form.code,
      execute_mode: form.execute_mode,
      endpoint: form.endpoint,
      input_schema: inputSchema,
      output_schema: outputSchema,
      description: form.description,
      is_active: form.is_active
    }
    if (isEdit.value) {
      await updateCapability(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createCapability(data)
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

const handleStatusChange = async (row, val) => {
  try {
    await updateCapability(row.id, { ...row, is_active: val })
    ElMessage.success(val ? '已启用' : '已停用')
  } catch (error) {
    console.error('状态更新失败:', error)
  }
}

const viewDetail = (row) => {
  router.push(`/admin/capabilities/${row.id}`)
}

const deleteItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除能力"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error' }
    )
    await deleteCapability(row.id)
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
})
</script>

<style scoped lang="scss">
.capability-list {
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

.filter-card {
  margin-bottom: 20px;
}

.cap-code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
}

.endpoint-text {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>