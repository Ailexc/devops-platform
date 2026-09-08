import type { Scene } from '@/types/presentation'

/** 场景 2：流程办理板块 */
export const sceneProcess: Scene = {
  id: 'process',
  title: '流程办理',
  description: '发起申请、审批处理、流程追踪',
  themeColor: '#e6a23c',
  role: 'xiaoming',
  roleLabel: '研发工程师',
  duration: '~3 分钟',
  steps: [
    {
      component: 'ApplySim',
      title: '选择流程',
      focus: 'step1',
      narration: '发起申请第一步：选择流程。系统根据角色和权限过滤可发起的流程。',
      highlight: '权限控制，按角色过滤',
    },
    {
      component: 'ApplySim',
      title: '填写表单',
      focus: 'step2',
      narration: '第二步：填写表单。表单由流程定义动态生成，支持多种字段类型。',
      highlight: '动态表单，按需生成',
    },
    {
      component: 'MyApplicationsSim',
      title: '我的申请',
      focus: 'stats',
      narration: '我的申请页面，实时追踪所有发起的流程状态：运行中、已挂起、已完成、已终止。',
      highlight: '状态实时追踪',
    },
    {
      component: 'TodoListSim',
      title: '待办审批',
      focus: 'table',
      narration: '审批人收到待办通知，在待办审批列表中查看待处理任务。',
      highlight: '待办自动推送',
    },
    {
      component: 'TaskDetailSim',
      title: '审批处理',
      focus: 'approval',
      narration: '任务办理页：查看申请详情、填写审批意见、支持通过/拒绝/转办操作。',
      highlight: '意见必填，操作便捷',
    },
    {
      component: 'TaskDetailSim',
      title: '流程追踪',
      focus: 'timeline',
      narration: '右侧流程追踪时间线，清晰展示当前进度和历史节点。',
      highlight: '流程可视化追踪',
    },
  ],
}
