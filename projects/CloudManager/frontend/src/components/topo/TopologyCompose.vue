<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { graphApi, ticketApi, costApi } from '@/api'
import type { Environment } from '@/types'
import { useUserStore } from '@/stores/user'
import TopoCanvas from './TopoCanvas.vue'
import ResourceDrawer from './ResourceDrawer.vue'
import ServiceDrawer from './ServiceDrawer.vue'
import RelationDrawer from './RelationDrawer.vue'
import RelationDetailDrawer from './RelationDetailDrawer.vue'
import { useRelationEditor } from '@/composables/useRelationEditor'
import type { TopoBox, TopoEdge, ZoneType, ZoneConfig } from './types'

const props = defineProps<{ envId?: number; appId?: number }>()
const router = useRouter()
const userStore = useUserStore()
const editor = useRelationEditor()

const loading = ref(false)
const graph = ref<any>({ nodes: [], edges: [] })
const services = ref<any[]>([])
const endpoints = ref<any[]>([])
const env = ref<Environment | null>(null)

// 控制器状态
const viewMode = ref<'compose' | 'stream'>('compose')
const zoneFilter = ref<'all' | ZoneType>('all')
const editMode = ref<'browse' | 'edit'>('browse')
const activeTab = ref<'graph' | 'services' | 'history' | 'cost'>('graph')

// 抽屉
const resDrawerOpen = ref(false)
const resId = ref<number>()
const svcDrawerOpen = ref(false)
const svc = ref<any>(null)
const edgeDrawerOpen = ref(false)
const edgeSel = ref<TopoEdge | null>(null)
const relationDetailOpen = ref(false)
const selectedEdge = ref<TopoEdge | null>(null)
const selectedEdgeNames = ref<{ source: string; target: string }>({ source: '', target: '' })
const addVisible = ref(false)
const submitting = ref(false)
const addForm = ref({ source: '', target: '', strength: 'hard' })
const changeHistory = ref<any[]>([])

// 成本 Tab（环境 = 账号 + 区域）
const envCost = ref<any>(null)
const costItems = ref<any[]>([])
const costTotal = ref(0)
const costPage = ref(1)
const costLoading = ref(false)
// 成本筛选
function genCostMonths() {
  const arr: string[] = []
  const d = new Date()
  for (let i = 0; i < 6; i++) {
    arr.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
    d.setMonth(d.getMonth() - 1)
  }
  return arr
}
const costMonths = ref<string[]>(genCostMonths())
const costMonth = ref(costMonths.value[0] || '')
const costType = ref('')
const costArea = ref('')
const costKeyword = ref('')
const costTypeOptions = [
  { value: 'instance', label: '云主机' }, { value: 'database', label: '数据库' }, { value: 'cache', label: '缓存' },
  { value: 'disk', label: '云硬盘' }, { value: 'load_balancer', label: '负载均衡' }, { value: 'object_storage', label: '对象存储' },
  { value: 'vpc', label: 'VPC' }, { value: 'subnet', label: '子网' }, { value: 'security_group', label: '安全组' },
  { value: 'gateway', label: '网关' }, { value: 'middleware', label: '中间件' }, { value: 'message_queue', label: '消息队列' },
]
const costAreas = computed(() => (env.value?.region ? [env.value.region] : []))
const costColumns = [
  { title: '资源名称', key: 'resource_name', dataIndex: 'resource_name', ellipsis: true },
  { title: '资源ID', key: 'resource_id', dataIndex: 'resource_id', width: 150, ellipsis: true },
  { title: '类型', key: 'resource_type', dataIndex: 'resource_type', width: 90 },
  { title: '规格', key: 'spec', dataIndex: 'spec', width: 110 },
  { title: '区域', key: 'region', dataIndex: 'region', width: 100 },
  { title: '费用日期', key: 'cost_date', dataIndex: 'cost_date', width: 100 },
  { title: '费用', key: 'cost', dataIndex: 'cost', width: 110, align: 'right' },
  { title: '部门', key: 'department_name', dataIndex: 'department_name', width: 90 },
]

async function loadCostTab() {
  if (!env.value || !props.appId) return
  costLoading.value = true
  try {
    const base = {
      app_id: props.appId,
      account: env.value.account_name || '',
      region: env.value.region || '',
      month: costMonth.value || '',
      resource_type: costType.value,
      area: costArea.value,
      keyword: costKeyword.value,
    }
    const [ov, it] = await Promise.all([
      costApi.environmentCost(base),
      costApi.environmentCostItems({ ...base, page: costPage.value, page_size: 20 }),
    ])
    envCost.value = ov.data
    costItems.value = it.data.results
    costTotal.value = it.data.count
  } catch { /* 静默 */ } finally { costLoading.value = false }
}

async function loadCostPage(p: number) {
  costPage.value = p
  if (!env.value || !props.appId) return
  costLoading.value = true
  try {
    const { data } = await costApi.environmentCostItems({
      app_id: props.appId,
      account: env.value.account_name || '',
      region: env.value.region || '',
      month: costMonth.value || '',
      resource_type: costType.value,
      area: costArea.value,
      keyword: costKeyword.value,
      page: p, page_size: 20,
    })
    costItems.value = data.results
    costTotal.value = data.count
  } catch { /* 静默 */ } finally { costLoading.value = false }
}

