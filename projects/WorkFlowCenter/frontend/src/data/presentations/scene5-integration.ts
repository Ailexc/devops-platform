import type { Scene } from '@/types/presentation'

/** 场景 5：外部集成板块 */
export const sceneIntegration: Scene = {
  id: 'integration',
  title: '外部集成',
  description: '程序管理、Webhook 订阅、事件驱动',
  themeColor: '#1abc9c',
  role: 'admin',
  roleLabel: '系统管理员',
  duration: '~2 分钟',
  steps: [
    {
      component: 'ApiDemoSim',
      title: 'API 发起',
      focus: 'curl',
      narration: '程序发起：外部系统通过 API + API Key 认证发起流程，支持 CMDB、IT 服务台等。',
      highlight: 'RESTful API 接入',
    },
    {
      component: 'ApiDemoSim',
      title: 'API 响应',
      focus: 'response',
      narration: 'API 响应：返回流程实例信息，支持异步执行和回调通知。',
      highlight: '异步执行，实时反馈',
    },
    {
      component: 'WebhookSim',
      title: 'Webhook 订阅',
      focus: 'alert',
      narration: 'Webhook 订阅：配置外部系统回调，接收流程事件通知，支持 HMAC 签名验证。',
      highlight: '事件驱动，实时推送',
    },
    {
      component: 'EventLogSim',
      title: '事件日志',
      focus: 'table',
      narration: '事件日志：全链路事件记录，支持按类型筛选，用于审计与排查。',
      highlight: '全链路审计追踪',
    },
  ],
}
