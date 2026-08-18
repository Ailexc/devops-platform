<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import { graphApi } from '@/api'
import type { GraphData } from '@/types'

const loading = ref(false)
const graph = ref<GraphData>({ nodes: [], edges: [] })
const envLabel = ref('')
const layeredEl = ref<HTMLElement>()
const forceEl = ref<HTMLElement>()
const circularEl = ref<HTMLElement>()
const treeEl = ref<HTMLElement>()

const CATEGORY_COLORS: Record<string, string> = {
  application: '#7C3AED',
  environment: '#EC4899',
  service: '#3B82F6',
  resource: '#10B981',
  endpoint: '#F59E0B',
}
const CATEGORY_ORDER = ['application', 'environment', 'service', 'resource', 'endpoint']

function linkOf(e: any) {
  return {
    source: e.source,
    target: e.target,
    lineStyle: {
      type: e.strength === 'soft' ? 'dashed' : 'solid',
      width: e.strength === 'hard' ? 2 : 1,
      color: e.strength === 'soft' ? '#94A3B8' : '#8B5CF6',
      curveness: 0.06,
    },
  }
}

function nodeOf(n: any) {
  return {
    id: n.id,
    name: n.name,
    category: n.category,
    meta: n.meta || {},
    symbolSize: n.category === 'application' ? 44 : n.category === 'environment' ? 38 : n.category === 'service' ? 30 : 24,
    itemStyle: { color: CATEGORY_COLORS[n.category] || '#94A3B8' },
    label: { show: true, position: 'bottom', fontSize: 10, color: '#374151' },
  }
}

function renderLayered() {
  const el = layeredEl.value
  if (!el) return
  const chart = echarts.init(el)
  const nodes = graph.value.nodes.map((n) => {
    const idx = CATEGORY_ORDER.indexOf(n.category)
    const col = idx === -1 ? CATEGORY_ORDER.length : idx
    const same = graph.value.nodes.filter((x) => x.category === n.category).map((x) => x.id)
    const pos = same.indexOf(n.id)
    const total = Math.max(1, same.length)
    return {
      ...nodeOf(n),
      x: 80 + col * 230,
      y: 60 + (total === 1 ? 0 : (pos / (total - 1) - 0.5)) * 260,
    }
  })
  chart.setOption({
    tooltip: { formatter: (p: any) => (p.dataType === 'node' ? `<strong>${p.name}</strong><br/>${p.category}` : `${p.data.source} → ${p.data.target}`) },
    series: [{
      type: 'graph',
      layout: 'none',
      roam: false,
      data: nodes,
      links: graph.value.edges.map(linkOf),
      label: { show: false },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: 6,
    }],
  })
}

function renderForce() {
  const el = forceEl.value
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { formatter: (p: any) => (p.dataType === 'node' ? `<strong>${p.name}</strong><br/>${p.category}` : `${p.data.source} → ${p.data.target}`) },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: false,
      data: graph.value.nodes.map(nodeOf),
      links: graph.value.edges.map(linkOf),
      force: { repulsion: 220, edgeLength: [80, 160], gravity: 0.1 },
      label: { show: false },
    }],
  })
}

function renderCircular() {
  const el = circularEl.value
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { formatter: (p: any) => (p.dataType === 'node' ? `<strong>${p.name}</strong><br/>${p.category}` : `${p.data.source} → ${p.data.target}`) },
    series: [{
      type: 'graph',
      layout: 'circular',
      circular: { rotateLabel: true },
      roam: false,
      data: graph.value.nodes.map(nodeOf),
      links: graph.value.edges.map(linkOf),
      label: { show: false },
    }],
  })
}

