<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{ 
  focus?: string
  view?: string
  selectedNode?: string
  analysisMode?: boolean
  addDependencyMode?: boolean
  mainTab?: string
}>()

const currentView = ref(props.view || 'service')
const currentNode = ref(props.selectedNode || null)
const mainTab = ref<'graph' | 'services' | 'changes' | 'cost'>(props.mainTab as any || 'graph')

watch(() => props.view, (v) => { if (v) currentView.value = v })
watch(() => props.selectedNode, (v) => { if (v) currentNode.value = v })
watch(() => props.analysisMode, (v) => { if (v) currentNode.value = 'order' })
watch(() => props.mainTab, (v) => { if (v) mainTab.value = v as any })

const serviceNodes = [
  { id: 'gateway', name: 'API Gateway', type: 'gateway', x: 200, y: 30, color: '#667eea', status: 'healthy' },
  { id: 'web', name: 'Web 服务', type: 'service', x: 80, y: 100, color: '#10b981', status: 'healthy' },
  { id: 'user', name: '用户服务', type: 'service', x: 320, y: 100, color: '#f59e0b', status: 'healthy' },
  { id: 'order', name: '订单服务', type: 'service', x: 200, y: 100, color: '#3b82f6', status: 'warning' },
  { id: 'mysql', name: 'MySQL', type: 'database', x: 60, y: 190, color: '#8b5cf6', status: 'healthy' },
  { id: 'redis', name: 'Redis', type: 'cache', x: 160, y: 190, color: '#ef4444', status: 'healthy' },
  { id: 'mongo', name: 'MongoDB', type: 'database', x: 260, y: 190, color: '#06b6d4', status: 'healthy' },
  { id: 's3', name: 'S3 存储', type: 'storage', x: 360, y: 190, color: '#84cc16', status: 'healthy' },
]

// 上下游视图节点
const upstreamNodes = [
  { id: 'iam', name: 'IAM 认证', type: '上游应用', x: 80, y: 30, color: '#8b5cf6', status: 'healthy' },
  { id: 'log', name: '日志平台', type: '上游应用', x: 200, y: 30, color: '#f59e0b', status: 'healthy' },
  { id: 'cm', name: 'Cloud Manager', type: '本系统', x: 200, y: 110, color: '#667eea', status: 'healthy' },
  { id: 'cmdb', name: 'CMDB', type: '下游系统', x: 80, y: 190, color: '#10b981', status: 'healthy' },
  { id: 'ticket', name: '工单系统', type: '下游系统', x: 200, y: 190, color: '#ef4444', status: 'healthy' },
  { id: 'monitor', name: '监控平台', type: '下游系统', x: 320, y: 190, color: '#06b6d4', status: 'healthy' },
]

const serviceEdges = [
  { from: 'gateway', to: 'web' }, { from: 'gateway', to: 'user' }, { from: 'gateway', to: 'order' },
  { from: 'web', to: 'mysql' }, { from: 'web', to: 'redis' },
  { from: 'user', to: 'mysql' }, { from: 'user', to: 'redis' },
  { from: 'order', to: 'mongo' }, { from: 'order', to: 'redis' }, { from: 'order', to: 's3' },
]

const upstreamEdges = [
  { from: 'iam', to: 'cm' }, { from: 'log', to: 'cm' },
  { from: 'cm', to: 'cmdb' }, { from: 'cm', to: 'ticket' }, { from: 'cm', to: 'monitor' },
]

const currentNodes = computed(() => {
  if (currentView.value === 'upstream') return upstreamNodes
  return serviceNodes
})

const currentEdges = computed(() => {
  if (currentView.value === 'upstream') return upstreamEdges
  return serviceEdges
})

