// 演示幻灯片数据
export const scenes = [
  {
    id: 'system-overview',
    title: '系统能力宣讲',
    description: '全方位展示系统架构与核心能力',
    slides: [
      {
        type: 'hero',
        title: '流程驱动的业务自动化平台',
        subtitle: 'Workflow Engine',
        description: '基于 Django + Vue 3 的现代化工作流引擎，支持可视化流程设计、智能表单、多级审批和自动化执行',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      },
      {
        type: 'text',
        title: '技术架构全景',
        content: '系统采用前后端分离架构，后端基于 Django 5 + DRF，前端使用 Vue 3 + Element Plus',
        bullets: [
          '后端：Django 5 + DRF + Celery + Redis',
          '前端：Vue 3 + Element Plus + Pinia',
          '流程引擎：自研轻量级 BPM 引擎',
          '数据库：PostgreSQL',
          '消息队列：Celery + Redis',
        ],
      },
      {
        type: 'text',
        title: '流程设计器',
        content: '可视化拖拽式流程设计器，零代码配置审批链路',
        bullets: [
          '支持串行/并行/条件分支/会签/或签',
          '拖拽式节点配置，所见即所得',
          '支持程序发起和人工发起',
          '节点配置实时预览',
        ],
      },
      {
        type: 'text',
        title: '表单引擎',
        content: '动态表单引擎，支持 AI 智能生成',
        bullets: [
          'JSON Schema 驱动的动态表单',
          '支持 20+ 表单组件',
          'AI 智能生成表单 schema',
          '表单数据自动关联流程变量',
        ],
      },
      {
        type: 'text',
        title: '审批引擎',
        content: '灵活的审批引擎，满足各种审批场景',
        bullets: [
          '串行审批：按顺序逐级审批',
          '并行审批：多人同时审批',
          '会签：所有人通过才算通过',
          '或签：一人通过即通过',
          '条件分支：根据条件自动路由',
        ],
      },
      {
        type: 'text',
        title: '自动化执行',
        content: '流程节点支持自动执行绑定的能力',
        bullets: [
          '能力注册中心：统一管理可执行能力',
          'Mock 执行器：开发测试环境模拟执行',
          'HTTP 执行器：调用外部 API',
          '任务配置：可视化配置执行参数',
        ],
      },
      {
        type: 'text',
        title: '程序发起',
        content: '支持外部系统通过 API 发起流程',
        bullets: [
          'RESTful API 接口',
          'API Key 认证',
          '发起程序管理',
          '支持 Webhook 回调',
        ],
      },
      {
        type: 'text',
        title: '事件驱动',
        content: '基于事件总线的异步处理机制',
        bullets: [
          '事件发布：流程状态变更自动发布事件',
          'Webhook 订阅：外部系统订阅事件',
          '事件日志：完整的事件追踪',
          '异步处理：Celery 异步任务队列',
        ],
      },
      {
        type: 'text',
        title: '数据看板',
        content: '实时数据统计，掌握流程运行状况',
        bullets: [
          '待办统计：我的待办、我的申请',
          '流程统计：进行中、已完成、已终止',
          '效率指标：平均审批时长、完成率',
          '趋势分析：流程执行趋势图',
        ],
      },
      {
        type: 'hero',
        title: '技术亮点与可扩展性',
        subtitle: 'Summary',
        description: '模块化设计 | 插件化扩展 | 高性能 | 易集成',
        background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
      },
    ],
  },
  {
    id: 'demo-scene',
    title: '端到端流程演示',
    description: 'IT 运维自动化场景演示',
    slides: [
      {
        type: 'hero',
        title: 'IT 运维自动化场景',
        subtitle: 'Workflow Demo',
        description: '通过真实的 IT 运维场景，展示流程引擎的完整能力',
        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      },
      {
        type: 'text',
        title: '场景一：服务器申请（人工发起）',
        content: '员工通过页面发起服务器申请，经过运维审批后自动开通',
        bullets: [
          '发起人：小明（研发组）',
          '审批人：小李（IT运维组）',
          '流程：提交 → 运维审批 → 自动开通 → 完成',
          '表单：主机名、CPU、内存、操作系统、申请理由',
        ],
      },
      {
        type: 'text',
        title: '场景二：服务器申请（程序发起）',
        content: 'CMDB 系统通过 API 自动发起服务器申请，无需人工审批',
        bullets: [
          '发起程序：CMDB 资产同步',
          '认证方式：API Key',
          '流程：API 调用 → 自动开通 → 完成',
          '特点：跳过审批，直接执行',
        ],
      },
      {
        type: 'text',
        title: '场景三：新增服务申请',
        content: '开发团队申请新增服务部署，需要部门主管和运维双重审批',
        bullets: [
          '发起人：小红（研发组）',
          '审批链：部门主管 → 运维开通',
          '表单：服务名称、类型、环境、资源需求',
          '特点：多级审批 + 自动执行',
        ],
      },
      {
        type: 'text',
        title: '场景四：服务器重启（纯程序）',
        content: '运维脚本自动触发服务器重启，无需任何审批',
        bullets: [
          '发起程序：CMDB 资产同步 / IT 服务台',
          '流程：API 调用 → 自动重启 → 完成',
          '特点：最简流程，纯自动化',
        ],
      },
      {
        type: 'text',
        title: '三种发起模式对比',
        content: '系统支持三种发起模式，满足不同场景需求',
        bullets: [
          '人工+程序：灵活配置，可设置审批或直接执行',
          '纯程序：API 触发，自动执行，适合运维场景',
          '纯人工：页面发起，必须审批，适合正式流程',
        ],
      },
      {
        type: 'text',
        title: '演示数据说明',
        content: '预置的种子数据包含完整的组织架构和流程配置',
        bullets: [
          '组织架构：技术部（研发+运维）、财务部、总经办',
          '流程定义：3 个演示流程，支持程序和人工发起',
          '预置实例：2 个服务器申请实例（运行中+已完成）',
          '发起程序：CMDB 资产同步、IT 服务台',
        ],
      },
      {
        type: 'hero',
        title: '感谢观看',
        subtitle: 'Thank You',
        description: '流程驱动，让业务自动化更简单',
        background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      },
    ],
  },
]

export default scenes
