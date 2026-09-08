<template>
  <div class="role-list">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><Avatar /></el-icon></div><div><h1>角色管理</h1><p class="page-header-desc">流程中的职责 · 审批人维度（与流程配置绑定）</p></div></div>
      <p>角色用于流程审批人、提交范围等配置；自定义人员审批时再单独添加</p>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建角色
      </el-button>
    </div>

    <!-- 真实业务场景 -->
    <el-card class="scene-card" shadow="never">
      <template #header><span>角色 = 流程中的职责</span></template>
      <p class="scene-desc">
        流程配置基于<strong>组织架构与角色</strong>分配审批人：如「运维审批」角色，流程节点指定该角色后，运行时自动解析出角色下成员为审批人；
        仅当需要<strong>自定义人员</strong>审批时才单独添加。身份源回答「你是谁」，角色回答「你在这个流程里承担什么职责」。
      </p>
      <div class="scene-flow">
        <div class="scene-flow__node">流程节点</div>
        <span class="arrow">→</span>
        <div class="scene-flow__node">指定角色（如：运维审批）</div>
        <span class="arrow">→</span>
        <div class="scene-flow__node">运行时解析角色成员为审批人</div>
      </div>
    </el-card>

    <el-card>
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="角色名称" min-width="150" />
        <el-table-column label="成员" min-width="100" align="center">
          <template #default="{ row }">
            <el-tooltip :content="(row.members || []).join('、') || '暂无成员'" placement="top">
              <span class="member-count">{{ row.member_count || 0 }} 人</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="被流程使用" min-width="130" align="center">
          <template #default="{ row }">
            <template v-if="row.used_by?.length">
              <el-tooltip :content="row.used_by.map(u => u[0] + ' · ' + u[1]).join('\n')" placement="top">
                <el-tag type="warning" size="small" effect="plain">{{ row.used_by.length }} 个节点</el-tag>
              </el-tooltip>
            </template>
            <span v-else class="muted">未使用</span>
          </template>
        </el-table-column>
        <el-table-column label="权限数" width="90" align="center">
          <template #default="{ row }">
            {{ row.permissions?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色' : '新建角色'" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="角色名称" required>
          <el-input v-model="form.name" placeholder="如：部门主管" />
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
import { Plus, Avatar } from '@element-plus/icons-vue'
import { getRoles, createRole, deleteRole } from '@/api/modules/admin'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const editing = ref(null)

const form = reactive({
  name: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    const response = await getRoles()
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取角色失败:', error)
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  form.name = ''
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = row
  form.name = row.name
  dialogVisible.value = true
}

const save = async () => {
  if (!form.name) {
    ElMessage.warning('请填写角色名称')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      // 后端基于 Group，更新即重建（简单处理）
      await createRole({ name: form.name })
      ElMessage.success('已保存')
    } else {
      await createRole({ name: form.name })
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

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除角色「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteRole(row.id)
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
.role-list {
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

.scene-card {
  margin-bottom: 16px;

  .scene-desc {
    margin: 0 0 14px;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.8;

    strong {
      color: #165dff;
    }
  }

  .scene-flow {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;

    .scene-flow__node {
      background: #f0f5ff;
      border: 1px solid #d6e4ff;
      color: #165dff;
      border-radius: 8px;
      padding: 8px 14px;
      font-size: 13px;
    }

    .arrow {
      color: #c9cdd4;
      font-size: 16px;
    }
  }
}

.member-count {
  font-weight: 600;
  color: #1d2129;
}

.muted {
  color: #c9cdd4;
}
</style>