const nodeDetails: Record<string, any> = {
  gateway: { name: 'API Gateway', type: '网关', port: 443, instances: 2, cpu: 35, memory: 42, upstream: [], downstream: ['Web 服务', '用户服务', '订单服务'], health: 'healthy' },
  web: { name: 'Web 服务', type: '服务', port: 8080, instances: 3, cpu: 45, memory: 67, upstream: ['API Gateway'], downstream: ['MySQL', 'Redis'], health: 'healthy' },
  user: { name: '用户服务', type: '服务', port: 8081, instances: 2, cpu: 38, memory: 52, upstream: ['API Gateway'], downstream: ['MySQL', 'Redis'], health: 'healthy' },
  order: { name: '订单服务', type: '服务', port: 8082, instances: 3, cpu: 72, memory: 78, upstream: ['API Gateway'], downstream: ['MongoDB', 'Redis', 'S3 存储'], health: 'warning' },
  mysql: { name: 'MySQL', type: '数据库', port: 3306, instances: 2, cpu: 55, memory: 72, upstream: ['Web 服务', '用户服务'], downstream: [], health: 'healthy' },
  redis: { name: 'Redis', type: '缓存', port: 6379, instances: 3, cpu: 28, memory: 45, upstream: ['Web 服务', '用户服务', '订单服务'], downstream: [], health: 'healthy' },
  mongo: { name: 'MongoDB', type: '数据库', port: 27017, instances: 3, cpu: 42, memory: 58, upstream: ['订单服务'], downstream: [], health: 'healthy' },
  s3: { name: 'S3 存储', type: '存储', port: 443, instances: 1, cpu: 15, memory: 20, upstream: ['订单服务'], downstream: [], health: 'healthy' },
  iam: { name: 'IAM 认证', type: '上游应用', port: 443, instances: 2, cpu: 30, memory: 35, upstream: [], downstream: ['Cloud Manager'], health: 'healthy' },
  log: { name: '日志平台', type: '上游应用', port: 8080, instances: 3, cpu: 45, memory: 60, upstream: [], downstream: ['Cloud Manager'], health: 'healthy' },
  cm: { name: 'Cloud Manager', type: '本系统', port: 8080, instances: 4, cpu: 52, memory: 68, upstream: ['IAM 认证', '日志平台'], downstream: ['CMDB', '工单系统', '监控平台'], health: 'healthy' },
  cmdb: { name: 'CMDB', type: '下游系统', port: 8080, instances: 2, cpu: 40, memory: 55, upstream: ['Cloud Manager'], downstream: [], health: 'healthy' },
  ticket: { name: '工单系统', type: '下游系统', port: 8080, instances: 2, cpu: 35, memory: 45, upstream: ['Cloud Manager'], downstream: [], health: 'healthy' },
  monitor: { name: '监控平台', type: '下游系统', port: 3000, instances: 3, cpu: 55, memory: 70, upstream: ['Cloud Manager'], downstream: [], health: 'healthy' },
}

const impactAnalysis = { node: '订单服务', upstream: ['API Gateway'], downstream: ['MongoDB', 'Redis', 'S3 存储'], affectedUsers: 1250 }

const typeIcons: Record<string, string> = { gateway: '🌐', service: '⚙️', database: '🗄️', cache: '⚡', storage: '💾', 网关: '🌐', 服务: '⚙️', 数据库: '🗄️', 缓存: '⚡', 存储: '💾' }

// 主 Tab（依赖图谱 / 服务列表 / 变更记录 / 💰 成本）

// 服务列表
const services = [
  { name: '前端', type: '主机', instances: 1, spec: 'ecs.g6.2xlarge', status: '运行中' },
  { name: '后端', type: '主机', instances: 1, spec: 't3.large', status: '运行中' },
]

// 变更记录
const changes = [
  { time: '2026-08-12 16:40', user: '只读用户', action: '更新配置', target: '后端 · 环境变量 DATABASE_URL', result: '成功' },
  { time: '2026-08-11 10:12', user: 'admin', action: '变更规格', target: '前端 · ecs.g6.large → ecs.g6.2xlarge', result: '成功' },
  { time: '2026-08-09 14:05', user: '只读用户', action: '部署版本', target: '后端 · v2.4.1 → v2.5.0', result: '成功' },
  { time: '2026-08-06 09:30', user: 'admin', action: '重启服务', target: '前端 · 滚动重启', result: '成功' },
]

