<template>
  <div class="approval-task-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <div>
          <h1>{{ pageTitle }}</h1>
          <p class="page-header-desc">{{ pageDesc }}</p>
        </div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-card">
      <div class="filter-row">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部" clearable>
              <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="filterForm.keyword"
              placeholder="搜索节点名称"
              clearable
              @keyup.enter="fetchData"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">搜索</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 列表 -->
    <div class="table-card">
      <div class="table-card-header">
        <div class="table-card-title">
          任务列表
          <span class="table-count">{{ pagination.total }} 条</span>
        </div>
      </div>
      <el-table v-loading="loading" :data="tableData">
        <el-table-column label="申请标题" min-width="200">
          <template #default="{ row }">
            <span class="table-link" @click="viewTask(row)">
              {{ row.ticket_title || row.node_name || row.instance_no }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="node_name" label="节点" width="120" />
        <el-table-column prop="node_type" label="类型" width="90" align="center">
          <template #default="{ row }">
            {{ nodeTypeLabel(row.node_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="处理人" width="100">
          <template #default="{ row }">
            {{ row.assignee_name || (row.candidate_users?.length ? '多人候选' : '待认领') }}
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ row.status_display || getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ row.created_at }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-group">
              <el-button
                v-if="mode === 'todo' && row.status === 'pending'"
                type="warning"
                link
                @click="claimTask(row)"
              >
                认领
              </el-button>
              <el-button type="primary" link @click="viewTask(row)">
                {{ mode === 'todo' ? '办理' : '查看' }}
              </el-button>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Tickets } from '@element-plus/icons-vue'
import { getTasks, claimTask as claimTaskApi } from '@/api/modules/task'

const route = useRoute()
const router = useRouter()

const mode = computed(() => route.meta.mode || 'todo')
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

const pageTitle = computed(() => {
  const titles = { todo: '待办审批', done: '已办审批', cc: '抄送我的' }
  return titles[mode.value] || '审批任务'
})

const pageDesc = computed(() => {
  const descs = {
    todo: '需要你处理的审批任务',
    done: '你已处理完成的审批记录',
    cc: '抄送给你知悉的流程'
  }
  return descs[mode.value] || ''
})

const statusOptions = computed(() => {
  if (mode.value === 'todo') {
    return [
      { value: 'pending', label: '待认领' },
      { value: 'claimed', label: '已认领' }
    ]
  }
  return [
    { value: 'completed', label: '已完成' },
    { value: 'rejected', label: '已拒绝' }
  ]
})

const nodeTypeLabel = (type) => {
  const labels = {
    start: '开始', approve: '审批', handle: '办理',
    service: '服务', cc: '抄送', condition: '条件', end: '结束'
  }
  return labels[type] || type || '-'
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      type: mode.value,
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filterForm
    }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    const response = await getTasks(params)
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取任务失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.keyword = ''
  pagination.page = 1
  fetchData()
}

const viewTask = (row) => {
  router.push(`/my/tasks/${row.id}`)
}

const claimTask = async (row) => {
  try {
    await claimTaskApi(row.id)
    ElMessage.success('认领成功')
    fetchData()
  } catch (error) {
    console.error('认领失败:', error)
    ElMessage.error('认领失败')
  }
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    claimed: 'primary',
    completed: 'success',
    cancelled: 'info',
    skipped: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '待认领',
    claimed: '已认领',
    completed: '已完成',
    cancelled: '已取消',
    skipped: '已跳过'
  }
  return labels[status] || status
}

// 切换待办/已办/抄送时（同一组件复用），重置分页并重新拉取
watch(mode, () => {
  pagination.page = 1
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.approval-task-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}
</style>
