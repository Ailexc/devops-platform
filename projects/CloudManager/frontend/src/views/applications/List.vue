<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { graphApi } from '@/api'
import type { OrgTreeNode, Environment, AppDetail } from '@/types'
import TopologyCompose from '@/components/topo/TopologyCompose.vue'

const router = useRouter()
const loading = ref(false)
const orgs = ref<OrgTreeNode[]>([])
const selectedKey = ref('')
const orgPanelCollapsed = ref(false)
const expandedKeys = ref<string[]>([])

type ViewState = { type: 'dept' } | { type: 'app'; id: number } | { type: 'env'; id: number; appId: number }
const view = ref<ViewState>({ type: 'dept' })
const deptApps = ref<any[]>([])
const app = ref<AppDetail | null>(null)
const appEnvs = ref<Environment[]>([])
const selectedEnvId = ref<number | null>(null)
const env = ref<Environment | null>(null)

// 部署单元数据（从环境服务动态加载）
const deployUnits = ref<any[]>([])

const envTypeColor: Record<string, string> = { dev: 'green', test: 'blue', staging: 'orange', prod: 'red' }
const deployPolicy: Record<string, string> = { prod: '主机 (EC2) + 容器 (EKS)', staging: '主机 + 容器', test: '仅容器 (EKS/TKE)', dev: '仅容器' }

async function loadTree() {
  loading.value = true
  try {
    const { data } = await graphApi.organization()
    orgs.value = data
  } catch { message.error('加载组织架构失败') }
  finally { loading.value = false }
}

function findDept(id: number, list: OrgTreeNode[] = orgs.value): OrgTreeNode | null {
  for (const d of list) {
    if (d.id === id) return d
    const child = findDept(id, d.children || [])
    if (child) return child
  }
  return null
}

function selectDept(id: number) {
  const dept = findDept(id)
  view.value = { type: 'dept' }
  deptApps.value = dept?.applications || []
  selectedKey.value = `dept:${id}`
}

async function selectApp(id: number) {
  view.value = { type: 'app', id }
  selectedKey.value = `app:${id}`
  selectedEnvId.value = null
  env.value = null
  loading.value = true
  try {
    const [detail, envList] = await Promise.all([graphApi.appDetail(id), graphApi.applicationEnvs(id)])
    app.value = detail.data
    appEnvs.value = envList.data
  } catch { message.error('加载应用详情失败') }
  finally { loading.value = false }
}

async function onEnvChange(envId: number) {
  if (!envId || !app.value) { env.value = null; return }
  selectedEnvId.value = envId
  view.value = { type: 'env', id: envId, appId: app.value.id }
  loading.value = true
  try {
    const [envRes, svcRes] = await Promise.all([
      graphApi.envDetail(envId),
      graphApi.envServices(envId),
    ])
    env.value = envRes.data
    // 从服务数据动态构建部署单元
    const svcList: any[] = svcRes.data || []
    deployUnits.value = svcList.map((s: any) => ({
      id: s.id,
      name: s.name,
      type: s.deploy_type === 'eks' ? 'k8s' : 'vm',
      spec: s.resource_spec || s.deploy_type_display || '-',
      instances: s.resources_count || (s.resource_name ? 1 : 0),
      cpu: '-',
      service_type: s.service_type,
      status: s.status,
    }))
  } catch { message.error('加载环境详情失败') }
  finally { loading.value = false }
}

function handleTreeClick(key: string) {
  if (!key) return
  const [type, idStr] = key.split(':')
  const id = Number(idStr)
  if (type === 'dept') {
    // 点击部门时，同时展开/收起
    toggleTreeExpand(key)
    selectDept(id)
  } else if (type === 'app') {
    selectApp(id)
  }
}

function toggleTreeExpand(key: string, event?: Event) {
  event?.stopPropagation()
  const idx = expandedKeys.value.indexOf(key)
  if (idx > -1) expandedKeys.value.splice(idx, 1)
  else expandedKeys.value.push(key)
}

onMounted(loadTree)
</script>

