<template>
  <div class="app-register">
    <PageHeader title="注册应用" desc="配置应用基本信息、网络信息、鉴权方式等">
      <template #actions>
        <button class="btn btn-ghost" @click="router.back()">取消</button>
      </template>
    </PageHeader>

    <div class="register-content">
      <!-- 基本信息 -->
      <div class="section">
        <div class="section-title">📋 基本信息</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="field">
              <label class="field-label">应用 Code <span class="required">*</span></label>
              <input v-model="form.code" class="input" placeholder="如：cmdb、itsm、cloudportal" />
              <div class="field-hint">唯一标识，用于 API 调用和权限点前缀</div>
            </div>
            <div class="field">
              <label class="field-label">应用名称 <span class="required">*</span></label>
              <input v-model="form.name" class="input" placeholder="如：配置管理中心" />
            </div>
            <div class="field">
              <label class="field-label">应用类型</label>
              <select v-model="form.type" class="input select">
                <option :value="1">API 服务</option>
                <option :value="2">数据服务</option>
              </select>
              <div class="field-hint">能力包决定 API/数据维度，此处仅做基础分类</div>
            </div>
            <div class="field">
              <label class="field-label">开发语言</label>
              <select v-model="form.language" class="input select">
                <option value="">未指定</option>
                <option value="Go">Go</option>
                <option value="Java">Java</option>
                <option value="Python">Python</option>
                <option value="Node.js">Node.js</option>
                <option value="TypeScript">TypeScript</option>
                <option value="Rust">Rust</option>
                <option value="C++">C++</option>
                <option value="其他">其他</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">所属组</label>
              <select v-model="form.owner_group_id" class="input select">
                <option :value="undefined">不指定</option>
                <option v-for="g in orgGroups" :key="g.id" :value="g.id">{{ (g.path_names || [g.name]).join(' → ') }}</option>
              </select>
              <div class="field-hint">组织兜底锚点：owner 全部失联时向上兜底</div>
            </div>
            <div class="field full-width">
              <label class="field-label">应用描述</label>
              <textarea v-model="form.description" class="input textarea" placeholder="简要描述应用的功能和用途" rows="3"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- OpenAPI 配置 -->
      <div class="section">
        <div class="section-title">🔗 OpenAPI 配置</div>
        <div class="section-body">
          <!-- 兼容性提示卡片 -->
          <div class="tip-card">
            <span class="tip-icon">💡</span>
            <div class="tip-text">
              <b>OpenAPI 地址兼容 OpenAPI 3.0 与 Swagger 2.0 格式</b>，解析器会自动识别，用于同步生成权限点与能力包。
              <br />若需要面向人的说明文档（操作手册 / 产品文档 / 自写 API 指南），请在下方单独填写「产品文档链接」。
            </div>
          </div>
          <div class="form-grid">
            <div class="field full-width">
              <label class="field-label">OpenAPI URL</label>
              <div class="input-with-btn">
                <input v-model="form.openapi_url" class="input" placeholder="http://localhost:8090/openapi.json" />
                <button class="btn btn-primary" @click="checkOpenAPI" :disabled="!form.openapi_url || checking">
                  {{ checking ? '检查中...' : '🔍 检查' }}
                </button>
              </div>
              <div class="field-hint">填写后点击「检查」验证连通性并预览接口和数据模型数量</div>
              <!-- 检查结果 -->
              <div v-if="openapiResult" class="openapi-result" :class="openapiResult.success ? 'result-success' : 'result-error'">
                <div class="result-content">
                  <div class="result-icon">{{ openapiResult.success ? '✅' : '❌' }}</div>
                  <div class="result-info">
                    <div class="result-title">{{ openapiResult.success ? 'OpenAPI 检查通过' : '检查失败' }}</div>
                    <template v-if="openapiResult.success">
                      <div class="result-stats">
                        <span>📦 接口：{{ openapiResult.actions }} 个</span>
                        <span>🗂️ 数据模型：{{ openapiResult.models }} 个</span>
                      </div>
                    </template>
                    <div v-else class="result-error-msg">{{ openapiResult.error }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="field full-width">
              <label class="field-label">📖 产品文档 / 操作手册链接 <span class="optional">（可选）</span></label>
              <input v-model="form.doc_url" class="input" placeholder="https://docs.example.com/cmdb/manual" />
              <div class="field-hint">面向人的说明文档（操作手册 / 产品文档 / 自写 API 指南），会展示在应用详情与能力包中供申请方查阅</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 网络信息 -->
      <div class="section">
        <div class="section-title">🌐 网络信息</div>
        <div class="section-body">
          <div class="net-group-title">基础设施</div>
          <div class="form-grid">
            <div class="field">
              <label class="field-label">☁️ 云平台</label>
              <input v-model="form.net_info.cloud" class="input" placeholder="AWS / 阿里云 / 私有云" />
            </div>
            <div class="field">
              <label class="field-label">🔑 账号/租户</label>
              <input v-model="form.net_info.account" class="input" placeholder="prod-account-001" />
            </div>
            <div class="field">
              <label class="field-label">🌍 区域/机房</label>
              <input v-model="form.net_info.region" class="input" placeholder="cn-hangzhou / idc-bj-01" />
            </div>
          </div>
          <div class="net-group-title">网络</div>
          <div class="form-grid">
            <div class="field">
              <label class="field-label">🔒 VPC/网络空间</label>
              <input v-model="form.net_info.vpc" class="input" placeholder="vpc-123456" />
            </div>
            <div class="field">
              <label class="field-label">📦 子网</label>
              <input v-model="form.net_info.subnet" class="input" placeholder="subnet-abc123" />
            </div>
            <div class="field">
              <label class="field-label">🛡️ 安全组</label>
              <input v-model="form.net_info.sg" class="input" placeholder="sg-web-servers" />
            </div>
          </div>
          <div class="net-group-title">部署与探测</div>
          <div class="form-grid">
            <div class="field">
              <label class="field-label">🐳 容器/集群</label>
              <input v-model="form.net_info.container" class="input" placeholder="k8s-prod-cluster" />
            </div>
            <div class="field">
              <label class="field-label">💓 健康检查端点</label>
              <input v-model="form.net_info.health" class="input" placeholder="/healthz" />
            </div>
          </div>
          <div class="net-group-title">服务地址</div>
          <div class="form-grid">
            <div class="field">
              <label class="field-label">🏠 内网地址</label>
              <input v-model="form.net_info.internal_url" class="input" placeholder="http://service.internal:8080" />
            </div>
            <div class="field">
              <label class="field-label">🌐 外网地址</label>
              <input v-model="form.net_info.external_url" class="input" placeholder="https://api.example.com" />
            </div>
          </div>
        </div>
      </div>

      <!-- 鉴权方式 -->
      <div class="section">
        <div class="section-title">🔐 鉴权方式</div>
        <div class="section-body">
          <div class="auth-options">
            <label class="auth-option" :class="{ selected: form.auth_methods.includes('jwt') }">
              <input type="checkbox" v-model="form.auth_methods" value="jwt" />
              <div class="auth-icon">🎫</div>
              <div class="auth-info">
                <div class="auth-name">JWT Token</div>
                <div class="auth-desc">基于 JSON Web Token 的无状态鉴权</div>
              </div>
            </label>
            <label class="auth-option" :class="{ selected: form.auth_methods.includes('oauth2') }">
              <input type="checkbox" v-model="form.auth_methods" value="oauth2" />
              <div class="auth-icon">🔑</div>
              <div class="auth-info">
                <div class="auth-name">OAuth 2.0</div>
                <div class="auth-desc">标准授权框架，支持多种授权模式</div>
              </div>
            </label>
            <label class="auth-option" :class="{ selected: form.auth_methods.includes('api_key') }">
              <input type="checkbox" v-model="form.auth_methods" value="api_key" />
              <div class="auth-icon">🗝️</div>
              <div class="auth-info">
                <div class="auth-name">API Key</div>
                <div class="auth-desc">简单的密钥鉴权，适合服务间调用</div>
              </div>
            </label>
            <label class="auth-option" :class="{ selected: form.auth_methods.includes('basic') }">
              <input type="checkbox" v-model="form.auth_methods" value="basic" />
              <div class="auth-icon">👤</div>
              <div class="auth-info">
                <div class="auth-name">Basic Auth</div>
                <div class="auth-desc">用户名密码基础鉴权</div>
              </div>
            </label>
          </div>
        </div>
      </div>

      <!-- 负责人配置 -->
      <div class="section">
        <div class="section-title">👥 负责人配置</div>
        <div class="section-body">
          <div class="form-grid">
            <div class="field full-width">
              <label class="field-label">应用负责人 <span class="required">*</span></label>
              <div class="owner-select">
                <div v-for="(owner, index) in form.owners" :key="index" class="owner-item">
                  <select v-model="form.owners[index]" class="input select">
                    <option value="">请选择负责人</option>
                    <option v-for="user in users" :key="user.id" :value="user.id">{{ user.display_name || user.username }} ({{ user.username }})</option>
                  </select>
                  <button v-if="form.owners.length > 1" class="btn btn-sm btn-danger" @click="removeOwner(index)">移除</button>
                </div>
                <button class="btn btn-sm btn-outline" @click="addOwner">+ 添加负责人</button>
              </div>
              <div class="field-hint">至少需要 2 位负责人，确保应用管理不依赖单人</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-bar">
      <button class="btn" @click="router.back()">取消</button>
      <button class="btn btn-primary" @click="submit" :disabled="!canSubmit">
        {{ submitting ? '注册中...' : '注册应用' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const users = ref<any[]>([])
const orgGroups = ref<any[]>([])
const submitting = ref(false)

const form = reactive({
  code: '',
  name: '',
  type: 1,
  language: '',
  description: '',
  doc_url: '',
  owner_group_id: undefined as number | undefined,
  openapi_url: '',
  net_info: {
    cloud: '',
    account: '',
    region: '',
    vpc: '',
    subnet: '',
    sg: '',
    container: '',
    health: '',
    internal_url: '',
    external_url: ''
  } as Record<string, string>,
  auth_methods: [] as string[],
  owners: [0] as number[]
})

const canSubmit = computed(() => {
  return form.code && form.name && form.owners.filter(o => o > 0).length >= 2 && !submitting.value
})

const checking = ref(false)
const openapiResult = ref<any>(null)

async function checkOpenAPI() {
  if (!form.openapi_url) return
  checking.value = true
  openapiResult.value = null
  try {
    const res = await fetch(form.openapi_url)
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    const spec = await res.json()
    const paths = spec.paths || {}
    const schemas = spec.components?.schemas || spec.definitions || {}
    let actionCount = 0
    for (const path in paths) {
      for (const method in paths[path]) {
        if (['get', 'post', 'put', 'delete', 'patch'].includes(method.toLowerCase())) {
          actionCount++
        }
      }
    }
    openapiResult.value = {
      success: true,
      actions: actionCount,
      models: Object.keys(schemas).length
    }
  } catch (e: any) {
    openapiResult.value = {
      success: false,
      error: e.message || '无法访问 OpenAPI 文档'
    }
  } finally {
    checking.value = false
  }
}

onMounted(async () => {
  try {
    const data = await api.users()
    users.value = (data as any).items || []
    const g = await api.groups()
    orgGroups.value = ((g as any).items || []).filter((x: any) => x.type === 1)
  } catch (e) {
    console.error('Failed to load users/groups', e)
  }
})

function addOwner() {
  form.owners.push(0)
}

function removeOwner(index: number) {
  form.owners.splice(index, 1)
}

async function submit() {
  if (!canSubmit.value) return
  
  submitting.value = true
  try {
    const ownerIds = form.owners.filter(o => o > 0)
    if (ownerIds.length < 2) {
      ElMessage.error('至少需要 2 位负责人')
      return
    }

    // 构建网络信息对象（过滤空值）
    const netInfo: Record<string, string> = {}
    for (const [key, value] of Object.entries(form.net_info)) {
      if (value) netInfo[key] = value
    }

    // 构建鉴权方式对象
    const authMethods = form.auth_methods.map(method => ({
      type: method,
      name: method === 'jwt' ? 'JWT Token' : method === 'oauth2' ? 'OAuth 2.0' : method === 'api_key' ? 'API Key' : 'Basic Auth',
      icon: method === 'jwt' ? '🎫' : method === 'oauth2' ? '🔑' : method === 'api_key' ? '🗝️' : '👤',
      strength: method === 'oauth2' ? 'high' : method === 'jwt' ? 'high' : method === 'api_key' ? 'medium' : 'low',
      strengthLabel: method === 'oauth2' ? '高' : method === 'jwt' ? '高' : method === 'api_key' ? '中' : '低',
      desc: method === 'jwt' ? '基于 JSON Web Token 的无状态鉴权' : method === 'oauth2' ? '标准授权框架，支持多种授权模式' : method === 'api_key' ? '简单的密钥鉴权，适合服务间调用' : '用户名密码基础鉴权'
    }))

    const payload = {
      code: form.code,
      name: form.name,
      type: form.type,
      description: form.description,
      language: form.language,
      doc_url: form.doc_url,
      owner_group_id: form.owner_group_id,
      openapi_url: form.openapi_url,
      net_info: Object.keys(netInfo).length > 0 ? netInfo : undefined,
      auth: authMethods.length > 0 ? authMethods : undefined,
      owner_ids: ownerIds
    }

    const result = await api.registerApp(payload)
    ElMessage.success('应用注册成功')
    router.push(`/apps/${(result as any).app?.id ?? (result as any).id}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.app-register {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  padding-bottom: 100px;
}

.input-with-btn {
  display: flex;
  gap: 8px;
}
.input-with-btn .input { flex: 1; }

.net-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin: 16px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--border);
}
.net-group-title:first-child { margin-top: 0; }

.openapi-result {
  margin-top: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid;
}
.result-success { background: rgba(34,197,94,.08); border-color: rgba(34,197,94,.3); }
.result-error { background: rgba(239,68,68,.08); border-color: rgba(239,68,68,.3); }
.result-content { display: flex; align-items: center; gap: 12px; }
.result-icon { font-size: 20px; }
.result-info { flex: 1; }
.result-title { font-weight: 600; font-size: 14px; }
.result-stats { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.result-error-msg { font-size: 13px; color: var(--danger); margin-top: 2px; }

/* 兼容性提示卡片 */
.tip-card {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 16px;
  margin-bottom: 18px;
  border-radius: 8px;
  background: var(--brand-soft, #eaf1fe);
  border: 1px solid rgba(59,130,246,.25);
}
.tip-icon { font-size: 16px; margin-top: 1px; }
.tip-text { font-size: 13px; color: var(--text); line-height: 1.6; }
.tip-text b { color: var(--brand-strong); }

.register-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}

.section-title {
  padding: 16px 20px;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
}

.section-body {
  padding: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field.full-width {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.field-label .required {
  color: var(--danger);
}

.field-label .optional {
  color: var(--text-tertiary);
  font-weight: 400;
}

.field-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.input {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-card);
  color: var(--text);
  transition: all 0.2s;
}

.input:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-soft);
}

.textarea {
  height: auto;
  padding: 12px;
  resize: vertical;
  min-height: 80px;
}

.select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.auth-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.auth-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-option:hover {
  border-color: var(--brand);
}

.auth-option.selected {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.auth-option input {
  display: none;
}

.auth-icon {
  font-size: 24px;
  margin-top: 2px;
}

.auth-info {
  flex: 1;
}

.auth-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.auth-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

.owner-select {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.owner-item {
  display: flex;
  gap: 12px;
  align-items: center;
}

.owner-item .input {
  flex: 1;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  z-index: 100;
}

.btn {
  height: 40px;
  padding: 0 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:hover {
  background: var(--bg-hover);
}

.btn-primary {
  background: var(--brand);
  color: white;
  border-color: var(--brand);
}

.btn-primary:hover {
  background: var(--brand-strong);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-ghost {
  background: transparent;
  border-color: transparent;
}

.btn-ghost:hover {
  background: var(--bg-hover);
}

.btn-outline {
  background: transparent;
}

.btn-sm {
  height: 32px;
  padding: 0 12px;
  font-size: 12px;
}

.btn-danger {
  color: var(--danger);
  border-color: var(--danger);
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.1);
}
</style>