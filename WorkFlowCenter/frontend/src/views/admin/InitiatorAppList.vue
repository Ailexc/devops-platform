<template>
  <div class="initiator-app-list">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><Link /></el-icon></div>
        <div>
          <h1>开放 API</h1>
          <p class="page-header-desc">业务方接入 · 能力平台对接（同步 API 集成）</p>
        </div>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建接入方
      </el-button>
    </div>

    <!-- 真实业务场景 -->
    <el-card class="scene-card" shadow="never">
      <template #header><span>真实业务场景</span></template>
      <div class="scene-grid">
        <div class="scene-block">
          <div class="scene-block__head">
            <el-tag type="primary" effect="dark" size="small">业务方接入</el-tag>
            <span class="scene-block__name">外部调用本系统</span>
          </div>
          <ul class="scene-block__list">
            <li><strong>监控告警自动建单</strong>：监控探到故障自动调开放 API 建单（最高频入口）</li>
            <li><strong>CI 流水线 / 程序发起</strong>：脚本、流水线携带 API Key 发起工单</li>
            <li><strong>发布平台</strong>：发布系统调本系统流程发起审批，审批通过回调继续发布（双向）</li>
            <li><strong>对外回调端点</strong>：外部任务完成后调用本系统回报结果（HMAC 验签）</li>
          </ul>
        </div>
        <div class="scene-block">
          <div class="scene-block__head">
            <el-tag type="warning" effect="dark" size="small">能力平台对接</el-tag>
            <span class="scene-block__name">本系统调用外部</span>
          </div>
          <ul class="scene-block__list">
            <li><strong>任务中心</strong>：下发执行任务，App ID/Secret 整体签名（双向：下发 + 回执）</li>
            <li><strong>消息平台</strong>：统一消息出口发飞书等 IM（不直连通讯软件）</li>
          </ul>
        </div>
      </div>
      <p class="scene-hint">原则：<strong>同步 API 统一走「开放 API」（双向）</strong>，异步消息走「消息通道」；下方登记业务方接入方并管理接口凭证，能力平台对接以清单呈现。</p>
    </el-card>

    <!-- 业务方接入 · 接入方登记 -->
    <el-card>
      <template #header><span>业务方接入 · 接入方登记</span></template>
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="name" label="接入方名称" min-width="150" />
        <el-table-column prop="code" label="接入方标识" width="160">
          <template #default="{ row }">
            <code class="code-badge">{{ row.code }}</code>
          </template>
        </el-table-column>
        <el-table-column label="API Key" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_key" size="small" type="success">已生成</el-tag>
            <el-tag v-else size="small" type="info">未生成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="调用统计" min-width="180">
          <template #default="{ row }">
            <template v-if="callStats[row.code]">
              <span class="call-total">{{ callStats[row.code].total }}</span> 次 /
              <el-tag :type="callStats[row.code].failed ? 'danger' : 'success'" size="small">
                {{ callStats[row.code].failed }} 失败
              </el-tag>
              <div class="call-last">{{ callStats[row.code].last_call_at || '—' }}</div>
            </template>
            <span v-else class="call-none">—</span>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val) => toggleActive(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="warning" link @click="resetKey(row)">重置密钥</el-button>
            <el-button type="info" link @click="showExample(row)">调用示例</el-button>
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

    <!-- 能力平台对接 -->
    <el-card class="platform-card" shadow="never">
      <template #header><span>能力平台对接 · 本系统调用外部 API</span></template>
      <el-table :data="platformList" border stripe>
        <el-table-column prop="target" label="对接平台" min-width="110" />
        <el-table-column prop="action" label="交互方式" min-width="150" />
        <el-table-column label="方向" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === '双向' ? 'warning' : 'info'" size="small">{{ row.direction }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="desc" label="说明" min-width="330" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 开放 API 目录 -->
    <el-card class="api-catalog-card" shadow="never">
      <template #header><span>开放 API 目录（对外暴露端点）</span></template>
      <p class="catalog-desc">
        本系统对外暴露的<strong>同步 API 端点</strong>，外部系统据此对接本系统：
      </p>
      <el-table :data="apiCatalog" border stripe>
        <el-table-column label="方法" width="90" align="center">
          <template #default="{ row }">
            <span class="method-tag" :class="row.method === 'POST' ? 'method--post' : 'method--get'">{{ row.method }}</span>
          </template>
        </el-table-column>
        <el-table-column label="接口路径" min-width="260">
          <template #default="{ row }">
            <code class="code-badge">{{ row.path }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="用途" min-width="220" />
        <el-table-column prop="auth" label="认证" min-width="200" />
      </el-table>
    </el-card>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑接入方' : '新建接入方'" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="接入方名称" required>
          <el-input v-model="form.name" placeholder="如：CMDB 资产同步" />
        </el-form-item>
        <el-form-item label="接入方标识" required>
          <el-input v-model="form.code" placeholder="如：cmdb_sync（调用时使用）" :disabled="editing" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-alert
          v-if="!editing"
          type="info"
          :closable="false"
          show-icon
          title="创建成功后会生成 API Key，仅展示一次，请妥善保存"
        />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- API Key 一次性展示 -->
    <el-dialog v-model="keyDialogVisible" title="API Key（仅展示一次）" width="560px">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="请立即复制保存，关闭后将无法再次查看"
        class="key-alert"
      />
      <div class="key-box">
        <code>{{ currentApiKey }}</code>
        <el-button type="primary" link @click="copyKey">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
      </div>
      <template #footer>
        <el-button type="primary" @click="keyDialogVisible = false">我已保存</el-button>
      </template>
    </el-dialog>

    <!-- 调用示例 -->
    <el-dialog v-model="exampleDialogVisible" title="开放 API 调用示例" width="640px">
      <p class="example-tip">
        将下面的 <code>&#123;&#123;API_KEY&#125;&#125;</code> 替换为「{{ exampleAppName }}」的 API Key，
        <code>definition_id</code> 换成目标流程 ID，<code>initiator_user_id</code> 为提单人用户 ID。
      </p>
      <pre class="example-box">{{ exampleText }}</pre>
      <template #footer>
        <el-button type="primary" @click="copyExample">
          <el-icon><CopyDocument /></el-icon>
          复制示例
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Link, CopyDocument } from '@element-plus/icons-vue'
import {
  getInitiatorApps, createInitiatorApp, updateInitiatorApp,
  deleteInitiatorApp, resetInitiatorAppKey, getInitiatorAppStats
} from '@/api/modules/initiator-apps'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const callStats = ref({})
const dialogVisible = ref(false)
const keyDialogVisible = ref(false)
const exampleDialogVisible = ref(false)
const editing = ref(null)
const currentApiKey = ref('')
const exampleAppName = ref('')
const exampleText = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  is_active: true
})

