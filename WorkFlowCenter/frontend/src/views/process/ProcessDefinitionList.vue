<template>
  <div class="process-definition-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div>
          <h1>流程配置</h1>
          <p class="page-header-desc">管理和配置业务流程模版</p>
        </div>
      </div>
      <el-button type="primary" @click="createNew">
        <el-icon><Plus /></el-icon>
        新建流程
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="filter-card">
      <div class="filter-row">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部" clearable>
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
              <el-option label="已停用" value="disabled" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="filterForm.keyword" placeholder="搜索流程名称" clearable @keyup.enter="fetchData" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">搜索</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <div class="table-card">
      <div class="table-card-header">
        <div class="table-card-title">
          流程列表
          <span class="table-count">{{ pagination.total }} 条</span>
        </div>
      </div>
      <el-table v-loading="loading" :data="tableData">
        <el-table-column prop="name" label="流程名称" min-width="150">
          <template #default="{ row }">
            <span class="table-link" @click="editItem(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="key" label="唯一标识" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ row.created_at }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <div class="action-group">
              <el-button type="primary" link @click="editItem(row)">编辑</el-button>
              <el-button v-if="row.status === 'draft'" type="success" link @click="publishItem(row)">发布</el-button>
              <el-button v-if="row.status === 'published'" type="warning" link @click="deactivateItem(row)">停用</el-button>
              <el-button type="danger" link @click="deleteItem(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <span class="pagination-info">共 <strong>{{ pagination.total }}</strong> 条</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDefinitions,
  publishDefinition,
  deactivateDefinition,
  deleteDefinition,
  checkDefinition
} from '@/api/modules/process'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

const filterForm = reactive({
  status: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filterForm
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    
    const response = await getDefinitions(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.status = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

// 新建流程
const createNew = () => {
  router.push('/process-definitions/new')
}

// 编辑
const editItem = (row) => {
  router.push(`/process-definitions/${row.id}`)
}

// 发布
const publishItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要发布流程"${row.name}"吗？发布后将对所有用户可见。`,
      '发布确认',
      {
        confirmButtonText: '确定发布',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 发布前自检：存在错误项则阻止发布，引导到编辑页修复
    const checkResp = await checkDefinition(row.id)
    const checkData = checkResp?.data ?? checkResp
    const summary = checkData?.summary || {}
    if (summary.errors > 0) {
      ElMessage.error(`流程存在 ${summary.errors} 个错误项，请先到编辑页修复后再发布`)
      return
    }

    await publishDefinition(row.id)
    ElMessage.success('发布成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('发布失败:', error)
    }
  }
}

// 停用
const deactivateItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要停用流程"${row.name}"吗？停用后将不再显示在工单创建列表中。`,
      '停用确认',
      {
        confirmButtonText: '确定停用',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deactivateDefinition(row.id)
    ElMessage.success('停用成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停用失败:', error)
    }
  }
}

// 删除
const deleteItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除流程"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await deleteDefinition(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    draft: 'info',
    published: 'success',
    disabled: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    draft: '草稿',
    published: '已发布',
    disabled: '已停用'
  }
  return labels[status] || status
}

// 获取分类标签
const categoryLabel = (category) => {
  const labels = {
    general: '通用',
    hr: '人事',
    finance: '财务',
    admin: '行政',
    it: 'IT'
  }
  return labels[category] || '通用'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.process-definition-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}
</style>