function resetCostFilter() {
  costMonth.value = costMonths.value[0] || ''
  costType.value = ''
  costArea.value = ''
  costKeyword.value = ''
  costPage.value = 1
  loadCostTab()
}

// 申请增加预算（预算为应用级，走工单闭环）
const budgetVisible = ref(false)
const applyAmount = ref<number | null>(null)
const applyReason = ref('')
const applying = ref(false)

function openBudget() {
  budgetVisible.value = true
  applyAmount.value = null
  applyReason.value = ''
}

async function submitBudget() {
  if (!envCost.value || !applyAmount.value || applyAmount.value <= 0) {
    message.warning('请输入有效的申请金额')
    return
  }
  applying.value = true
  try {
    const { data } = await costApi.applyBudget({ app_id: envCost.value.id, amount: applyAmount.value, reason: applyReason.value })
    message.success(`✅ ${data.message}`)
    budgetVisible.value = false
    await loadCostTab()
  } catch { message.error('申请失败') } finally { applying.value = false }
}

// 缩放控制
const topoCanvasRef = ref<InstanceType<typeof TopoCanvas>>()
const zoomScale = computed(() => topoCanvasRef.value?.scale ?? 1)

// 6个区域配置（系统构成视图）— 使用百分比铺满整个画布
const composeZones = ref<ZoneConfig[]>([
  { key: 'access', label: '接入区', color: '#06B6D4', icon: '🌐', x: 0, y: 0, w: 0.2, h: 0.72 },
  { key: 'service', label: '服务区', color: '#3B82F6', icon: '⚙️', x: 0.21, y: 0, w: 0.4, h: 0.72 },
  { key: 'middleware', label: '中间件区', color: '#8B5CF6', icon: '🧱', x: 0.62, y: 0, w: 0.36, h: 0.35 },
  { key: 'data', label: '数据区', color: '#F97316', icon: '🗄️', x: 0.62, y: 0.36, w: 0.36, h: 0.36 },
  { key: 'infra', label: '基础设施区', color: '#10B981', icon: '☸️', x: 0.21, y: 0.73, w: 0.4, h: 0.25 },
  { key: 'monitor', label: '监控区', color: '#64748B', icon: '📊', x: 0.62, y: 0.73, w: 0.36, h: 0.25 },
])

// 上下游视图区域 — 使用百分比铺满整个画布
const streamZones = ref<ZoneConfig[]>([
  { key: 'access', label: '上游（依赖本服务）', color: '#06B6D4', icon: '⬆️', x: 0, y: 0, w: 0.3, h: 1 },
  { key: 'service', label: '本服务', color: '#3B82F6', icon: '🎯', x: 0.31, y: 0, w: 0.38, h: 1 },
  { key: 'data', label: '下游（本服务依赖）', color: '#F97316', icon: '⬇️', x: 0.7, y: 0, w: 0.28, h: 1 },
])

const filteredZones = computed(() => {
  const allZones = viewMode.value === 'compose' ? composeZones.value : streamZones.value
  if (zoneFilter.value === 'all') return allZones
  return allZones.filter(z => z.key === zoneFilter.value)
})

const ICONS: Record<string, string> = {
  client: '👤', gateway: '🌐', frontend: '🖥️', backend: '⚙️', worker: '🔧',
  database: '🗄️', cache: '⚡', message_queue: '📨', cluster: '☸️', middleware: '🧱',
}

function iconOf(key: string) { return ICONS[key] || '📦' }
function svcPort(s: any) { const ep = endpoints.value.find(e => e.service === s.id); return ep ? `${ep.protocol}:${ep.port}` : '-' }
function svcInstances(sId: number) { return graph.value.nodes.find((n: any) => n.id === `svc:${sId}`)?.meta?.instances || [] }
const canEdit = computed(() => userStore.hasPermission('cmdb:relation:edit'))

// 构建服务依赖关系
function buildServiceDeps() {
  const deps = { upstream: [] as any[], downstream: [] as any[], self: [] as any[] }
  const svcIds = new Set(services.value.map(s => `svc:${s.id}`))
  
  for (const e of graph.value.edges) {
    if (e.relation_type === 'deployed_on') continue
    const srcSvc = e.source.startsWith('svc:') && svcIds.has(e.source)
    const tgtSvc = e.target.startsWith('svc:') && svcIds.has(e.target)
    
    if (srcSvc && tgtSvc) {
      // 服务间依赖
      deps.downstream.push({ source: e.source, target: e.target, strength: e.strength })
    } else if (srcSvc && !tgtSvc) {
      // 服务依赖资源（下游）
      deps.downstream.push({ source: e.source, target: e.target, strength: e.strength })
    } else if (!srcSvc && tgtSvc) {
      // 资源/其他服务依赖本服务（上游）
      deps.upstream.push({ source: e.source, target: e.target, strength: e.strength })
    }
  }
  return deps
}