<template>
  <div class="app-page">
    <!-- 面包屑 -->
    <div class="breadcrumb">
      <a @click.prevent="view = { type: 'dept' }">应用中心</a>
      <span>/</span>
      <template v-if="view.type === 'app' && app">
        <span>{{ app.department_name || '技术部' }}</span>
        <span>/</span>
        <span class="current">{{ app.name }}</span>
      </template>
      <template v-else-if="view.type === 'env' && env">
        <a @click.prevent="selectApp(env.application)">{{ env.application_name }}</a>
        <span>/</span>
        <span class="current">{{ env.name }}环境</span>
      </template>
      <template v-else>
        <span class="current">组织架构</span>
      </template>
    </div>

    <!-- 组织架构面板 -->
    <div class="org-panel">
      <div class="org-panel-header" @click="orgPanelCollapsed = !orgPanelCollapsed">
        <div class="org-panel-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          组织架构
        </div>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          :style="{ transform: orgPanelCollapsed ? 'rotate(-90deg)' : '', transition: '0.2s' }">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
      <div class="org-panel-body" v-show="!orgPanelCollapsed">
        <template v-for="dept in orgs" :key="dept.id">
          <!-- 部门：整行可点击展开 -->
          <div class="tree-item" :class="{ active: selectedKey === `dept:${dept.id}` }" @click="handleTreeClick(`dept:${dept.id}`)">
            <span class="tree-toggle" :class="{ expanded: expandedKeys.includes(`dept:${dept.id}`) }" @click="toggleTreeExpand(`dept:${dept.id}`, $event)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </span>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <span>{{ dept.name }}</span>
          </div>
          <!-- 应用列表 -->
          <div class="tree-children" v-show="expandedKeys.includes(`dept:${dept.id}`)">
            <div v-for="a in dept.applications" :key="`app:${a.id}`" class="tree-item" :class="{ active: selectedKey === `app:${a.id}` }" @click="handleTreeClick(`app:${a.id}`)">
              <span style="width:16px"></span>
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              <span>{{ a.name }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content" v-if="view.type !== 'dept'">
      <!-- 应用信息卡片 + 环境选择下拉 -->
      <div class="env-info-card" v-if="app">
        <div class="env-info-header">
          <div class="env-info-title">
            <span class="env-type-badge prod">{{ app.app_type_display || '应用' }}</span>
            {{ app.name }}
          </div>
          <div class="env-selector">
            <label>选择环境：</label>
            <select class="env-select" :value="selectedEnvId || ''" @change="onEnvChange(Number(($event.target as HTMLSelectElement).value))">
              <option value="" disabled>请选择环境...</option>
              <option v-for="e in appEnvs" :key="e.id" :value="e.id">
                {{ e.name }} ({{ e.env_type_display }})
              </option>
            </select>
          </div>
        </div>
        <div class="env-info-grid">
          <div class="env-info-item"><span class="env-info-label">所属组织</span><span class="env-info-value">{{ app.department_name || '-' }}</span></div>
          <div class="env-info-item"><span class="env-info-label">技术框架</span><span class="env-info-value">{{ app.framework || '-' }}</span></div>
          <div class="env-info-item"><span class="env-info-label">环境数量</span><span class="env-info-value">{{ appEnvs.length }} 个</span></div>
          <div class="env-info-item"><span class="env-info-label">重要级别</span><span class="env-info-value"><a-tag :color="app.importance_level === 'P0' ? 'red' : 'blue'">{{ app.importance_level || 'P2' }}</a-tag></span></div>
        </div>
      </div>

      <!-- 未选择环境时的提示 -->
      <div v-if="!selectedEnvId && view.type !== 'env'" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="1.5">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <p>请选择环境以查看依赖图谱</p>
      </div>

      <!-- 环境详情 + 依赖图谱（选择环境后显示） -->
      <template v-if="selectedEnvId && env">
        <!-- 环境详情卡片 -->
        <div class="env-detail-card">
          <div class="env-detail-header">
            <div class="env-detail-title">
              <span class="env-type-badge" :class="env.env_type">{{ env.env_type_display }}</span>
              {{ env.name }}环境
              <span class="cloud-badge" :class="env.account_name?.includes('AWS') ? 'aws' : 'tencent'">
                {{ env.account_name?.includes('AWS') ? 'AWS' : '腾讯云' }}
              </span>
            </div>
            <div class="env-deploy-rule">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              允许部署：{{ deployPolicy[env.env_type] || '容器' }}
            </div>
          </div>
          <div class="env-info-grid">
            <div class="env-info-item"><span class="env-info-label">云厂商</span><span class="env-info-value">{{ env.account_name || '-' }}</span></div>
            <div class="env-info-item"><span class="env-info-label">地域</span><span class="env-info-value">{{ env.region || '-' }}</span></div>
            <div class="env-info-item"><span class="env-info-label">服务数</span><span class="env-info-value">{{ env.services_count }}</span></div>
            <div class="env-info-item"><span class="env-info-label">描述</span><span class="env-info-value">{{ env.description || '-' }}</span></div>
          </div>
          <!-- 部署单元 -->
          <div class="deploy-legend">
            <span class="legend-title">基础设施（服务部署单元）：</span>
            <div class="legend-item"><span class="legend-dot vm"></span> 主机</div>
            <div class="legend-item"><span class="legend-dot k8s"></span> 容器</div>
          </div>
          <div class="deploy-units">
            <div v-for="unit in deployUnits" :key="unit.id" class="deploy-unit">
              <div class="deploy-unit-header">
                <div class="deploy-unit-name">
                  <svg v-if="unit.type === 'vm'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>
                  {{ unit.name }}
                </div>
                <span class="deploy-unit-type" :class="unit.type">{{ unit.type === 'vm' ? '主机' : '容器' }}</span>
              </div>
              <div class="deploy-unit-meta">
                <span>{{ unit.instances }} 实例</span>
                <span>{{ unit.spec }}</span>
                <span class="deploy-unit-status" :class="unit.status">{{ unit.status === 'running' ? '运行中' : unit.status }}</span>
              </div>
            </div>
            <a-empty v-if="!deployUnits.length" description="暂无部署单元" :image-style="{ height: '40px' }" />
          </div>
        </div>

        <!-- 依赖图谱 -->
        <TopologyCompose :env-id="selectedEnvId" :app-id="app?.id" />
      </template>
    </div>

    <!-- 默认状态 -->
    <div v-else class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="1.5">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg>
      <p>请选择左侧应用</p>
    </div>
  </div>
</template>

<style scoped>
.app-page { padding: 0; }

/* 应用成本管理 */
.app-cost-card { background: white; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.cost-head { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #E2E8F0; }
.cost-title { font-size: 14px; font-weight: 600; color: #1E293B; }
.cost-sub { font-size: 12px; color: #94A3B8; font-weight: 400; margin-left: 4px; }
.cost-head-right { display: flex; align-items: center; gap: 10px; }
.cost-ticket-hint { font-size: 12px; color: #7C3AED; }
.cost-stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0; border-bottom: 1px solid #E2E8F0; }
.cs { padding: 14px 16px; border-right: 1px solid #F1F5F9; }
.cs:last-child { border-right: none; }
.csv { font-size: 18px; font-weight: 700; color: #1E293B; }
.csv.up { color: #EF4444; }
.csv.down { color: #10B981; }
.csv.warn { color: #F59E0B; }
.csl { font-size: 12px; color: #64748B; margin-top: 4px; }
.cost-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.cost-chart-card { padding: 12px 16px; border-right: 1px solid #F1F5F9; }
.cost-chart-card:last-child { border-right: none; }
.cc-title { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 8px; }

.breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #64748B; margin-bottom: 16px; }
.breadcrumb a { color: #3B82F6; text-decoration: none; cursor: pointer; }
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb span { color: #E2E8F0; }
.breadcrumb .current { color: #1E293B; font-weight: 500; }

.org-panel { background: white; border: 1px solid #E2E8F0; border-radius: 12px; margin-bottom: 16px; }
.org-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #E2E8F0; cursor: pointer; }
.org-panel-header:hover { background: #F8FAFC; }
.org-panel-title { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; }
.org-panel-body { padding: 8px; max-height: 300px; overflow-y: auto; }

.tree-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; font-size: 14px; cursor: pointer; transition: 0.2s; user-select: none; }
.tree-item:hover { background: #F1F5F9; }
.tree-item.active { background: #EFF6FF; color: #2563EB; }
.tree-item .icon { width: 18px; height: 18px; flex-shrink: 0; }
.tree-toggle { width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; transition: 0.2s; flex-shrink: 0; }
.tree-toggle.expanded { transform: rotate(90deg); }
.tree-children { padding-left: 24px; }

.main-content { min-height: 500px; }

.env-info-card { background: #F8FAFC; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; }
.env-info-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 12px; }
.env-info-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }
.env-type-badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.env-type-badge.prod { background: #FEE2E2; color: #991B1B; }
.env-type-badge.staging { background: #FEF3C7; color: #92400E; }
.env-type-badge.test { background: #DBEAFE; color: #1E40AF; }
.env-type-badge.dev { background: #D1FAE5; color: #065F46; }
.cloud-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.cloud-badge.aws { background: #FFF4E5; color: #B7570A; }
.cloud-badge.tencent { background: #E6F4FF; color: #0052CC; }

.env-selector { display: flex; align-items: center; gap: 8px; }
.env-selector label { font-size: 13px; color: #64748B; }
.env-select { padding: 8px 12px; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; background: white; cursor: pointer; min-width: 200px; }
.env-select:focus { outline: none; border-color: #3B82F6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }

.env-detail-card { background: #F8FAFC; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; }
.env-detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.env-detail-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
.env-deploy-rule { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 12px; color: #64748B; }

.env-info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
.env-info-item { display: flex; flex-direction: column; gap: 4px; }
.env-info-label { font-size: 11px; color: #64748B; text-transform: uppercase; }
.env-info-value { font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 6px; }

.deploy-legend { display: flex; align-items: center; gap: 16px; padding: 8px 12px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; margin: 12px 0; font-size: 12px; }
.legend-title { font-weight: 500; color: #64748B; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 8px; height: 8px; border-radius: 2px; }
.legend-dot.vm { background: #6366F1; }
.legend-dot.k8s { background: #10B981; }

.deploy-units { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.deploy-unit { background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }
.deploy-unit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.deploy-unit-name { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 500; }
.deploy-unit-type { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.deploy-unit-type.vm { background: #E0E7FF; color: #3730A3; }
.deploy-unit-type.k8s { background: #D1FAE5; color: #065F46; }
.deploy-unit-meta { display: flex; gap: 12px; font-size: 12px; color: #64748B; }
.deploy-unit-status { font-weight: 500; }
.deploy-unit-status.running { color: #10B981; }
.deploy-unit-status.stopped { color: #EF4444; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; }
.empty-state p { margin-top: 16px; color: #94A3B8; font-size: 14px; }
</style>
