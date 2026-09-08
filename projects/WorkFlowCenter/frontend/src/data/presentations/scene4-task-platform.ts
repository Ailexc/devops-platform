import type { Scene } from '@/types/presentation'

/** 场景 4：任务平台板块 */
export const sceneTaskPlatform: Scene = {
  id: 'task-platform',
  title: '任务平台',
  description: '能力注册、执行机制、任务追踪与真实架构',
  themeColor: '#9b59b6',
  role: 'admin',
  roleLabel: '系统管理员',
  duration: '~3 分钟',
  steps: [
    {
      component: 'CapabilitySim',
      title: '能力注册',
      narration:
        '能力注册中心是自动化执行的基础。每个能力代表一个可被调用的原子操作（如创建主机、添加 DNS 记录、发送邮件等），' +
        '注册时需要定义唯一编码、名称、描述、输入参数 Schema 和输出结果 Schema。' +
        '所有能力统一管理，支持按编码搜索和状态筛选，方便管理员快速查找和维护。',
      highlight: '能力统一注册 · Schema 定义 · 编码管理',
    },
    {
      component: 'CapabilitySim',
      title: '执行模式',
      narration:
        '能力支持两种执行模式：Mock 模式用于开发测试阶段，模拟真实执行返回预设结果，无需对接外部系统；' +
        'HTTP 模式用于生产环境，通过 RESTful API 调用外部系统执行真实操作。' +
        '两种模式可随时切换，开发阶段用 Mock 快速验证流程，上线后切换到 HTTP 对接真实业务系统。',
      highlight: 'Mock 快速验证 · HTTP 生产对接 · 灵活切换',
    },
    {
      component: 'TaskJobSim',
      title: '任务中心',
      narration:
        '任务中心是所有能力执行记录的统一视图。顶部统计卡片展示执行总数、成功数、执行中、失败数等关键指标；' +
        '下方列表展示每条任务的 Job ID、关联能力、流程单号、执行状态、耗时和创建时间。' +
        '支持按状态筛选和关键词搜索，管理员可以快速定位异常任务并进行排查。',
      highlight: '全链路任务追踪 · 状态统计 · 异常排查',
    },
    {
      component: 'TaskJobSim',
      title: '任务详情',
      narration:
        '点击任意任务可查看完整详情：输入参数（JSON 格式）、输出结果（JSON 格式）、错误信息（如有）、' +
        '执行耗时、重试次数等。每条记录完整保留执行快照，支持事后审计和问题排查。' +
        '失败任务支持一键重试，自动沿用原始参数重新执行。',
      highlight: '输入输出完整记录 · 一键重试 · 事后审计',
    },
    {
      component: 'TaskJobSim',
      title: '真实架构说明',
      narration:
        '⚠️ 重要说明：当前演示环境为方便展示，将任务平台集成在系统内部。' +
        '在真实业务场景中，我们采用独立的任务管理平台架构——工作流引擎通过 RESTful API 调用外部任务平台，' +
        '任务平台支持接入各种异构系统（CMDB、DNS、监控、IT 服务台等），统一调度和管理所有自动化任务。' +
        '这种解耦架构使得工作流引擎专注于流程编排，任务平台专注于任务调度，各自独立演进、独立扩展。',
      highlight: '独立任务平台 · 解耦架构 · 外部系统统一调度',
    },
  ],
}