// 系统构成视图
function buildCompose() {
  const boxes: TopoBox[] = []
  const DATA_TYPES = ['database', 'cache', 'message_queue']
  const MIDDLEWARE_TYPES = ['cache', 'message_queue']
  
  // 接入区（左侧20%宽度）
  boxes.push({ id: 'client', name: '客户端', icon: '👤', zone: 'access', meta: { port: 'HTTPS 443' }, x: 0.02, y: 0.08, w: 0.16, h: 0.12 })
  const gw = graph.value.nodes.find((n: any) => n.meta?.resource_type === 'gateway')
  if (gw) boxes.push({ id: gw.id, name: gw.name, icon: '🌐', zone: 'access', meta: { port: gw.meta?.port || '80/443' }, x: 0.02, y: 0.28, w: 0.16, h: 0.12, primaryResId: Number(gw.id.split(':')[1]) })

  // 服务区（中间40%宽度）
  const svcBoxes = services.value.map((s, i) => ({
    id: `svc:${s.id}`, name: s.name, icon: iconOf(s.service_type), zone: 'service' as ZoneType,
    meta: { port: svcPort(s), count: svcInstances(s.id).length },
    x: 0.22, y: 0.05 + i * 0.18, w: 0.18, h: 0.15, primaryResId: svcInstances(s.id)[0]?.id
  }))
  boxes.push(...svcBoxes)

  // 中间件区（右上36%宽度）
  const mwBoxes = graph.value.nodes
    .filter((n: any) => n.category === 'resource' && MIDDLEWARE_TYPES.includes(n.meta?.resource_type))
    .map((n: any, i: number) => ({
      id: n.id, name: n.name, icon: iconOf(n.meta?.resource_type), zone: 'middleware' as ZoneType,
      meta: { port: n.meta?.port || '-' }, x: 0.64, y: 0.08 + i * 0.22, w: 0.32, h: 0.18, primaryResId: Number(n.id.split(':')[1])
    }))
  boxes.push(...mwBoxes)

  // 数据区（右下36%宽度）
  const dataBoxes = graph.value.nodes
    .filter((n: any) => n.category === 'resource' && DATA_TYPES.includes(n.meta?.resource_type) && !MIDDLEWARE_TYPES.includes(n.meta?.resource_type))
    .map((n: any, i: number) => ({
      id: n.id, name: n.name, icon: iconOf(n.meta?.resource_type), zone: 'data' as ZoneType,
      meta: { port: n.meta?.port || '-' }, x: 0.64, y: 0.4 + i * 0.22, w: 0.32, h: 0.18, primaryResId: Number(n.id.split(':')[1])
    }))
  boxes.push(...dataBoxes)

  // 基础设施区（底部中间）
  const cluster = graph.value.nodes.find((n: any) => n.meta?.resource_type === 'cluster')
  if (cluster) boxes.push({ id: cluster.id, name: cluster.name, icon: '☸️', zone: 'infra', meta: { port: 'K8s' }, x: 0.22, y: 0.78, w: 0.38, h: 0.18, primaryResId: Number(cluster.id.split(':')[1]) })

  // 边
  const edges = buildEdges(boxes)
  return { boxes, edges }
}

// 上下游视图（服务间依赖）
function buildStream() {
  const boxes: TopoBox[] = []
  const deps = buildServiceDeps()
  const svcIds = new Set(services.value.map(s => `svc:${s.id}`))
  
  // 收集上游服务（依赖本服务的其他服务）
  const upstreamIds = new Set<string>()
  const downstreamIds = new Set<string>()
  
  for (const svc of services.value) {
    const svcId = `svc:${svc.id}`
    // 查找谁依赖这个服务
    for (const e of graph.value.edges) {
      if (e.target === svcId && e.source.startsWith('svc:') && e.source !== svcId) {
        upstreamIds.add(e.source)
      }
    }
    // 查找这个服务依赖谁
    for (const e of graph.value.edges) {
      if (e.source === svcId && e.target.startsWith('svc:') && e.target !== svcId) {
        downstreamIds.add(e.target)
      }
    }
  }
  
  // 上游服务（左30%）
  let upIdx = 0
  for (const svcId of upstreamIds) {
    const s = services.value.find(s => `svc:${s.id}` === svcId)
    if (s) {
      boxes.push({ id: svcId, name: s.name, icon: iconOf(s.service_type), zone: 'access', meta: { port: svcPort(s) }, x: 0.02, y: 0.1 + upIdx * 0.2, w: 0.26, h: 0.15 })
      upIdx++
    }
  }
  
  // 本服务（中38%）
  services.value.forEach((s, i) => {
    boxes.push({ id: `svc:${s.id}`, name: s.name, icon: iconOf(s.service_type), zone: 'service', meta: { port: svcPort(s) }, x: 0.33, y: 0.1 + i * 0.2, w: 0.34, h: 0.15 })
  })
  
  // 下游服务（右28%）
  let downIdx = 0
  for (const svcId of downstreamIds) {
    const s = services.value.find(s => `svc:${s.id}` === svcId)
    if (s) {
      boxes.push({ id: svcId, name: s.name, icon: iconOf(s.service_type), zone: 'data', meta: { port: svcPort(s) }, x: 0.72, y: 0.1 + downIdx * 0.2, w: 0.26, h: 0.15 })
      downIdx++
    }
  }
  
  // 资源下游（数据区右侧）
  const resourceDown: string[] = graph.value.edges
    .filter((e: any) => e.source.startsWith('svc:') && !e.target.startsWith('svc:') && e.relation_type !== 'deployed_on')
    .map((e: any) => e.target as string)
  const uniqueResDown = [...new Set(resourceDown)]
  
  uniqueResDown.forEach((rId, i) => {
    const node = graph.value.nodes.find((n: any) => n.id === rId)
    if (node) {
      boxes.push({ id: rId, name: node.name, icon: iconOf(node.meta?.resource_type), zone: 'data', meta: { port: node.meta?.port || '-' }, x: 0.72, y: 0.1 + (downIdx + i) * 0.15, w: 0.26, h: 0.12, primaryResId: Number(rId.split(':')[1]) })
    }
  })

  const edges = buildEdges(boxes)
  return { boxes, edges }
}

