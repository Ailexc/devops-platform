<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import type { TopoBox, TopoEdge, ZoneConfig } from './types'

const props = defineProps<{
  boxes: TopoBox[]
  edges: TopoEdge[]
  zones?: ZoneConfig[]
  height?: string
}>()

const emit = defineEmits<{
  (e: 'node-click', box: TopoBox): void
  (e: 'edge-click', edge: TopoEdge): void
}>()

// 缩放控制
const scale = ref(1)
const minScale = 0.5
const maxScale = 2

function zoomIn() { scale.value = Math.min(scale.value + 0.1, maxScale) }
function zoomOut() { scale.value = Math.max(scale.value - 0.1, minScale) }
function resetZoom() { scale.value = 1 }

// 容器尺寸（用于百分比→像素转换）
const containerRef = ref<HTMLDivElement>()
const containerW = ref(800)
const containerH = ref(580)
let ro: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    containerW.value = rect.width || 800
    containerH.value = rect.height || 580
    ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        containerW.value = entry.contentRect.width || 800
        containerH.value = entry.contentRect.height || 580
      }
    })
    ro.observe(containerRef.value)
  }
})

onBeforeUnmount(() => { ro?.disconnect() })

// 百分比→像素
function toPx(val: number, base: number): number {
  return val < 1 ? val * base : val
}

// 区域样式
const ZONE_STYLES: Record<string, { color: string }> = {
  access: { color: '#06B6D4' }, service: { color: '#3B82F6' }, middleware: { color: '#8B5CF6' },
  data: { color: '#F97316' }, infra: { color: '#10B981' }, monitor: { color: '#64748B' },
}

const NODE_STYLES: Record<string, { border: string; iconBg: string; iconColor: string }> = {
  access: { border: '#06B6D4', iconBg: '#ECFEFF', iconColor: '#06B6D4' },
  service: { border: '#3B82F6', iconBg: '#EFF6FF', iconColor: '#3B82F6' },
  middleware: { border: '#8B5CF6', iconBg: '#F5F3FF', iconColor: '#8B5CF6' },
  data: { border: '#F97316', iconBg: '#FFF7ED', iconColor: '#F97316' },
  infra: { border: '#10B981', iconBg: '#ECFDF5', iconColor: '#10B981' },
  monitor: { border: '#64748B', iconBg: '#F8FAFC', iconColor: '#64748B' },
}

// 过滤可见节点
const visibleBoxes = computed(() => props.boxes.filter(b => !b.hidden))

// 判断节点是否在当前筛选的区域内
const activeZoneKeys = computed(() => {
  if (!props.zones || props.zones.length === 0) return null
  return new Set(props.zones.map(z => z.key))
})

function isNodeActive(box: TopoBox): boolean {
  if (!activeZoneKeys.value) return true
  return activeZoneKeys.value.has(box.zone)
}

function isEdgeVisible(edge: TopoEdge): boolean {
  const src = visibleBoxes.value.find(b => b.id === edge.source)
  const tgt = visibleBoxes.value.find(b => b.id === edge.target)
  if (!src || !tgt) return false
  if (!activeZoneKeys.value) return true
  return activeZoneKeys.value.has(src.zone) && activeZoneKeys.value.has(tgt.zone)
}

// 计算连线坐标 - 从节点底部中心到目标顶部中心（百分比→像素）
function getEdgeCoords(edge: TopoEdge) {
  const sourceBox = visibleBoxes.value.find(b => b.id === edge.source)
  const targetBox = visibleBoxes.value.find(b => b.id === edge.target)
  if (!sourceBox || !targetBox) return null
  
  const sx = toPx(sourceBox.x, containerW.value) + toPx(sourceBox.w, containerW.value) / 2
  const sy = toPx(sourceBox.y, containerH.value) + toPx(sourceBox.h, containerH.value)
  const tx = toPx(targetBox.x, containerW.value) + toPx(targetBox.w, containerW.value) / 2
  const ty = toPx(targetBox.y, containerH.value)
  
  return { sx, sy, tx, ty }
}

function getEdgeColor(edge: TopoEdge): string {
  if (edge.removed) return '#EF4444'
  if (edge.pending) return '#3B82F6'
  if (edge.strength === 'soft') return '#94A3B8'
  return '#8B5CF6'
}

function getEdgeDash(edge: TopoEdge): string {
  if (edge.removed || edge.pending || edge.strength === 'soft') return '6,4'
  return 'none'
}

defineExpose({ scale, zoomIn, zoomOut, resetZoom })
</script>