// 环境成本（对齐真实：订单中心 dev，70 条，¥20,316.93）
const envCostOverview = [
  { label: '本月成本', value: '¥20,316.93', color: '#0f172a' },
  { label: '环比上月', value: '-14%', color: '#10b981' },
  { label: '预算使用率', value: '10.2%', color: '#7c3aed' },
  { label: '本月预算', value: '¥200,000', color: '#0f172a' },
  { label: '费用记录', value: '70 条', color: '#0f172a' },
]
const envCostRows = [
  { name: 'lb-cn-004', id: 'lb-06f20b85081e', type: 'load_balancer', spec: 'slb.s1.small', cost: 660.72, date: '2026-08-20', dept: '财务部' },
  { name: 'subnet-cn-001', id: 'subnet-3273a5dbf89d', type: 'subnet', spec: '', cost: 649.82, date: '2026-08-09', dept: '技术部' },
  { name: 'api-cn-009', id: 'i-d8f96e1c021c', type: 'instance', spec: 't3.xlarge', cost: 545.27, date: '2026-08-10', dept: '研发组' },
  { name: 'vpc-cn-003', id: 'vpc-ac9a70ba076d', type: 'vpc', spec: '', cost: 536.6, date: '2026-08-28', dept: '研发组' },
  { name: 'sg-cn-005', id: 'sg-87e8d8c8d92f', type: 'security_group', spec: '', cost: 521.64, date: '2026-08-23', dept: '运维组' },
]

function selectNode(id: string) { currentNode.value = id }
</script>

