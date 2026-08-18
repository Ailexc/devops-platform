import type { Scene } from '@/types/presentation'

/** 场景 6：端到端演示 */
export const sceneDemo: Scene = {
  id: 'demo',
  title: '端到端演示',
  description: 'IT 运维自动化完整流程',
  themeColor: '#67c23a',
  role: 'xiaoming',
  roleLabel: '研发工程师',
  duration: '~4 分钟',
  steps: [
    {
      component: 'ProcessOverviewSim',
      title: '发起申请',
      focus: 'apply',
      narration:
        '小明需要一台测试服务器。在「发起申请」页面，系统根据小明的角色权限自动过滤可发起的流程，' +
        '展示服务器申请、采购申请、请假申请等模版。小明选择「服务器申请」流程，进入表单填写。',
      highlight: '角色权限过滤 · 流程模版选择',
    },
    {
      component: 'ProcessOverviewSim',
      title: '填写表单',
      focus: 'apply',
      narration:
        '填写服务器申请表单：主机名 web-test-01、CPU 4 核、内存 8 GB、操作系统 CentOS 7，' +
        '申请理由「线上扩容，支撑业务增长」。表单由流程定义动态生成，支持多种字段类型和校验规则。' +
        '确认无误后点击提交，流程自动进入审批链路。',
      highlight: '动态表单 · 字段校验 · 自动流转',
    },
    {
      component: 'ProcessOverviewSim',
      title: '状态追踪',
      focus: 'my',
      narration:
        '提交后切换到「我的申请」标签页，可以看到刚刚提交的服务器申请状态为「运行中」，' +
        '当前节点显示「运维审批」，等待审批人处理。' +
        '系统实时更新流程状态，申请人随时掌握进度。',
      highlight: '实时状态更新 · 当前节点追踪',
    },
    {
      component: 'ProcessOverviewSim',
      title: '待办审批',
      focus: 'todo',
      narration:
        '运维小李收到待办通知，在「待办审批」列表中看到这条申请。' +
        '点击「办理」按钮进入任务详情页，查看申请信息（主机名、配置、申请理由等）。',
      highlight: '待办自动推送 · 一键办理',
    },
    {
      component: 'TaskDetailSim',
      title: '审批通过',
      focus: 'approval',
      narration:
        '小李查看申请详情，确认当前资源池充足后，填写审批意见「资源充足，同意开通」，' +
        '点击「同意」按钮。审批通过后，流程自动流转到下一个节点——自动开通。',
      highlight: '审批意见必填 · 流程自动流转',
    },
    {
      component: 'TaskDetailSim',
      title: '自动开通',
      focus: 'autoExecute',
      narration:
        '审批通过后，系统自动调用 CMDB 创建主机（主机 ID: host-20260808-001，IP: 10.0.1.100），' +
        '随后自动配置 DNS 解析、发送通知邮件给申请人。整个过程无需人工操作，仅耗时数秒。' +
        '这就是自动办理节点的价值——程序代理人员自动通过，大幅缩短工单流转时间。',
      highlight: '程序代理自动执行 · 数秒完成 · 无需人工',
    },
    {
      component: 'EventLogSim',
      title: '事件审计',
      focus: 'table',
      narration:
        '事件日志完整记录了整条链路的每一步：流程发起、待办创建、审批通过、CMDB 主机创建、' +
        'DNS 配置、邮件通知。每条日志包含时间戳、事件类型、事件来源和详细描述，' +
        '支持按类型筛选，满足审计与排查需求。',
      highlight: '全链路审计 · 按类型筛选 · 时间戳记录',
    },
    {
      component: 'DemoSummarySim',
      title: '演示总结',
      narration:
        '完成！从申请到开通全程自动化，人工仅需审批一步。' +
        '传统模式需要 4~8 小时的人工逐级操作，本平台缩短到 5~15 分钟。' +
        '这就是流程驱动的业务自动化——让业务人员专注于业务本身，而非流程流转。',
      highlight: '全流程自动化 · 效率提升 80%',
    },
  ],
}