function buildEdges(boxes: TopoBox[]) {
  const edges: TopoEdge[] = []
  const boxIds = new Set(boxes.map(b => b.id))
  const svcOfRes = new Map<number, string>()
  
  // 构建资源到服务的映射
  for (const e of graph.value.edges) {
    if (e.relation_type === 'deployed_on' && e.source.startsWith('svc:')) {
      const resId = Number(e.target.split(':')[1])
      svcOfRes.set(resId, e.source)
    }
  }
  
  // 处理所有边
  for (const e of graph.value.edges) {
    // 跳过 deployed_on（已经通过 svcOfRes 处理）
    if (e.relation_type === 'deployed_on') continue
    
    let src = e.source
    let tgt = e.target
    
    // 如果是资源节点，尝试映射到服务节点
    if (src.startsWith('res:')) {
      const resId = Number(src.split(':')[1])
      const mappedSvc = svcOfRes.get(resId)
      if (mappedSvc && boxIds.has(mappedSvc)) {
        src = mappedSvc
      }
    }
    if (tgt.startsWith('res:')) {
      const resId = Number(tgt.split(':')[1])
      const mappedSvc = svcOfRes.get(resId)
      if (mappedSvc && boxIds.has(mappedSvc)) {
        tgt = mappedSvc
      }
    }
    
    // 只添加两端都在 boxes 中的边
    if (boxIds.has(src) && boxIds.has(tgt) && src !== tgt) {
      edges.push({ 
        source: src, 
        target: tgt, 
        label: e.relation_type === 'depends_on' ? '依赖' : '', 
        strength: e.strength || 'hard', 
        relation_type: e.relation_type 
      })
    }
  }
  
  // 添加客户端到网关的边
  if (boxIds.has('client')) {
    const gw = graph.value.nodes.find((n: any) => n.meta?.resource_type === 'gateway')
    if (gw && boxIds.has(gw.id)) {
      edges.push({ source: 'client', target: gw.id, label: 'HTTPS', strength: 'hard', relation_type: 'upstream' })
    }
  }
  
  // 添加草稿边
  for (const d of editor.draft.value) {
    if (d.action === 'add') {
      edges.push({ source: d.source, target: d.target, label: '草稿', strength: d.strength, relation_type: d.relation_type, pending: true })
    }
  }
  
  // Mock: 添加服务间依赖（如果没有真实数据）
  const svcEdges = edges.filter(e => e.source.startsWith('svc:') && e.target.startsWith('svc:'))
  if (svcEdges.length === 0) {
    const svcs = boxes.filter(b => b.id.startsWith('svc:'))
    // 如果有多个服务，添加模拟依赖
    if (svcs.length >= 2 && svcs[0] && svcs[1]) {
      edges.push({ source: svcs[0].id, target: svcs[1].id, label: 'HTTP', strength: 'hard', relation_type: 'depends_on' })
    }
    if (svcs.length >= 3 && svcs[1] && svcs[2]) {
      edges.push({ source: svcs[1].id, target: svcs[2].id, label: 'gRPC', strength: 'hard', relation_type: 'depends_on' })
    }
  }
  
  return edges
}

const currentData = computed(() => viewMode.value === 'compose' ? buildCompose() : buildStream())
const selectableBoxes = computed(() => currentData.value.boxes.filter(b => b.id !== 'client'))

const svcInstancesArr = computed(() => svc.value ? svcInstances(svc.value.id || svc.value) : [])
const svcPortStr = computed(() => svc.value ? svcPort(svc.value) : '')
const svcDeps = computed(() => {
  if (!svc.value) return []
  const svcId = `svc:${svc.value.id || svc.value}`
  return currentData.value.edges.filter(e => e.source === svcId || e.target === svcId).map(e => {
    const isSource = e.source === svcId
    const otherId = isSource ? e.target : e.source
    const otherBox = currentData.value.boxes.find(b => b.id === otherId)
    return { group: isSource ? 'down' : 'up', name: otherBox?.name || otherId, relation_type: e.relation_type, strength: e.strength, port: otherBox?.meta?.port || '' }
  })
})

function openResourceDetail(id: number) {
  svcDrawerOpen.value = false
  window.open(`/resources/${id}`, '_blank')
}

function handleNodeClick(box: TopoBox) {
  if (box.id === 'client') return
  // 服务节点优先打开 ServiceDrawer（展示全部实例/主机/Pod 清单）
  if (box.id.startsWith('svc:')) {
    svc.value = services.value.find(s => s.id === Number(box.id.split(':')[1])) || box.id
    svcDrawerOpen.value = true
  } else if (box.primaryResId) {
    // 资源节点打开 ResourceDrawer
    resId.value = box.primaryResId
    resDrawerOpen.value = true
  }
}

function handleEdgeClick(edge: TopoEdge) {
  edgeSel.value = edge
  edgeDrawerOpen.value = true
}

