// 演示系统类型定义

/** 演示步骤中的高亮区域 */
export interface HighlightArea {
  /** CSS 选择器，用于定位高亮元素 */
  selector: string
  /** 高亮区域标题 */
  label: string
  /** 高亮框内边距（px），默认 8 */
  padding?: number
  /** 高亮框圆角（px），默认 8 */
  borderRadius?: number
}

/** 页面模拟中的操作项 */
export interface PageAction {
  /** 操作图标（emoji） */
  icon: string
  /** 操作名称 */
  label: string
  /** 操作结果（可选） */
  result?: string
}

/** 演示步骤 */
export interface PresentationStep {
  /** 步骤 ID */
  id: string
  /** 路由路径 */
  route: string
  /** 步骤标题 */
  title: string
  /** 步骤说明（详细描述） */
  description: string
  /** 亮点文字（1-2 句核心卖点） */
  highlight: string
  /** 页面模拟组件名 */
  pageComponent: string
  /** 页面模拟组件的 Props */
  pageProps?: Record<string, any>
  /** 当前步骤的操作说明 */
  narration?: string
  /** 高亮区域配置 */
  highlightArea?: HighlightArea
  /** 浮层位置：相对于高亮区域 */
  tooltipPosition?: 'top' | 'bottom' | 'left' | 'right'
  /** 路由 query 参数 */
  query?: Record<string, string>
}

/** 演示场景 */
export interface PresentationScene {
  /** 场景 ID */
  id: string
  /** 场景标题 */
  title: string
  /** 场景副标题 */
  subtitle: string
  /** 场景描述（简短） */
  description: string
  /** 预计时长（分钟） */
  duration: number
  /** 场景图标（SVG path） */
  icon: string
  /** 场景主题色 */
  color: string
  /** 场景角色（如"系统管理员"） */
  role?: string
  /** 场景步骤 */
  steps: PresentationStep[]
}

/** 场景元数据（目录页使用，不含步骤） */
export interface SceneMeta {
  id: string
  title: string
  subtitle: string
  description: string
  duration: number
  icon: string
  color: string
  stepCount: number
}
