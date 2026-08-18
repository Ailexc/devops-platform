<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { GraphNode, GraphEdge } from '@/types'

const props = withDefaults(defineProps<{
  nodes: GraphNode[]
  edges: GraphEdge[]
  height?: string
  roam?: boolean
}>(), {
  height: '480px',
  roam: false,
})

const emit = defineEmits<{
  (e: 'node-click', node: GraphNode): void
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const CATEGORY_COLORS: Record<string, string> = {
  application: '#7C3AED',
  environment: '#EC4899',
  service: '#3B82F6',
  resource: '#10B981',
  endpoint: '#F59E0B',
}

function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const categories = Object.keys(CATEGORY_COLORS).map((name) => ({ name }))
  chart.setOption({
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const meta = params.data.meta || {}
          const lines = Object.entries(meta)
            .slice(0, 8)
            .map(([k, v]) => `${k}: ${v}`)
          return `<strong>${params.name}</strong><br/>${lines.join('<br/>') || '暂无元数据'}`
        }
        return `${params.data.source} → ${params.data.target}<br/>${params.data.relation_type || ''}`
      },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: props.roam,
      draggable: false,
      animationDurationUpdate: 300,
      animationEasingUpdate: 'cubicOut',
      data: props.nodes.map((n) => ({
        id: n.id,
        name: n.name,
        category: n.category,
        meta: n.meta || {},
        symbolSize: n.category === 'application' ? 46 : n.category === 'service' ? 36 : 26,
        itemStyle: { color: CATEGORY_COLORS[n.category] || '#94A3B8' },
        label: { show: true, position: 'bottom', fontSize: 11, color: '#374151' },
      })),
      links: props.edges.map((e) => ({
        source: e.source,
        target: e.target,
        relation_type: e.relation_type,
        lineStyle: {
          type: e.strength === 'soft' ? 'dashed' : 'solid',
          width: e.strength === 'hard' ? 2 : 1,
          color: e.strength === 'soft' ? '#94A3B8' : '#8B5CF6',
          curveness: 0.08,
        },
        label: {
          show: props.edges.length <= 40,
          formatter: () => e.relation_type,
          fontSize: 10,
          color: '#9CA3AF',
        },
      })),
      categories,
      force: { repulsion: 220, edgeLength: [80, 160], gravity: 0.08 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
      animation: true,
    }],
  })
}

function handleResize() {
  chart?.resize()
}

onMounted(async () => {
  await nextTick()
  render()
  chart?.on('click', (params: any) => {
    if (params.dataType === 'node') {
      emit('node-click', params.data as GraphNode)
    }
  })
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

watch(() => [props.nodes, props.edges], () => render(), { deep: true })
</script>

<template>
  <div ref="chartRef" :style="{ width: '100%', height: props.height }"></div>
</template>
