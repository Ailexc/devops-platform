// ========== 区域类型定义 ==========

export type ZoneType =
  | 'access'       // 接入区
  | 'service'      // 服务区
  | 'middleware'   // 中间件区
  | 'data'         // 数据区
  | 'infra'        // 基础设施区
  | 'monitor'      // 监控区

export interface ZoneConfig {
  key: ZoneType
  label: string
  color: string
  icon: string
  x: number
  y: number
  w: number
  h: number
}

// 默认区域配置 — 使用百分比铺满画布
export const DEFAULT_ZONES: ZoneConfig[] = [
  { key: 'access', label: '接入区', color: '#06B6D4', icon: '🌐', x: 0, y: 0, w: 0.2, h: 0.72 },
  { key: 'service', label: '服务区', color: '#3B82F6', icon: '⚙️', x: 0.21, y: 0, w: 0.4, h: 0.72 },
  { key: 'middleware', label: '中间件区', color: '#8B5CF6', icon: '🧱', x: 0.62, y: 0, w: 0.36, h: 0.35 },
  { key: 'data', label: '数据区', color: '#F97316', icon: '🗄️', x: 0.62, y: 0.36, w: 0.36, h: 0.36 },
  { key: 'infra', label: '基础设施区', color: '#10B981', icon: '☸️', x: 0.21, y: 0.73, w: 0.4, h: 0.25 },
  { key: 'monitor', label: '监控区', color: '#64748B', icon: '📊', x: 0.62, y: 0.73, w: 0.36, h: 0.25 },
]

// ========== 节点类型定义 ==========

export interface TopoBox {
  id: string
  name: string
  icon: string
  zone: ZoneType
  meta: Record<string, any>
  x: number
  y: number
  w: number
  h: number
  primaryResId?: number
  hidden?: boolean
}

// ========== 边类型定义 ==========

export interface TopoEdge {
  source: string
  target: string
  label: string
  strength: string
  relation_type: string
  pending?: boolean
  removed?: boolean
  pendingInfo?: { ticketNo: string; ticketId?: number; status: string }
}

// ========== 旧版兼容（可移除） ==========

export interface ZoneRect {
  key: string
  x: number
  y: number
  w: number
  h: number
  label: string
}