function buildTreeRoot() {
  const byId = new Map(graph.value.nodes.map((n) => [n.id, n]))
  const edges = graph.value.edges
  const appNode = graph.value.nodes.find((n) => n.category === 'application')
  if (!appNode) return null
  const root: any = { name: appNode.name, itemStyle: { color: CATEGORY_COLORS.application }, children: [] }
  const childrenMap = new Map<string, any[]>()
  for (const e of edges) {
    if (!childrenMap.has(e.source)) childrenMap.set(e.source, [])
    childrenMap.get(e.source)!.push(e.target)
  }
  const seen = new Set<string>()
  const build = (id: string): any => {
    seen.add(id)
    const node = byId.get(id)
    if (!node) return null
    const childIds = (childrenMap.get(id) || []).filter((c) => !seen.has(c))
    return {
      name: node.name,
      itemStyle: { color: CATEGORY_COLORS[node.category] || '#94A3B8' },
      children: childIds.map(build).filter(Boolean),
    }
  }
  root.children = (childrenMap.get(appNode.id) || []).map(build).filter(Boolean)
  return root
}

function renderTree() {
  const el = treeEl.value
  if (!el) return
  const chart = echarts.init(el)
  const root = buildTreeRoot()
  if (!root) return
  chart.setOption({
    tooltip: { formatter: (p: any) => `<strong>${p.name}</strong>` },
    series: [{
      type: 'tree',
      data: [root],
      layout: 'orthogonal',
      orient: 'LR',
      roam: false,
      symbolSize: 9,
      initialTreeDepth: -1,
      lineStyle: { color: '#C4B5FD', width: 1.2 },
      label: { position: 'right', fontSize: 10 },
      leaves: { label: { position: 'right' } },
    }],
  })
}

onMounted(async () => {
  loading.value = true
  try {
    const apps = await graphApi.applications()
    const first = apps.data[0]
    if (!first) throw new Error('无应用')
    const envs = await graphApi.applicationEnvs(first.id)
    const env = envs.data.find((e) => e.env_type === 'prod') || envs.data[0]
    if (!env) throw new Error('无环境')
    const g = await graphApi.environment(env.id)
    graph.value = g.data
    envLabel.value = `${first.name} / ${env.name}`
    await nextTick()
    renderLayered()
    renderForce()
    renderCircular()
    renderTree()
  } catch {
    message.error('加载图谱数据失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <a-page-header
      title="🧭 图谱样式预览"
      :sub-title="`示例数据：${envLabel || '加载中...'}（仅用于选择风格）`"
    />

    <div style="margin-bottom: 12px">
      <span style="margin-right: 12px">图例：</span>
      <a-tag color="purple">应用</a-tag>
      <a-tag color="magenta">环境</a-tag>
      <a-tag color="blue">服务</a-tag>
      <a-tag color="green">资源</a-tag>
      <a-tag color="orange">端点</a-tag>
      <span style="color: #999; font-size: 12px; margin-left: 8px">实线=强制依赖 / 虚线=软依赖</span>
    </div>

    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="① 分层分组（推荐）" size="small">
          <template #extra><a-tag color="green">推荐</a-tag></template>
          <div ref="layeredEl" style="height: 420px"></div>
          <p style="color: #666; font-size: 12px">
            按 应用→环境→服务→资源→端点 固定泳道排列，位置规范不重叠，一眼看懂层级与依赖方向
          </p>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="② 力导向（现状）" size="small">
          <div ref="forceEl" style="height: 420px"></div>
          <p style="color: #666; font-size: 12px">节点按引力自动散布，灵活但杂乱、位置不可控</p>
        </a-card>
      </a-col>
      <a-col :span="12" style="margin-top: 16px">
        <a-card title="③ 环形/径向" size="small">
          <div ref="circularEl" style="height: 420px"></div>
          <p style="color: #666; font-size: 12px">围绕中心节点向外辐射，适合看单点周边关系</p>
        </a-card>
      </a-col>
      <a-col :span="12" style="margin-top: 16px">
        <a-card title="④ 树形/层级树" size="small">
          <div ref="treeEl" style="height: 420px"></div>
          <p style="color: #666; font-size: 12px">严格的父子归属树（环境内服务与资源归属），依赖边在此风格中不展示</p>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>