function openRelationDetail(edge: TopoEdge) {
  selectedEdge.value = edge
  const sourceBox = currentData.value.boxes.find(b => b.id === edge.source)
  const targetBox = currentData.value.boxes.find(b => b.id === edge.target)
  selectedEdgeNames.value = {
    source: sourceBox?.name || edge.source,
    target: targetBox?.name || edge.target,
  }
  relationDetailOpen.value = true
}
function openAddModal() { addForm.value = { source: '', target: '', strength: 'hard' }; addVisible.value = true }

function addDraft() {
  if (!addForm.value.source || !addForm.value.target || addForm.value.source === addForm.value.target) { message.warning('请选择不同的源和目标'); return }
  const src = selectableBoxes.value.find(b => b.id === addForm.value.source)
  const tgt = selectableBoxes.value.find(b => b.id === addForm.value.target)
  editor.addDraft({ action: 'add', source: addForm.value.source, target: addForm.value.target, sourceName: src?.name || '', targetName: tgt?.name || '', relation_type: 'depends_on', strength: addForm.value.strength })
  message.success('已加入变更草稿'); addVisible.value = false
}

function removeEdgeToDraft() {
  if (!edgeSel.value || edgeSel.value.pending) { message.warning('待生效边需在工单中处理'); return }
  editor.addDraft({ action: 'remove', source: edgeSel.value.source, target: edgeSel.value.target, sourceName: edgeSel.value.source, targetName: edgeSel.value.target, relation_type: edgeSel.value.relation_type, strength: edgeSel.value.strength })
  message.success('已加入变更草稿'); edgeDrawerOpen.value = false
}

async function submitDraft() {
  if (!editor.draft.value.length || !env.value) return
  submitting.value = true
  try {
    const { data } = await graphApi.relationChanges({ title: `关系变更（${editor.draft.value.length}项）`, application_id: env.value.application, environment_id: env.value.id, changes: editor.draft.value.map(d => ({ action: d.action, source_id: Number(d.source.split(':')[1]), target_id: Number(d.target.split(':')[1]), relation_type: d.relation_type, strength: d.strength })) })
    message.success(`工单已提交：${data.ticket_no}`); editor.clearDraft(); router.push(`/ticket/detail/${data.ticket_id}`)
  } catch { message.error('提交失败') } finally { submitting.value = false }
}

async function loadHistory() {
  if (!env.value) return
  try {
    const { data } = await ticketApi.list({ page_size: 20 })
    changeHistory.value = (data.results || []).filter((t: any) => t.request_content?.environment_id === env.value?.id)
  } catch { changeHistory.value = [] }
}

async function loadData() {
  loading.value = true
  try {
    if (props.envId) {
      const [g, svc, ep, det] = await Promise.all([graphApi.environment(props.envId), graphApi.envServices(props.envId), graphApi.envEndpoints(props.envId), graphApi.envDetail(props.envId)])
      graph.value = g.data; services.value = svc.data; endpoints.value = ep.data; env.value = det.data
    } else if (props.appId) {
      const [g, svc, ep] = await Promise.all([graphApi.application(props.appId), graphApi.appServices(props.appId), graphApi.appEndpoints(props.appId)])
      graph.value = g.data; services.value = svc.data; endpoints.value = ep.data
      env.value = { application: props.appId, id: 0, application_name: '', name: '全部环境', env_type: '', env_type_display: '', account_name: '', region: '', services_count: 0 } as any
    }
    await loadHistory()
  } catch { message.error('加载失败') } finally { loading.value = false }
}

watch(() => [props.envId, props.appId], loadData)
watch(() => activeTab.value, (tab) => { if (tab === 'cost') loadCostTab() })
onMounted(loadData)
</script>