<template>
  <div class="topo-sim">
    <div class="topo-header">
      <div class="header-left">
        <h2>🔗 依赖图谱</h2>
        <span class="app-tag">Cloud Manager · 生产环境</span>
      </div>
      <div class="header-right">
        <div class="main-tabs">
          <span class="mtab" :class="{ active: mainTab === 'graph' }" @click="mainTab = 'graph'">依赖图谱</span>
          <span class="mtab" :class="{ active: mainTab === 'services' }" @click="mainTab = 'services'">服务列表 (2)</span>
          <span class="mtab" :class="{ active: mainTab === 'changes' }" @click="mainTab = 'changes'">变更记录</span>
          <span class="mtab cost" :class="{ active: mainTab === 'cost' }" @click="mainTab = 'cost'">💰 成本</span>
        </div>
      </div>
    </div>

    <div v-if="mainTab === 'graph'" class="topo-content">
      <div class="topo-canvas">
        <svg class="topo-svg" viewBox="0 0 420 230">
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8"/></marker>
            <marker id="arrow-red" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#ef4444"/></marker>
          </defs>
          <g v-for="edge in currentEdges" :key="`${edge.from}-${edge.to}`">
            <line :x1="currentNodes.find(n => n.id === edge.from)?.x" :y1="(currentNodes.find(n => n.id === edge.from)?.y || 0) + 20" :x2="currentNodes.find(n => n.id === edge.to)?.x" :y2="(currentNodes.find(n => n.id === edge.to)?.y || 0)" :stroke="analysisMode && (edge.from === 'order' || edge.to === 'order') ? '#ef4444' : '#cbd5e1'" :stroke-width="analysisMode && (edge.from === 'order' || edge.to === 'order') ? 2.5 : 1.5" :marker-end="analysisMode && (edge.from === 'order' || edge.to === 'order') ? 'url(#arrow-red)' : 'url(#arrow)'"/>
          </g>
          <g v-for="node in currentNodes" :key="node.id" class="node-group" @click="selectNode(node.id)">
            <rect :x="node.x - 35" :y="node.y - 5" width="70" height="35" rx="6" :fill="analysisMode && (node.id === 'order' || node.id?.startsWith('order')) ? '#dc2626' : node.color" :class="{ selected: currentNode === node.id, 'analysis-target': analysisMode && (node.id === 'order' || node.id?.startsWith('order')), 'analysis-affected': analysisMode && (impactAnalysis.downstream.some(d => node.name?.includes(d) || node.id?.includes(d.toLowerCase())) || impactAnalysis.upstream.some(u => node.name?.includes(u) || node.id?.includes(u.toLowerCase()))) }"/>
            <text :x="node.x" :y="node.y + 16" text-anchor="middle" fill="#fff" font-size="9" font-weight="500">{{ node.name }}</text>
          </g>
        </svg>
        <div class="topo-legend">
          <div class="legend-item" v-for="(icon, type) in typeIcons" :key="type"><span class="legend-icon">{{ icon }}</span><span class="legend-label">{{ type }}</span></div>
        </div>
      </div>

      <div class="topo-panel">
        <!-- 添加依赖模式 -->
        <div v-if="addDependencyMode" class="panel-card add-dep-card">
          <h3>➕ 添加依赖</h3>
          <div class="dep-form">
            <div class="form-group">
              <label>依赖类型</label>
              <select class="form-select">
                <option>上游应用</option>
                <option>下游服务</option>
                <option>数据库</option>
                <option>缓存</option>
                <option>消息队列</option>
                <option>对象存储</option>
              </select>
            </div>
            <div class="form-group">
              <label>依赖名称</label>
              <input type="text" class="form-input" placeholder="输入服务名称" value="支付服务" />
            </div>
            <div class="form-group">
              <label>协议</label>
              <select class="form-select">
                <option>HTTP</option>
                <option>TCP</option>
                <option>gRPC</option>
                <option>MQTT</option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>端口</label>
                <input type="text" class="form-input" value="8083" />
              </div>
              <div class="form-group">
                <label>超时(ms)</label>
                <input type="text" class="form-input" value="30000" />
              </div>
            </div>
            <div class="form-group">
              <label>说明</label>
              <textarea class="form-textarea" rows="2" placeholder="依赖说明">订单服务调用支付服务完成支付流程</textarea>
            </div>
          </div>
          <button class="btn-submit">✅ 添加依赖</button>
          <p class="panel-hint">💡 添加后将自动更新拓扑图和依赖关系</p>
        </div>

        <!-- 影响分析模式 -->
        <div v-if="analysisMode" class="panel-card analysis-card">
          <h3>🚨 影响分析</h3>
          <div class="analysis-header"><span class="analysis-node">订单服务</span><span class="analysis-severity high">严重</span></div>
          <div class="analysis-stats">
            <div class="stat-row"><span class="stat-label">受影响用户</span><span class="stat-value warn">1,250</span></div>
            <div class="stat-row"><span class="stat-label">影响范围</span><span class="stat-value">4 个服务</span></div>
          </div>
          <div class="analysis-section"><span class="section-label">⬆️ 上游依赖</span><div class="affected-list"><div class="affected-item upstream">🔴 API Gateway</div></div></div>
          <div class="analysis-section"><span class="section-label">⬇️ 下游影响</span><div class="affected-list"><div class="affected-item downstream">🟡 MongoDB</div><div class="affected-item downstream">🟡 Redis</div><div class="affected-item downstream">🟡 S3 存储</div></div></div>
        </div>

        <div v-else-if="currentNode && nodeDetails[currentNode]" class="panel-card">
          <div class="panel-header"><h3>{{ nodeDetails[currentNode].name }}</h3><span class="node-status" :class="nodeDetails[currentNode].health">{{ nodeDetails[currentNode].health === 'healthy' ? '✅ 健康' : '⚠️ 警告' }}</span></div>
          <div class="panel-body">
            <div class="detail-section"><span class="section-label">基本信息</span><div class="detail-row"><span class="label">类型</span><span class="value">{{ typeIcons[nodeDetails[currentNode].type] }} {{ nodeDetails[currentNode].type }}</span></div><div class="detail-row"><span class="label">端口</span><span class="value mono">{{ nodeDetails[currentNode].port }}</span></div><div class="detail-row"><span class="label">实例数</span><span class="value">{{ nodeDetails[currentNode].instances }} 个</span></div></div>
            <div class="detail-section"><span class="section-label">资源使用</span><div class="detail-row"><span class="label">CPU</span><span class="value">{{ nodeDetails[currentNode].cpu }}%</span></div><div class="detail-row"><span class="label">内存</span><span class="value">{{ nodeDetails[currentNode].memory }}%</span></div></div>
            <div class="detail-section" v-if="nodeDetails[currentNode].upstream.length"><span class="section-label">⬆️ 上游调用</span><div class="dep-list"><div v-for="dep in nodeDetails[currentNode].upstream" :key="dep" class="dep-item">{{ dep }}</div></div></div>
            <div class="detail-section" v-if="nodeDetails[currentNode].downstream.length"><span class="section-label">⬇️ 下游依赖</span><div class="dep-list"><div v-for="dep in nodeDetails[currentNode].downstream" :key="dep" class="dep-item">{{ dep }}</div></div></div>
          </div>
        </div>

        <div v-else class="panel-card">
          <h3>📊 依赖统计</h3>
          <div class="stat-grid"><div class="stat-item"><span class="stat-value">8</span><span class="stat-label">节点</span></div><div class="stat-item"><span class="stat-value">10</span><span class="stat-label">依赖</span></div><div class="stat-item"><span class="stat-value">7</span><span class="stat-label">健康</span></div><div class="stat-item warning"><span class="stat-value">1</span><span class="stat-label">警告</span></div></div>
          <p class="panel-hint">💡 点击节点查看详情</p>
        </div>
      </div>
    </div>

    <!-- 服务列表 Tab -->
    <div v-else-if="mainTab === 'services'" class="plain-tab">
      <h3 class="plain-title">🧩 服务列表（服务部署单元）</h3>
      <div class="plain-table">
        <table>
          <thead><tr><th>服务名</th><th>部署方式</th><th>实例</th><th>规格</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="s in services" :key="s.name">
              <td class="res-name">{{ s.name }}</td>
              <td>{{ s.type }}</td>
              <td>{{ s.instances }} 实例</td>
              <td class="mono">{{ s.spec }}</td>
              <td><span class="st-ok">● 运行中</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 变更记录 Tab -->
    <div v-else-if="mainTab === 'changes'" class="plain-tab">
      <h3 class="plain-title">🕘 变更记录</h3>
      <div class="change-list">
        <div v-for="c in changes" :key="c.time + c.action" class="change-item">
          <div class="change-head"><span class="change-time">{{ c.time }}</span><span class="change-user">{{ c.user }}</span><span class="ch-ok">{{ c.result }}</span></div>
          <div class="change-body"><b>{{ c.action }}</b> · {{ c.target }}</div>
        </div>
      </div>
    </div>

    <!-- 💰 成本 Tab -->
    <div v-else class="plain-tab">
      <div class="cost-overview-bar">
        <div v-for="o in envCostOverview" :key="o.label" class="co-item">
          <div class="co-label">{{ o.label }}</div>
          <div class="co-value" :style="{ color: o.color }">{{ o.value }}</div>
        </div>
        <span class="btn-budget">📝 申请增加预算</span>
      </div>
      <div class="cost-hint">📍 该环境（Mock 账号 / cn-hangzhou）下各资源费用明细：</div>
      <div class="cost-filter">
        <span class="cf-label">筛选：</span>
        <select class="cf-select"><option>2026-08</option><option>2026-07</option></select>
        <select class="cf-select"><option>全部类型</option><option>云主机</option><option>数据库</option></select>
        <select class="cf-select"><option>全部区域</option><option>cn-hangzhou</option></select>
        <span class="cf-input">🔍 搜索资源名...</span>
        <span class="cf-reset">重置</span>
      </div>
      <div class="plain-table">
        <table>
          <thead><tr><th>资源名称</th><th>资源ID</th><th>类型</th><th>规格</th><th>费用日期</th><th class="right">费用</th><th>部门</th></tr></thead>
          <tbody>
            <tr v-for="r in envCostRows" :key="r.id">
              <td class="res-name">{{ r.name }}</td>
              <td class="mono">{{ r.id }}</td>
              <td><span class="type-tag">{{ r.type }}</span></td>
              <td>{{ r.spec || '-' }}</td>
              <td>{{ r.date }}</td>
              <td class="right cost">¥{{ r.cost.toFixed(2) }}</td>
              <td>{{ r.dept }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="cost-page">共 70 条 <span class="pg">1</span> <span class="pg">2</span> <span class="pg">3</span> <span class="pg">4</span></div>
    </div>
  </div>
</template>

<style scoped>
.topo-sim { padding: 16px; background: #f1f5f9; height: 100%; display: flex; flex-direction: column; }
.topo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; background: #fff; padding: 12px 16px; border-radius: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
h2 { font-size: 16px; font-weight: 700; color: #0f172a; margin: 0; }
.app-tag { padding: 4px 10px; background: #f1f5f9; border-radius: 6px; font-size: 12px; color: #475569; }
.view-tabs { display: flex; gap: 2px; background: #f1f5f9; padding: 3px; border-radius: 8px; }
.tab { padding: 6px 14px; font-size: 12px; color: #64748b; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.tab.active { background: #fff; color: #0f172a; font-weight: 500; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.topo-content { flex: 1; display: flex; gap: 12px; min-height: 0; }
.topo-canvas { flex: 1; background: #fff; border-radius: 10px; padding: 16px; display: flex; flex-direction: column; }
.topo-svg { flex: 1; width: 100%; }
.node-group { cursor: pointer; }
.node-group rect { transition: all 0.2s; }
.node-group:hover rect { filter: brightness(1.1); }
.node-group rect.selected { stroke: #0f172a; stroke-width: 2; }
.node-group rect.analysis-target { stroke: #dc2626; stroke-width: 3; filter: drop-shadow(0 0 8px rgba(220,38,38,0.5)); }
.node-group rect.analysis-affected { stroke: #f59e0b; stroke-width: 2; opacity: 0.8; }
.topo-legend { display: flex; justify-content: center; gap: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #64748b; }
.legend-icon { font-size: 12px; }
.topo-panel { width: 240px; display: flex; flex-direction: column; gap: 10px; }
.panel-card { background: #fff; border-radius: 10px; padding: 14px; }
.panel-card.add-dep-card { border: 2px solid #dbeafe; background: #eff6ff; }
.panel-card.analysis-card { border: 2px solid #fecaca; background: #fef2f2; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.panel-header h3 { font-size: 14px; font-weight: 600; color: #0f172a; margin: 0; }
.node-status { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.node-status.healthy { background: #dcfce7; color: #16a34a; }
.node-status.warning { background: #fef3c7; color: #d97706; }
h3 { font-size: 13px; font-weight: 600; color: #0f172a; margin: 0 0 10px 0; }
.panel-body { display: flex; flex-direction: column; gap: 12px; }
.detail-section { padding-bottom: 10px; border-bottom: 1px solid #f1f5f9; }
.detail-section:last-child { border-bottom: none; padding-bottom: 0; }
.section-label { display: block; font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 6px; }
.detail-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 11px; }
.label { color: #64748b; }
.value { color: #0f172a; font-weight: 500; }
.mono { font-family: monospace; font-size: 10px; }
.dep-list { display: flex; flex-direction: column; gap: 4px; }
.dep-item { padding: 4px 8px; background: #f8fafc; border-radius: 4px; font-size: 11px; color: #475569; }
.analysis-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.analysis-node { font-size: 14px; font-weight: 600; color: #dc2626; }
.analysis-severity { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.analysis-severity.high { background: #fecaca; color: #dc2626; }
.analysis-stats { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #fecaca; }
.stat-row { display: flex; justify-content: space-between; font-size: 12px; }
.stat-label { color: #64748b; }
.stat-value { font-weight: 600; color: #0f172a; }
.stat-value.warn { color: #dc2626; }
.analysis-section { margin-bottom: 10px; }
.affected-list { display: flex; flex-direction: column; gap: 4px; }
.affected-item { padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.affected-item.upstream { background: #fee2e2; color: #dc2626; }
.affected-item.downstream { background: #fef3c7; color: #d97706; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.stat-item { text-align: center; padding: 10px; background: #f8fafc; border-radius: 6px; }
.stat-value { display: block; font-size: 18px; font-weight: 700; color: #0f172a; }
.stat-label { display: block; font-size: 10px; color: #64748b; margin-top: 2px; }
.stat-item.warning .stat-value { color: #d97706; }
.panel-hint { font-size: 11px; color: #94a3b8; text-align: center; margin: 8px 0 0; }

/* 添加依赖表单 */
.dep-form { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 11px; font-weight: 600; color: #475569; }
.form-select, .form-input, .form-textarea { padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; background: #fff; color: #0f172a; }
.form-select:focus, .form-input:focus, .form-textarea:focus { outline: none; border-color: #2563eb; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-textarea { resize: none; font-family: inherit; }
.btn-submit { width: 100%; padding: 10px; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-submit:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }

/* 主 Tab（依赖图谱 / 服务列表 / 变更记录 / 💰 成本） */
.main-tabs { display: flex; gap: 4px; background: #f1f5f9; padding: 3px; border-radius: 8px; }
.mtab { padding: 6px 14px; font-size: 12px; color: #64748b; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.mtab.active { background: #fff; color: #0f172a; font-weight: 500; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.mtab.cost.active { background: #faf5ff; color: #7c3aed; }

/* 服务列表 / 变更记录 / 成本 Tab 通用 */
.plain-tab { flex: 1; background: #fff; border-radius: 10px; padding: 16px; overflow-y: auto; }
.plain-title { font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 12px; }
.plain-table { overflow-x: auto; }
.plain-table table { width: 100%; border-collapse: collapse; font-size: 12px; }
.plain-table th { text-align: left; padding: 8px 10px; color: #64748b; font-weight: 500; background: #f8fafc; border-bottom: 1px solid #eef0f4; }
.plain-table td { padding: 8px 10px; border-bottom: 1px solid #f6f7fb; color: #334155; }
.right { text-align: right; }
.res-name { color: #0f172a; font-weight: 500; }
.st-ok { color: #16a34a; }
.type-tag { padding: 2px 8px; background: #f1f5f9; border-radius: 4px; font-size: 11px; }
.cost { color: #059669; font-weight: 600; }

/* 变更记录 */
.change-list { display: flex; flex-direction: column; gap: 10px; }
.change-item { padding: 10px 12px; background: #f8fafc; border: 1px solid #eef0f4; border-radius: 8px; }
.change-head { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; font-size: 11px; }
.change-time { color: #64748b; }
.change-user { color: #94a3b8; }
.ch-ok { margin-left: auto; padding: 1px 8px; background: #ecfdf5; color: #059669; border-radius: 4px; font-size: 11px; }
.change-body { font-size: 12px; color: #334155; }

/* 成本 Tab */
.cost-overview-bar { display: flex; align-items: center; gap: 26px; padding: 12px 16px; background: linear-gradient(90deg, #faf5ff, #f6f7fb); border: 1px solid #f0ecff; border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.co-label { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
.co-value { font-size: 17px; font-weight: 700; }
.btn-budget { margin-left: auto; padding: 7px 14px; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: #fff; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3); }
.cost-hint { font-size: 12px; color: #64748b; margin-bottom: 10px; }
.cost-filter { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #eef0f4; border-radius: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.cf-label { font-size: 12px; color: #64748b; }
.cf-select { padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; background: #fff; color: #0f172a; }
.cf-input { flex: 1; min-width: 150px; padding: 5px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; color: #94a3b8; background: #fff; }
.cf-reset { font-size: 12px; color: #7c3aed; cursor: pointer; font-weight: 500; }
.cost-page { display: flex; align-items: center; justify-content: flex-end; gap: 6px; padding-top: 12px; font-size: 12px; color: #64748b; }
.pg { width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 11px; }
</style>
