<template>
  <div class="policies-page">
    <header class="page-header">
      <h1>策略管理</h1>
      <span class="page-desc">API + 数据级策略，策略即数据</span>
    </header>

    <div class="panel">
      <div class="panel-toolbar">
        <button class="btn btn-primary" @click="showCreate = true">发起授权</button>
        <span class="toolbar-hint">授权即审批：发起后需被授权方确认 + 其他负责人复核，通过后自动生效</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>主体</th>
            <th>效果</th>
            <th>版本</th>
            <th>来源</th>
            <th>数据范围</th>
            <th style="width: 100px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in policies" :key="p.id">
            <td class="mono">{{ p.id }}</td>
            <td>{{ p.name }}</td>
            <td><span class="tag">{{ ['', '用户', '组', '角色', '服务'][p.subject_type] }}</span></td>
            <td><span class="tag" :class="p.effect === 1 ? 'tag-success' : 'tag-danger'">{{ p.effect === 1 ? 'allow' : 'deny' }}</span></td>
            <td class="mono">v{{ p.version }}</td>
            <td><span class="tag" :class="sourceClass(p.source)">{{ sourceLabel(p.source) }}</span></td>
            <td class="mono text-secondary" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ p.resource_scope ? JSON.stringify(p.resource_scope) : '—' }}
            </td>
            <td>
              <button class="btn btn-sm" @click="publish(p)">发布</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="policies.length === 0" class="empty-state">暂无策略</div>
    </div>

    <el-dialog v-model="showCreate" title="发起授权（授权即审批）" width="600">
      <el-form label-width="90">
        <el-form-item label="被授权主体">
          <div class="subject-row">
            <el-select v-model="form.subject_type" style="width: 120px;">
              <el-option :value="1" label="用户" />
              <el-option :value="2" label="组" />
              <el-option :value="4" label="服务" />
            </el-select>
            <el-input-number v-model="form.subject_id" :min="1" style="flex: 1;" />
          </div>
        </el-form-item>
        <el-form-item label="应用">
          <el-select v-model="form.app_id" filterable style="width: 100%;">
            <el-option v-for="a in apps" :key="a.id" :label="`${a.code} — ${a.name}`" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口权限">
          <el-select v-model="form.action_ids" multiple filterable placeholder="选择要授予的接口动作">
            <el-option v-for="a in allActions" :key="a.id" :label="a.code" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据模型">
          <el-select v-model="form.scope_model" clearable placeholder="选择后为数据级授权（实例范围）">
            <el-option v-for="m in models" :key="m.id" :label="m.code" :value="m.code" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.scope_model" label="勾选实例">
          <el-select v-model="form.scope_instances" multiple filterable>
            <el-option v-for="i in instances" :key="i.id" :label="`${i.external_id}（${i.name}）`" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期(天)">
          <el-input-number v-model="form.ttl_days" :min="0" :max="365" /> <span class="text-secondary" style="font-size: 12px; margin-left: 8px;">0 = 永久</span>
        </el-form-item>
        <el-form-item label="授权理由">
          <el-input v-model="form.reason" type="textarea" :rows="2" placeholder="为什么给他/她/它这个权限（必填，审批与留痕依据）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showCreate = false">取消</button>
        <button class="btn btn-primary" :disabled="!form.reason" @click="create">提交授权申请单</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const policies = ref<any[]>([])
const apps = ref<any[]>([])
const allActions = ref<any[]>([])
const models = ref<any[]>([])
const instances = ref<any[]>([])
const showCreate = ref(false)
const form = reactive({
  effect: 1, subject_type: 1, subject_id: 1, app_id: undefined as number | undefined,
  action_ids: [] as number[], scope_model: '', scope_instances: [] as number[],
  ttl_days: 0, reason: '',
})

function sourceLabel(s: number) { return { 1: 'owner', 2: '申请', 3: '应用间' }[s] || '—' }
function sourceClass(s: number) { return { 1: 'tag-success', 2: 'tag-warning', 3: 'tag' }[s] || '' }

async function load() {
  const p = await api.policies()
  policies.value = (p as any).items
  const a = await api.apps()
  apps.value = (a as any).items
  const m = await api.resourceModels()
  models.value = (m as any).items
}
onMounted(load)

watch(() => form.app_id, async (id) => {
  if (!id) return
  const d = await api.actions(id)
  allActions.value = (d as any).items
})

watch(() => form.scope_model, async (code) => {
  if (!code) return
  const m = models.value.find((x: any) => x.code === code)
  if (m) {
    const d = await api.instances(m.id)
    instances.value = (d as any).items
  }
})

// 直授表单 = 能力包发放两形态之二（清单 2.6.3）：**授权即审批**——owner 自由勾选动作+实例+TTL+
// 理由必填，createPolicy 直接落策略（source=owner），不走审批流：授权者身份即审批留痕；
// TTL 到期回收防游离授权碎片（对标 AWS 反模式 inline policy）。与"能力市场按包申请"（申请式）并存。
async function create() {
  if (!form.reason) {
    ElMessage.warning('请填写授权理由（留痕依据）')
    return
  }
  if (!form.app_id) {
    ElMessage.warning('请选择应用')
    return
  }
  const resource_scope = form.scope_model
    ? { model: form.scope_model, operation: 'read', instance_ids: form.scope_instances }
    : null
  const expires_at = form.ttl_days > 0
    ? new Date(Date.now() + form.ttl_days * 86400000).toISOString()
    : null
  const res: any = await api.createPolicy({
    name: `grant:console:${Date.now()}`,
    effect: form.effect,
    subject_type: form.subject_type,
    subject_id: form.subject_id,
    app_id: form.app_id,
    action_ids: form.action_ids,
    resource_scope,
    conditions: {},
    force_remote: false,
    reason: form.reason,
    expires_at,
  })
  ElMessage.success(`授权申请单 #${res.id} 已提交，等待审批后生效`)
  showCreate.value = false
  load()
}

async function publish(row: any) {
  await api.publishPolicy(row.id)
  ElMessage.success(`策略 ${row.id} 已发布（v${row.version + 1}）`)
  load()
}
</script>

<style scoped>
.policies-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.panel { border: 1px solid var(--border); background: var(--bg); }
.panel-toolbar { display: flex; justify-content: flex-end; align-items: center; gap: 16px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.toolbar-hint { font-size: 12px; color: var(--text-secondary); }
.subject-row { display: flex; gap: 8px; width: 100%; }

.btn { padding: 6px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-primary:hover { opacity: 0.9; }
.btn-sm { padding: 4px 12px; font-size: 11px; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 16px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); }
.data-table tr:hover td { background: var(--bg-hover); }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-success { background: var(--success-bg); }
.tag-danger { background: var(--danger-bg); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