<template>
  <a-card size="small" class="topo-card">
    <!-- Tabs -->
    <div class="topo-tabs">
      <div class="topo-tab" :class="{ active: activeTab === 'graph' }" @click="activeTab = 'graph'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
        依赖图谱
      </div>
      <div class="topo-tab" :class="{ active: activeTab === 'services' }" @click="activeTab = 'services'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/></svg>
        服务列表 ({{ services.length }})
      </div>
      <div class="topo-tab" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        变更记录
      </div>
      <div class="topo-tab" :class="{ active: activeTab === 'cost' }" @click="activeTab = 'cost'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        💰 成本
      </div>
    </div>

    <!-- 依赖图谱 -->
    <template v-if="activeTab === 'graph'">
      <!-- 平铺操作栏 -->
      <div class="topo-toolbar">
        <div class="toolbar-group">
          <button class="toolbar-btn" :class="{ active: zoneFilter === 'all' }" @click="zoneFilter = 'all'">全部</button>
          <template v-if="viewMode === 'compose'">
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'access' }" @click="zoneFilter = 'access'">🌐 接入区</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'service' }" @click="zoneFilter = 'service'">⚙️ 服务区</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'middleware' }" @click="zoneFilter = 'middleware'">🧱 中间件</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'data' }" @click="zoneFilter = 'data'">🗄️ 数据区</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'infra' }" @click="zoneFilter = 'infra'">☸️ 基础设施</button>
          </template>
          <template v-else>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'access' }" @click="zoneFilter = 'access'">⬆️ 上游</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'service' }" @click="zoneFilter = 'service'">🎯 本服务</button>
            <button class="toolbar-btn" :class="{ active: zoneFilter === 'data' }" @click="zoneFilter = 'data'">⬇️ 下游</button>
          </template>
        </div>

        <div class="toolbar-divider"></div>

        <div class="toolbar-group">
          <button class="toolbar-btn" :class="{ active: viewMode === 'compose' }" @click="viewMode = 'compose'; zoneFilter = 'all'">系统构成</button>
          <button class="toolbar-btn" :class="{ active: viewMode === 'stream' }" @click="viewMode = 'stream'; zoneFilter = 'all'">上下游</button>
        </div>

        <div class="toolbar-divider"></div>

        <div class="toolbar-group">
          <button class="toolbar-btn" :class="{ active: editMode === 'browse' }" @click="editMode = 'browse'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            浏览
          </button>
          <button class="toolbar-btn" :class="{ active: editMode === 'edit' }" :disabled="!canEdit" @click="editMode = 'edit'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            编辑
          </button>
        </div>

        <div class="toolbar-right">
          <button v-if="editMode === 'edit' && canEdit" class="toolbar-btn primary" @click="openAddModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            添加依赖
          </button>
          <button class="toolbar-btn" :disabled="!editor.draft.value.length" @click="editor.draftVisible.value = true">
            📋 变更草稿
            <span v-if="editor.draft.value.length" class="badge">{{ editor.draft.value.length }}</span>
          </button>
        </div>
      </div>

      <!-- 图例 + 缩放控制 -->
      <div class="topo-legend">
        <span class="legend-label">图例：</span>
        <template v-if="viewMode === 'compose'">
          <a-tag color="cyan">👤 客户端 / 🌐 网关</a-tag>
          <a-tag color="blue">⚙️ 服务</a-tag>
          <a-tag color="purple">🧱 中间件</a-tag>
          <a-tag color="orange">🗄️ 数据</a-tag>
          <a-tag color="green">☸️ 集群</a-tag>
        </template>
        <template v-else>
          <a-tag color="cyan">⬆️ 上游服务</a-tag>
          <a-tag color="blue">🎯 本服务</a-tag>
          <a-tag color="orange">⬇️ 下游服务/资源</a-tag>
        </template>
        <span class="legend-hint">实线=强制 / 虚线=软依赖</span>
        <div class="zoom-controls-inline">
          <button class="zoom-btn-sm" @click="topoCanvasRef?.zoomIn()" title="放大">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </button>
          <span class="zoom-val">{{ Math.round(zoomScale * 100) }}%</span>
          <button class="zoom-btn-sm" @click="topoCanvasRef?.zoomOut()" title="缩小">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </button>
          <button class="zoom-btn-sm" @click="topoCanvasRef?.resetZoom()" title="重置">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          </button>
        </div>
      </div>

      <!-- 画布 -->
      <a-spin :spinning="loading">
        <TopoCanvas ref="topoCanvasRef" :boxes="currentData.boxes" :edges="currentData.edges" :zones="filteredZones" height="580px" @node-click="handleNodeClick" @edge-click="handleEdgeClick" />
      </a-spin>
    </template>

    <!-- 服务列表 -->
    <template v-if="activeTab === 'services'">
      <div class="services-list">
        <div v-for="s in services" :key="s.id" class="service-item" @click="svc = s; svcDrawerOpen = true">
          <div class="service-icon" :style="{ background: s.service_type === 'frontend' ? '#EFF6FF' : s.service_type === 'backend' ? '#F5F3FF' : '#ECFDF5', color: s.service_type === 'frontend' ? '#3B82F6' : s.service_type === 'backend' ? '#8B5CF6' : '#10B981' }">
            {{ iconOf(s.service_type) }}
          </div>
          <div class="service-info">
            <div class="service-name">{{ s.name }}</div>
            <div class="service-meta">{{ s.service_type_display }} · {{ svcPort(s) }} · {{ svcInstances(s.id).length }} 实例</div>
          </div>
          <div class="service-status" :class="s.status">{{ s.status }}</div>
        </div>
        <a-empty v-if="!services.length" description="暂无服务" />
      </div>
    </template>

    <!-- 变更记录 -->
    <template v-if="activeTab === 'history'">
      <div class="history-list">
        <div v-for="t in changeHistory" :key="t.id" class="history-item" @click="router.push(`/ticket/detail/${t.id}`)">
          <div class="history-status" :class="t.status">{{ t.status_display }}</div>
          <div class="history-info">
            <div class="history-title">{{ t.title }}</div>
            <div class="history-meta">{{ t.ticket_no }} · {{ t.created_at }}</div>
          </div>
        </div>
        <a-empty v-if="!changeHistory.length" description="暂无变更记录" />
      </div>
    </template>

    <!-- 成本明细（环境 = 账号 + 区域） -->
    <template v-if="activeTab === 'cost'">
      <div v-if="envCost" class="cost-overview-row">
        <div class="co-item"><span class="co-label">本月成本</span><span class="co-value">¥{{ Number(envCost.month_cost).toLocaleString() }}</span></div>
        <div class="co-item"><span class="co-label">环比上月</span><span class="co-value" :class="envCost.mom_pct > 0 ? 'co-up' : 'co-down'">{{ envCost.mom_pct > 0 ? '+' : '' }}{{ envCost.mom_pct }}%</span></div>
        <div class="co-item"><span class="co-label">预算使用率</span><span class="co-value" :class="envCost.usage_percent >= 90 ? 'co-warn' : ''">{{ envCost.usage_percent }}%</span></div>
        <div class="co-item"><span class="co-label">本月预算</span><span class="co-value">¥{{ Number(envCost.budget_amount).toLocaleString() }}</span></div>
        <div class="co-item"><span class="co-label">费用记录</span><span class="co-value">{{ costTotal }} 条</span></div>
        <div class="co-item co-actions"><a-button size="small" type="primary" @click="openBudget">📝 申请增加预算</a-button></div>
      </div>
      <div class="cost-tab-tip">📍 该环境（{{ env?.account_name }} / {{ env?.region }}）下各资源费用明细：</div>
      <div class="cost-filter-bar">
        <span class="cf-label">筛选：</span>
        <select v-model="costMonth" class="cf-select" @change="costPage = 1; loadCostTab()">
          <option v-for="m in costMonths" :key="m" :value="m">{{ m }}</option>
        </select>
        <select v-model="costType" class="cf-select" @change="costPage = 1; loadCostTab()">
          <option value="">全部类型</option>
          <option v-for="o in costTypeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
        <select v-model="costArea" class="cf-select" @change="costPage = 1; loadCostTab()">
          <option value="">全部区域</option>
          <option v-for="a in costAreas" :key="a" :value="a">{{ a }}</option>
        </select>
        <input v-model="costKeyword" class="cf-input" placeholder="🔍 搜索资源名..." @keyup.enter="costPage = 1; loadCostTab()" />
        <a-button size="small" @click="resetCostFilter">重置</a-button>
      </div>
      <a-table
        :data-source="costItems"
        :columns="costColumns"
        :pagination="{ current: costPage, pageSize: 20, total: costTotal, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }"
        :loading="costLoading"
        size="small"
        row-key="id"
        @change="(pag: any) => loadCostPage(pag.current)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'cost'"><span style="color:#7C3AED;font-weight:600">¥{{ Number(record.cost).toLocaleString() }}</span></template>
          <template v-if="column.key === 'resource_type'"><a-tag>{{ record.resource_type || '-' }}</a-tag></template>
        </template>
      </a-table>
    </template>
  </a-card>

  <!-- 申请增加预算弹窗 -->
  <a-modal v-model:open="budgetVisible" title="📝 申请增加预算" :footer="null" width="480px" :mask-closable="false">
    <a-form layout="vertical">
      <a-form-item label="应用"><span style="font-weight:600">{{ envCost?.name }}</span></a-form-item>
      <a-form-item label="当前预算"><span>¥{{ Number(envCost?.budget_amount || 0).toLocaleString() }}</span></a-form-item>
      <a-form-item label="申请增加金额（元）">
        <a-input-number v-model:value="applyAmount" :min="1" style="width:100%" placeholder="请输入申请金额" />
      </a-form-item>
      <a-form-item label="申请原因">
        <a-textarea v-model:value="applyReason" :rows="3" placeholder="如：业务增长，需要扩容 / 大促活动流量上升..." />
      </a-form-item>
      <div style="display:flex;justify-content:flex-end;gap:10px">
        <a-button @click="budgetVisible = false">取消</a-button>
        <a-button type="primary" :loading="applying" @click="submitBudget">提交申请</a-button>
      </div>
    </a-form>
  </a-modal>

  <!-- 抽屉 -->
  <ResourceDrawer v-model:open="resDrawerOpen" :resource-id="resId" />
  <ServiceDrawer v-model:open="svcDrawerOpen" :service="svc" :instances="svcInstancesArr" :port="svcPortStr" :deps="svcDeps" @instance-click="openResourceDetail" />
  <RelationDrawer v-model:open="edgeDrawerOpen" :edge="edgeSel" :edit-mode="editMode === 'edit' && canEdit" @remove="removeEdgeToDraft" @flip="() => {}" @view-detail="openRelationDetail(edgeSel!)" />