<template>
  <div class="topo-canvas" :style="{ height: height || '500px' }">
    <!-- 缩放容器 -->
    <div ref="containerRef" class="zoom-container" :style="{ transform: `scale(${scale})`, transformOrigin: 'top left' }">
      <!-- SVG 连线层（放在最底层） -->
      <svg class="edge-layer" :style="{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }">
        <template v-for="edge in edges" :key="`${edge.source}-${edge.target}`">
          <!-- 透明热区（用于点击） -->
          <line
            v-if="getEdgeCoords(edge) && isEdgeVisible(edge)"
            :x1="getEdgeCoords(edge)!.sx" :y1="getEdgeCoords(edge)!.sy"
            :x2="getEdgeCoords(edge)!.tx" :y2="getEdgeCoords(edge)!.ty"
            stroke="transparent"
            :stroke-width="20"
            stroke-linecap="round"
            style="pointer-events: stroke; cursor: pointer;"
            @click.stop="emit('edge-click', edge)"
          />
          <!-- 可见连线 -->
          <line
            v-if="getEdgeCoords(edge) && isEdgeVisible(edge)"
            :x1="getEdgeCoords(edge)!.sx" :y1="getEdgeCoords(edge)!.sy"
            :x2="getEdgeCoords(edge)!.tx" :y2="getEdgeCoords(edge)!.ty"
            :stroke="getEdgeColor(edge)"
            :stroke-width="edge.strength === 'hard' ? 2.5 : 1.5"
            :stroke-dasharray="getEdgeDash(edge)"
            stroke-linecap="round"
            style="pointer-events: none;"
          />
          <!-- 连线上的箭头 -->
          <polygon
            v-if="getEdgeCoords(edge) && isEdgeVisible(edge)"
            :points="`${getEdgeCoords(edge)!.tx},${getEdgeCoords(edge)!.ty} ${getEdgeCoords(edge)!.tx - 6},${getEdgeCoords(edge)!.ty - 8} ${getEdgeCoords(edge)!.tx + 6},${getEdgeCoords(edge)!.ty - 8}`"
            :fill="getEdgeColor(edge)"
            style="pointer-events: none;"
          />
        </template>
      </svg>

      <!-- 区域 -->
      <div 
        v-for="zone in zones" 
        :key="zone.key"
        class="zone"
        :style="{
          left: (zone.x < 1 ? zone.x * 100 + '%' : zone.x + 'px'),
          top: (zone.y < 1 ? zone.y * 100 + '%' : zone.y + 'px'),
          width: (zone.w < 1 ? zone.w * 100 + '%' : zone.w + 'px'),
          height: (zone.h < 1 ? zone.h * 100 + '%' : zone.h + 'px'),
          borderColor: ZONE_STYLES[zone.key]?.color || '#E2E8F0',
        }"
      >
        <span class="zone-label" :style="{ color: ZONE_STYLES[zone.key]?.color }">{{ zone.icon }} {{ zone.label }}</span>
      </div>

      <!-- 节点 -->
      <div 
        v-for="box in visibleBoxes" 
        :key="box.id"
        class="node"
        :class="{ inactive: !isNodeActive(box) }"
        :style="{
          left: (box.x < 1 ? box.x * 100 + '%' : box.x + 'px'),
          top: (box.y < 1 ? box.y * 100 + '%' : box.y + 'px'),
          width: (box.w < 1 ? box.w * 100 + '%' : box.w + 'px'),
          borderColor: NODE_STYLES[box.zone]?.border || '#E2E8F0',
          boxShadow: box.meta?.pending ? '0 0 0 2px #3B82F6' : undefined,
        }"
        @click.stop="emit('node-click', box)"
      >
        <div class="node-icon" :style="{ background: NODE_STYLES[box.zone]?.iconBg, color: NODE_STYLES[box.zone]?.iconColor }">{{ box.icon }}</div>
        <div class="node-name">{{ box.name }}</div>
        <div class="node-info" v-if="box.meta?.port">{{ box.meta.port }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.topo-canvas {
  position: relative;
  background: #F8FAFC;
  border-radius: 8px;
  overflow: hidden;
}

.zoom-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.zone {
  position: absolute;
  border: 2px dashed;
  border-radius: 12px;
  pointer-events: none;
  transition: opacity 0.3s;
}

.zone-label {
  position: absolute;
  top: 6px;
  left: 16px;
  background: #F8FAFC;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 500;
}

.node {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px;
  background: white;
  border: 2px solid;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  z-index: 2;
}

.node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.node.inactive {
  opacity: 0.3;
}

.node-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.node-name {
  font-size: 12px;
  font-weight: 600;
  color: #1E293B;
  text-align: center;
}

.node-info {
  font-size: 10px;
  color: #64748B;
}
</style>
