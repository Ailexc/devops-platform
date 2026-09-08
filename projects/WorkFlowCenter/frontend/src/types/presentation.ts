/** 演示步骤 */
export interface Step {
  /** 对应的模拟组件名 */
  component: string
  /** 步骤标题（可选，覆盖默认） */
  title?: string
  /** 高亮焦点 */
  focus?: string
  /** 旁白解说词 */
  narration: string
  /** 核心卖点 */
  highlight?: string
  /** 过渡动画 */
  animation?: 'slide-left' | 'slide-right' | 'fade' | 'pop-in'
}

/** 演示场景 */
export interface Scene {
  id: string
  title: string
  description: string
  /** 场景主题色 */
  themeColor: string
  /** 演示角色 */
  role: string
  /** 角色标签 */
  roleLabel: string
  /** 预计时长 */
  duration: string
  /** 步骤列表 */
  steps: Step[]
}