<RelationDetailDrawer v-model:open="relationDetailOpen" :edge="selectedEdge" :source-name="selectedEdgeNames.source" :target-name="selectedEdgeNames.target" />

  <!-- 添加依赖弹窗 -->
  <a-modal v-model:open="addVisible" title="＋ 添加依赖" @ok="addDraft">
    <a-form layout="vertical">
      <a-form-item label="源（依赖方）" required>
        <a-select v-model:value="addForm.source" placeholder="选择源">
          <a-select-option v-for="b in selectableBoxes" :key="b.id" :value="b.id">{{ b.name }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="目标（被依赖方）" required>
        <a-select v-model:value="addForm.target" placeholder="选择目标">
          <a-select-option v-for="b in selectableBoxes" :key="b.id" :value="b.id">{{ b.name }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="强度">
        <a-select v-model:value="addForm.strength">
          <a-select-option value="hard">强制依赖</a-select-option>
          <a-select-option value="soft">软依赖</a-select-option>
        </a-select>
      </a-form-item>
    </a-form>
  </a-modal>

  <!-- 变更草稿抽屉 -->
  <a-drawer v-model:open="editor.draftVisible.value" title="📋 变更草稿" :width="400">
    <div v-for="(d, i) in editor.draft.value" :key="i" class="draft-item">
      <a-tag :color="d.action === 'add' ? 'green' : 'red'">{{ d.action === 'add' ? '新增' : '移除' }}</a-tag>
      <div class="draft-content">
        <div>{{ d.sourceName }} → {{ d.targetName }}</div>
        <div class="draft-meta">{{ d.strength === 'hard' ? '强制' : '软依赖' }}</div>
      </div>
      <a-button size="small" type="link" danger @click="editor.removeDraft(i)">移除</a-button>
    </div>
    <a-empty v-if="!editor.draft.value.length" description="暂无变更" />
    <template #footer>
      <a-space>
        <a-button @click="editor.clearDraft()">清空</a-button>
        <a-button type="primary" :loading="submitting" @click="submitDraft">提交变更</a-button>
      </a-space>
    </template>
  </a-drawer>
</template>

<style scoped>
/* 成本 Tab */
.cost-overview-row { display: flex; align-items: center; gap: 24px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; flex-wrap: wrap; }
.co-item { display: flex; flex-direction: column; gap: 2px; }
.co-label { font-size: 12px; color: #94A3B8; }
.co-value { font-size: 16px; font-weight: 700; color: #1E293B; }
.co-up { color: #EF4444; }
.co-down { color: #10B981; }
.co-warn { color: #F59E0B; }
.co-actions { margin-left: auto; }
.cost-tab-tip { font-size: 13px; color: #64748B; margin-bottom: 10px; }
.cost-filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; }
.cf-label { font-size: 13px; color: #64748B; font-weight: 500; }
.cf-select { height: 30px; padding: 0 8px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; color: #334155; background: white; }
.cf-input { height: 30px; padding: 0 10px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; color: #334155; width: 180px; }
.cf-input:focus { outline: none; border-color: #3B82F6; }
.topo-card { border-radius: 12px; }
.topo-tabs { display: flex; gap: 4px; padding-bottom: 12px; border-bottom: 1px solid #E2E8F0; margin-bottom: 12px; }
.topo-tab { display: flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 14px; color: #64748B; border-bottom: 2px solid transparent; cursor: pointer; transition: 0.2s; }
.topo-tab:hover { color: #1E293B; }
.topo-tab.active { color: #3B82F6; border-bottom-color: #3B82F6; font-weight: 500; }

.topo-toolbar { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.toolbar-group { display: flex; gap: 2px; padding: 3px; background: white; border-radius: 6px; }
.toolbar-btn { display: flex; align-items: center; gap: 4px; padding: 5px 10px; border: none; background: transparent; border-radius: 4px; font-size: 12px; color: #64748B; cursor: pointer; transition: 0.2s; white-space: nowrap; }
.toolbar-btn:hover:not(:disabled) { background: #F1F5F9; color: #1E293B; }
.toolbar-btn.active { background: white; color: #3B82F6; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.toolbar-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.toolbar-btn.primary { background: #3B82F6; color: white; }
.toolbar-btn.primary:hover { background: #2563EB; }
.toolbar-divider { width: 1px; height: 24px; background: #E2E8F0; }
.toolbar-right { margin-left: auto; display: flex; gap: 8px; }
.badge { display: inline-flex; align-items: center; justify-content: center; min-width: 16px; height: 16px; padding: 0 4px; background: #EF4444; color: white; border-radius: 8px; font-size: 10px; font-weight: 500; }

.topo-legend { display: flex; align-items: center; gap: 6px; margin-bottom: 12px; font-size: 12px; flex-wrap: wrap; }
.legend-label { color: #64748B; }
.legend-hint { color: #94A3B8; margin-left: 8px; }
.zoom-controls-inline { display: flex; align-items: center; gap: 2px; margin-left: auto; padding: 2px 4px; background: white; border: 1px solid #E2E8F0; border-radius: 6px; }
.zoom-btn-sm { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; border-radius: 4px; cursor: pointer; color: #64748B; transition: 0.2s; }
.zoom-btn-sm:hover { background: #F1F5F9; color: #1E293B; }
.zoom-val { font-size: 11px; color: #64748B; min-width: 32px; text-align: center; }

.services-list { display: flex; flex-direction: column; gap: 8px; }
.service-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: #F8FAFC; border-radius: 8px; cursor: pointer; transition: 0.2s; }
.service-item:hover { background: #EFF6FF; }
.service-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.service-info { flex: 1; }
.service-name { font-size: 14px; font-weight: 500; }
.service-meta { font-size: 12px; color: #64748B; }
.service-status { padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.service-status.running { background: #D1FAE5; color: #065F46; }
.service-status.stopped { background: #FEE2E2; color: #991B1B; }

.history-list { display: flex; flex-direction: column; gap: 8px; }
.history-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: #F8FAFC; border-radius: 8px; cursor: pointer; transition: 0.2s; }
.history-item:hover { background: #EFF6FF; }
.history-status { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.history-status.pending { background: #FEF3C7; color: #92400E; }
.history-status.success { background: #D1FAE5; color: #065F46; }
.history-status.failed { background: #FEE2E2; color: #991B1B; }
.history-info { flex: 1; }
.history-title { font-size: 14px; font-weight: 500; }
.history-meta { font-size: 12px; color: #64748B; }

.draft-item { display: flex; align-items: center; gap: 8px; padding: 8px; background: #F8FAFC; border-radius: 6px; margin-bottom: 8px; }
.draft-content { flex: 1; font-size: 13px; }
.draft-meta { font-size: 11px; color: #64748B; }
</style>
