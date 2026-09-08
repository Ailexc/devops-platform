<template>
  <div class="task-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <div>
          <h1>任务中心</h1>
          <p class="page-header-desc">管理待办、已办和抄送任务</p>
        </div>
      </div>
    </div>
    
    <!-- Tab 切换 -->
    <div class="tabs-card">
      <div class="tabs-bar">
        <div
          v-for="tab in [{ key: 'todo', label: '待办任务' }, { key: 'done', label: '已办任务' }, { key: 'cc', label: '抄送我' }, { key: 'created', label: '我发起的' }]"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key; handleTabChange()"
        >
          {{ tab.label }}
        </div>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <div class="table-card">
      <el-table v-loading="loading" :data="tableData">
        <el-table-column prop="ticket_title" label="工单标题" min-width="200">
          <template #default="{ row }">
            <span class="table-link" @click="viewTask(row)">
              {{ row.ticket_title }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="node_name" label="当前节点" width="120" />
        
        <el-table-column prop="assignee" label="处理人" width="100">
          <template #default="{ row }">
            {{ row.assignee || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="'status-tag--' + row.status">
              <span class="status-tag__dot"></span>
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ row.created_at }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-group">
              <el-button
                v-if="activeTab === 'todo' && row.status === 'pending'"
                type="warning"
                link
                @click="claimTask(row)"
              >
                认领
              </el-button>
              <el-button type="primary" link @click="viewTask(row)">
                {{ activeTab === 'todo' ? '办理' : '查看' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
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
import { ElMessage } from 'element-plus'
import { Tickets } from '@element-plus/icons-vue'
import { getTasks, claimTask as claimTaskApi } from '@/api/modules/task'

const router = useRouter()

const loading = ref(false)
const activeTab = ref('todo')
const tableData = ref([])

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
      type: activeTab.value,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    const response = await getTasks(params)
    tableData.value = response.data?.items || []
    pagination.total = response.data?.total || 0
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// Tab 切换
const handleTabChange = () => {
  pagination.page = 1
  fetchData()
}

// 查看任务
const viewTask = (row) => {
  router.push(`/tasks/${row.id}`)
}

// 认领任务
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

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    claimed: 'primary',
    completed: 'success',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    pending: '待认领',
    claimed: '处理中',
    completed: '已完成',
    rejected: '已拒绝'
  }
  return labels[status] || status
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.task-list {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
}

.tabs-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  border: 1px solid #E5E6EB;
  margin-bottom: 20px;
  overflow: hidden;
}
.tabs-bar {
  display: flex; gap: 0; padding: 0 8px;
}
.tab-item {
  padding: 14px 20px; font-size: 14px; font-weight: 500;
  color: var(--text-secondary, #86909C); cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  transition: all 0.2s;
}
.tab-item:hover { color: #409EFF; }
.tab-item.active { color: #409EFF; border-bottom-color: #409EFF; font-weight: 600; }
</style>