// 能力平台对接（本系统调用外部 API）——说明清单
const platformList = [
  { target: '任务中心', action: '下发执行任务', direction: '双向', desc: '注册 App ID/Secret，参数+路径整体签名；下发后接收回执（派活签名 / 收结果验签）' },
  { target: '消息平台', action: '统一消息出口', direction: '单向', desc: '发飞书等 IM 一律经消息平台，不直接调通讯软件' }
]

// 开放 API 目录（对外暴露的同步 API 端点）
const apiCatalog = [
  { method: 'POST', path: '/api/v1/external/tickets', purpose: '外部程序 / 监控平台发起工单', auth: 'API Key（X-App-Code + X-App-Key）' },
  { method: 'POST', path: '/api/v1/external/callback', purpose: '外部任务执行完成回报结果', auth: 'HMAC-SHA256 签名（X-Callback-Signature）' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const response = await getInitiatorApps({ page: pagination.page, page_size: pagination.pageSize })
    const data = response?.data ?? response
    tableData.value = Array.isArray(data) ? data : (data?.results || [])
    pagination.total = data?.count || (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    console.error('获取发起程序失败:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await getInitiatorAppStats()
    const data = response?.data ?? response
    const map = {}
    ;(data?.by_app || []).forEach((a) => { map[a.code] = a })
    callStats.value = map
  } catch (e) {
    console.error('获取调用统计失败:', e)
  }
}

const openCreate = () => {
  editing.value = null
  Object.assign(form, { name: '', code: '', is_active: true })
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = row
  Object.assign(form, { name: row.name, code: row.code, is_active: row.is_active })
  dialogVisible.value = true
}

const save = async () => {
  if (!form.name.trim() || !form.code.trim()) {
    ElMessage.warning('请填写接入方名称和接入方标识')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateInitiatorApp(editing.value.id, { name: form.name, is_active: form.is_active })
      ElMessage.success('已保存')
    } else {
      const response = await createInitiatorApp({ name: form.name, code: form.code, is_active: form.is_active })
      const data = response?.data ?? response
      currentApiKey.value = data.api_key || ''
      ElMessage.success('接入方创建成功')
      keyDialogVisible.value = true
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，接入方标识可能已存在')
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row, val) => {
  try {
    await updateInitiatorApp(row.id, { is_active: val })
    row.is_active = val
    ElMessage.success(val ? '已启用' : '已停用')
  } catch (error) {
    console.error('切换状态失败:', error)
  }
}

const resetKey = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定重置「${row.name}」的 API Key 吗？旧 Key 将立即失效。`,
      '重置密钥',
      { confirmButtonText: '重置', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const response = await resetInitiatorAppKey(row.id)
    const data = response?.data ?? response
    currentApiKey.value = data.api_key || ''
    keyDialogVisible.value = true
    fetchData()
  } catch (error) {
    console.error('重置失败:', error)
    ElMessage.error('重置失败')
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除接入方「${row.name}」吗？绑定该接入方的流程将无法通过程序发起。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteInitiatorApp(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

const buildExample = (row) => {
  return [
    `curl -X POST ${location.origin}/api/v1/process-instances/start/ \\`,
    `  -H 'Content-Type: application/json' \\`,
    `  -H 'X-App-Code: ${row.code}' \\`,
    `  -H 'X-App-Key: {{API_KEY}}' \\`,
    `  -d '{"definition_id": 2, "business_key": "demo_001", "initiator_user_id": 1}'`
  ].join('\n')
}

const showExample = (row) => {
  exampleAppName.value = row.name
  exampleText.value = buildExample(row)
  exampleDialogVisible.value = true
}

const copyText = async (text) => {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
}

const copyKey = async () => {
  await copyText(currentApiKey.value)
  ElMessage.success('已复制')
}

const copyExample = async () => {
  await copyText(exampleText.value)
  ElMessage.success('示例已复制')
}

onMounted(() => {
  fetchData()
  loadStats()
})
</script>

<style scoped lang="scss">
.initiator-app-list {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .page-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .page-header-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #e8f3ff;
    color: #409eff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }

  .page-header h1 {
    font-size: 20px;
    font-weight: 700;
    margin: 0;
  }

  .page-header-desc {
    font-size: 13px;
    color: #86909c;
    margin: 2px 0 0;
  }

  .scene-card {
    margin-bottom: 16px;

    .scene-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }
    }

    .scene-block {
      background: #f7faff;
      border: 1px solid #e5e9f2;
      border-radius: 10px;
      padding: 14px 16px;

      .scene-block__head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .scene-block__name {
          font-size: 14px;
          font-weight: 600;
          color: #1d2129;
        }
      }

      .scene-block__desc {
        margin: 0;
        font-size: 13px;
        color: #4e5969;
        line-height: 1.7;

        strong {
          color: #165dff;
        }

        code {
          background: #f2f3f5;
          padding: 1px 5px;
          border-radius: 4px;
        }
      }

      .scene-block__list {
        margin: 0;
        padding-left: 18px;
        font-size: 13px;
        color: #4e5969;
        line-height: 2;

        strong {
          color: #165dff;
        }
      }
    }

    .scene-hint {
      margin: 0;
      font-size: 12.5px;
      color: #86909c;
      line-height: 1.8;
      border-top: 1px dashed #e5e9f2;
      padding-top: 12px;

      strong {
        color: #165dff;
      }
    }
  }

  .endpoint-card {
    margin-bottom: 16px;

    .endpoint {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;

      .endpoint__method {
        background: #165dff;
        color: #fff;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 4px;
      }

      .endpoint__url {
        background: #f2f3f5;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 13px;
        color: #1d2129;
      }
    }

    .endpoint-desc {
      margin: 0;
      font-size: 13px;
      color: #4e5969;
      line-height: 1.8;

      strong {
        color: #165dff;
      }

      code {
        background: #f2f3f5;
        padding: 1px 5px;
        border-radius: 4px;
      }
    }
  }

  .platform-card {
    margin-bottom: 16px;
  }

  .api-catalog-card {
    margin-bottom: 16px;

    .catalog-desc {
      margin: 0 0 14px;
      font-size: 13px;
      color: #4e5969;
      line-height: 1.8;

      strong {
        color: #165dff;
      }
    }

    .method-tag {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      color: #fff;

      &.method--post {
        background: #e8804a;
      }

      &.method--get {
        background: #2f8f6b;
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .code-badge {
    background: #f2f3f5;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: #4e5969;
  }

  .call-total {
    font-weight: 700;
    color: #1d2129;
  }

  .call-last {
    font-size: 12px;
    color: #86909c;
    margin-top: 2px;
  }

  .call-none {
    color: #c9cdd4;
  }

  .key-alert {
    margin-bottom: 14px;
  }

  .key-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: #f7f8fa;
    border: 1px dashed #e5e6eb;
    border-radius: 8px;
    padding: 12px 14px;

    code {
      font-size: 13px;
      color: #1d2129;
      word-break: break-all;
    }
  }

  .example-tip {
    font-size: 13px;
    color: #4e5969;
    line-height: 1.7;
    margin: 0 0 12px;

    code {
      background: #f2f3f5;
      padding: 1px 5px;
      border-radius: 4px;
    }
  }

  .example-box {
    background: #1d2129;
    color: #d9d9d9;
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 12px;
    line-height: 1.8;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
