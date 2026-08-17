import { Typography, Table, Tag, Card, Descriptions, List, Space, Alert, Divider } from 'antd';
import {
  ReloadOutlined,
  FireOutlined,
  EyeOutlined,
  AlertOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  NodeIndexOutlined,
  ExperimentOutlined,
  RollbackOutlined,
  SwapOutlined,
  CloudServerOutlined,
  PercentageOutlined,
  SafetyOutlined,
  ApartmentOutlined,
  BuildOutlined,
  ContainerOutlined,
} from '@ant-design/icons';

const { Paragraph, Text } = Typography;

/* ============ 策略图标映射 ============ */

const STRATEGY_ICONS: Record<string, React.ReactNode> = {
  rolling: <SwapOutlined />,
  blue_green: <CloudServerOutlined />,
  canary: <PercentageOutlined />,
  recreate: <ReloadOutlined />,
  red_black: <FireOutlined />,
  shadow: <EyeOutlined />,
};

const MODE_ICONS: Record<string, React.ReactNode> = {
  regular: <ThunderboltOutlined />,
  incremental: <NodeIndexOutlined />,
  compensation: <ExperimentOutlined />,
  quick: <ThunderboltOutlined />,
  rollback: <RollbackOutlined />,
  emergency: <AlertOutlined />,
  scheduled: <ClockCircleOutlined />,
};

/* ============ EC2 vs K8s 对比表通用列定义 ============ */

const ec2VsK8sColumns = [
  { title: '对比维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
  { title: 'EC2 模式', dataIndex: 'ec2', key: 'ec2' },
  { title: 'K8s 模式', dataIndex: 'k8s', key: 'k8s' },
];

/* ============ SVG 架构图组件 ============ */

const RecreateSVG = () => (
  <svg viewBox="0 0 800 380" style={{ width: '100%', maxWidth: 800, height: 'auto' }}>
    <text x="400" y="28" textAnchor="middle" fontSize="15" fontWeight="bold" fill="#333">重建部署过程示意（先停旧 → 再启新）</text>

    {/* 阶段一：初始状态 */}
    <text x="30" y="65" fontSize="12" fill="#666" textAnchor="start">阶段一：初始状态</text>
    {[0, 1, 2].map((i) => (
      <rect key={`init-${i}`} x={150 + i * 160} y={50} width="130" height="36" rx="6" fill="#e6f4ff" stroke="#1677ff" strokeWidth="1.5" />
    ))}
    {[0, 1, 2].map((i) => (
      <text key={`init-t${i}`} x={215 + i * 160} y="73" textAnchor="middle" fontSize="12" fill="#1677ff">v1 Pod-{i + 1}</text>
    ))}
    <text x="400" y="105" textAnchor="middle" fontSize="11" fill="#999">3 个 v1 版本 Pod 正在运行，正常提供服务</text>

    {/* 阶段二：停止阶段 */}
    <text x="30" y="145" fontSize="12" fill="#f5222d" textAnchor="start">阶段二：停止阶段</text>
    {[0, 1, 2].map((i) => (
      <rect key={`stop-${i}`} x={150 + i * 160} y={130} width="130" height="36" rx="6" fill="#fff1f0" stroke="#f5222d" strokeWidth="1.5" strokeDasharray="4,2" />
    ))}
    {[0, 1, 2].map((i) => (
      <text key={`stop-t${i}`} x={215 + i * 160} y="153" textAnchor="middle" fontSize="12" fill="#f5222d">v1 Pod-{i + 1}（已终止）</text>
    ))}

    {/* 服务中断窗口标注 */}
    <rect x={150} y={175} width={450} height={28} rx="4" fill="#fff2e8" stroke="#fa8c16" strokeWidth="1.5" strokeDasharray="4,2" />
    <text x="375" y="194" textAnchor="middle" fontSize="12" fill="#d46b08" fontWeight="bold">⚠️ 服务中断窗口：所有 Pod 已停止，服务暂时不可用</text>

    {/* 阶段三：启动阶段 */}
    <text x="30" y="240" fontSize="12" fill="#52c41a" textAnchor="start">阶段三：启动阶段</text>
    {[0, 1, 2].map((i) => (
      <rect key={`start-${i}`} x={150 + i * 160} y={225} width="130" height="36" rx="6" fill="#f6ffed" stroke="#52c41a" strokeWidth="1.5" />
    ))}
    {[0, 1, 2].map((i) => (
      <text key={`start-t${i}`} x={215 + i * 160} y="248" textAnchor="middle" fontSize="12" fill="#389e0d">v2 Pod-{i + 1}</text>
    ))}
    <text x="400" y="280" textAnchor="middle" fontSize="11" fill="#999">3 个 v2 版本 Pod 启动中，就绪后恢复服务</text>

    {/* 连接箭头 */}
    <path d="M400 86 L400 128" stroke="#999" strokeWidth="1.5" markerEnd="url(#recArrow)" />
    <path d="M400 203 L400 223" stroke="#999" strokeWidth="1.5" markerEnd="url(#recArrow)" />

    {/* 时间线 */}
    <line x1="30" y1="310" x2="770" y2="310" stroke="#ccc" strokeWidth="2" />
    <text x="30" y="335" fontSize="11" fill="#999">时间线</text>
    <text x="180" y="335" fontSize="11" fill="#1677ff">服务正常</text>
    <text x="320" y="335" fontSize="11" fill="#f5222d">服务中断</text>
    <text x="520" y="335" fontSize="11" fill="#52c41a">服务恢复</text>

    {/* 时间线分段 */}
    <rect x="30" y="303" width="210" height="14" rx="2" fill="#1677ff" opacity="0.3" />
    <rect x="240" y="303" width="180" height="14" rx="2" fill="#f5222d" opacity="0.3" />
    <rect x="420" y="303" width="350" height="14" rx="2" fill="#52c41a" opacity="0.3" />

    <defs>
      <marker id="recArrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="#999" />
      </marker>
    </defs>
  </svg>
);

const RedBlackSVG = () => (
  <svg viewBox="0 0 800 420" style={{ width: '100%', maxWidth: 800, height: 'auto' }}>
    <text x="400" y="28" textAnchor="middle" fontSize="15" fontWeight="bold" fill="#333">红黑部署架构示意（Netflix 风格）</text>

    {/* 用户 */}
    <rect x="280" y="50" width="140" height="40" rx="20" fill="#e6f4ff" stroke="#1677ff" strokeWidth="1.5" />
    <text x="350" y="75" textAnchor="middle" fontSize="13" fill="#1677ff">用户请求</text>
    <path d="M350 90 L350 120" stroke="#333" strokeWidth="2" />

    {/* 负载均衡器 */}
    <rect x="250" y="120" width="200" height="44" rx="6" fill="#fff7e6" stroke="#fa8c16" strokeWidth="2" />
    <text x="350" y="146" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#d46b08">负载均衡器 / 网关</text>

    {/* 切换开关 */}
    <rect x="295" y="175" width="110" height="28" rx="14" fill="#f5222d" stroke="#cf1322" strokeWidth="1.5" />
    <text x="350" y="194" textAnchor="middle" fontSize="12" fill="#fff" fontWeight="bold">流量切换</text>

    {/* 连接线 */}
    <path d="M300 203 L300 240 L160 240 L160 270" stroke="#f5222d" strokeWidth="2" fill="none" />
    <path d="M400 203 L400 240 L540 240 L540 270" stroke="#52c41a" strokeWidth="2" fill="none" />

    {/* 红色环境（旧 - 即将销毁） */}
    <rect x="60" y="270" width="200" height="100" rx="8" fill="#fff1f0" stroke="#f5222d" strokeWidth="2" />
    <text x="160" y="295" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#cf1322">红色环境 (Red)</text>
    <text x="160" y="315" textAnchor="middle" fontSize="12" fill="#cf1322">v1 版本（即将销毁）</text>
    <rect x="80" y="325" width="160" height="28" rx="4" fill="#f5222d" opacity="0.15" />
    <text x="160" y="344" textAnchor="middle" fontSize="11" fill="#cf1322">切换后立即回收 ⚡</text>

    {/* 黑色环境（新 - 当前生产） */}
    <rect x="440" y="270" width="200" height="100" rx="8" fill="#f6ffed" stroke="#52c41a" strokeWidth="2" />
    <text x="540" y="295" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#389e0d">黑色环境 (Black)</text>
    <text x="540" y="315" textAnchor="middle" fontSize="12" fill="#389e0d">v2 版本（当前生产）</text>
    <rect x="460" y="325" width="160" height="28" rx="4" fill="#52c41a" opacity="0.15" />
    <text x="540" y="344" textAnchor="middle" fontSize="11" fill="#389e0d">承载 100% 生产流量</text>

    {/* 回收箭头 */}
    <path d="M160 375 L160 395" stroke="#f5222d" strokeWidth="2" markerEnd="url(#redArr)" />
    <text x="160" y="410" textAnchor="middle" fontSize="11" fill="#f5222d">旧环境立即销毁回收</text>

    {/* 与蓝绿对比标注 */}
    <rect x="60" y="45" width="680" height="0" fill="none" />
    <text x="400" y="410" textAnchor="middle" fontSize="11" fill="#999">关键区别：与蓝绿不同，红黑切换后旧环境立即回收，不保留用于回滚</text>

    <defs>
      <marker id="redArr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="#f5222d" />
      </marker>
    </defs>
  </svg>
);

const ShadowSVG = () => (
  <svg viewBox="0 0 800 340" style={{ width: '100%', maxWidth: 800, height: 'auto' }}>
    <text x="400" y="28" textAnchor="middle" fontSize="15" fontWeight="bold" fill="#333">影子部署架构示意（流量镜像）</text>

    {/* 用户请求 */}
    <rect x="280" y="50" width="140" height="40" rx="20" fill="#e6f4ff" stroke="#1677ff" strokeWidth="1.5" />
    <text x="350" y="75" textAnchor="middle" fontSize="13" fill="#1677ff">生产流量</text>
    <path d="M350 90 L350 120" stroke="#333" strokeWidth="2" />

    {/* 网关/Service Mesh */}
    <rect x="250" y="120" width="200" height="44" rx="6" fill="#fff7e6" stroke="#fa8c16" strokeWidth="2" />
    <text x="350" y="142" textAnchor="middle" fontSize="13" fontWeight="bold" fill="#d46b08">网关 / Service Mesh</text>
    <text x="350" y="156" textAnchor="middle" fontSize="10" fill="#d46b08">流量复制 + 路由</text>

    {/* 分支 */}
    <path d="M300 164 L300 200 L160 200 L160 230" stroke="#1677ff" strokeWidth="2.5" fill="none" />
    <path d="M400 164 L400 200 L540 200 L540 230" stroke="#999" strokeWidth="2" fill="none" strokeDasharray="8,4" />

    {/* 生产环境 v1 */}
    <rect x="60" y="230" width="200" height="80" rx="8" fill="#e6f4ff" stroke="#1677ff" strokeWidth="2" />
    <text x="160" y="255" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#1677ff">生产环境 v1</text>
    <text x="160" y="275" textAnchor="middle" fontSize="11" fill="#1677ff">处理真实请求</text>
    <text x="160" y="295" textAnchor="middle" fontSize="11" fill="#1677ff">返回响应给用户</text>

    {/* 影子环境 v2 */}
    <rect x="440" y="230" width="200" height="80" rx="8" fill="#f5f5f5" stroke="#999" strokeWidth="2" strokeDasharray="6,3" />
    <text x="540" y="255" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#666">影子环境 v2</text>
    <text x="540" y="275" textAnchor="middle" fontSize="11" fill="#666">接收流量副本</text>
    <text x="540" y="295" textAnchor="middle" fontSize="11" fill="#666">响应被丢弃 ✗</text>

    {/* 流量标注 */}
    <text x="220" y="215" textAnchor="middle" fontSize="11" fill="#1677ff" fontWeight="bold">100% 真实流量</text>
    <text x="490" y="215" textAnchor="middle" fontSize="11" fill="#999">镜像流量（仅监控）</text>

    {/* 监控对比区域 */}
    <rect x="200" y="322" width="300" height="15" rx="3" fill="#f0f5ff" stroke="#1677ff" strokeWidth="1" />
    <text x="350" y="333" textAnchor="middle" fontSize="10" fill="#1677ff">监控对比：错误率 | 延迟 | 资源消耗 | 输出一致性</text>

    <defs>
      <marker id="shArrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="#333" />
      </marker>
    </defs>
  </svg>
);

/* ============ 新增策略对比数据 ============ */

const recreateComparisonData = [
  { key: '1', dimension: '实现方式', ec2: '通过 SSH 连接到所有实例，执行 stop 命令停止服务，再执行 start 命令启动新版本', k8s: '将 Deployment 副本数缩容至 0，等待所有 Pod 终止后，更新镜像版本再扩容至期望副本数' },
  { key: '2', dimension: '服务中断', ec2: '停止所有实例后服务完全中断，启动新实例后逐步恢复', k8s: '缩容到 0 后服务完全中断，新 Pod 启动并通过 Readiness Probe 后恢复' },
  { key: '3', dimension: '回滚策略', ec2: '重新部署旧版本到所有实例，需要完整部署流程', k8s: 'kubectl rollout undo 回滚到上一个 ReplicaSet 版本' },
  { key: '4', dimension: '配置文件', ec2: '使用部署脚本控制停止和启动流程，需自行管理状态', k8s: 'Deployment spec.replicas 控制副本数，声明式管理，配置简单' },
  { key: '5', dimension: '监控方式', ec2: 'CloudWatch 监控实例状态，需手动确认所有实例已停止/启动', k8s: 'kubectl get pods 查看 Pod 状态，配合 rollout status 追踪进度' },
];

const redBlackComparisonData = [
  { key: '1', dimension: '实现方式', ec2: '创建新的 ASG（自动伸缩组），部署新版本，切换 ELB 流量后立即删除旧 ASG', k8s: '创建新 Deployment，修改 Service Selector 切换流量，立即删除旧 Deployment' },
  { key: '2', dimension: '流量切换', ec2: '修改 ELB Target Group 指向新 ASG，切换秒级完成', k8s: '更新 Service Label Selector 指向新 Deployment，切换瞬间完成' },
  { key: '3', dimension: '回滚策略', ec2: '旧 ASG 已删除，需重新创建旧版本的 ASG（从 AMI/快照恢复）', k8s: '旧 Deployment 已删除，需重新创建旧版本 Deployment（从历史镜像）' },
  { key: '4', dimension: '资源管理', ec2: '切换后立即释放旧 ASG 资源，成本较低', k8s: '切换后立即删除旧 Deployment，释放 Pod 和资源' },
  { key: '5', dimension: '配置文件', ec2: '两套 ASG Launch Configuration，切换后删除旧配置', k8s: '两个 Deployment YAML，切换后删除旧 Deployment 资源' },
];

const shadowComparisonData = [
  { key: '1', dimension: '实现方式', ec2: '通过 ELB 或 Nginx 的 mirror 模块将流量复制到影子实例组', k8s: '通过 Istio VirtualService 的 mirror 字段将流量镜像到影子 Deployment' },
  { key: '2', dimension: '流量处理', ec2: '影子实例接收请求副本，处理但不返回响应，响应被丢弃', k8s: '影子 Pod 接收镜像请求，Sidecar 自动丢弃响应，不影响用户' },
  { key: '3', dimension: '副作用隔离', ec2: '需自行处理影子实例的数据库写入隔离（如使用影子数据库）', k8s: '可通过独立 ConfigMap 配置影子实例的数据库连接，指向影子数据库' },
  { key: '4', dimension: '性能影响', ec2: '影子实例的资源消耗需独立监控，避免影响生产实例', k8s: '通过 Resource Quota 和 LimitRange 限制影子实例的资源使用' },
  { key: '5', dimension: '监控方式', ec2: '对比生产实例和影子实例的 CloudWatch 指标，手工分析差异', k8s: 'Prometheus 按版本标签聚合指标，Grafana 仪表盘实时对比差异' },
];

/* ============ 新增部署策略 ============ */

export const strategyData = [
  {
    key: 'recreate',
    label: '重建部署（Recreate Deployment）',
    icon: STRATEGY_ICONS.recreate,
    color: 'volcano',
    sections: [
      {
        title: '历史背景与名称由来',
        content: (
          <Paragraph>
            重建部署（Recreate）是<Text strong>最原始、最直观</Text>的部署策略。在容器化技术兴起之前，
            几乎所有应用部署都是这种模式——<Text strong>先停止旧服务，再启动新服务</Text>。
            在 K8s 中，Recreate 是 Deployment 提供的两种策略类型之一（另一种是 RollingUpdate），
            但 K8s 默认使用 RollingUpdate，Recreate 需要显式指定。
            这种策略名称直接来源于其行为：「重建」——<Text strong>完全销毁旧实例，再创建全新实例</Text>。
          </Paragraph>
        ),
      },
      {
        title: '核心原理',
        content: (
          <Paragraph>
            重建部署的核心原理是<Text strong>「全量替换」</Text>：先终止所有旧版本实例，
            等待全部实例停止后，再启动所有新版本实例。整个过程存在一个明确的<Text strong>服务中断窗口</Text>——
            从旧实例停止到新实例就绪之间的时间段，服务完全不可用。
            其本质是一种<Text strong>简单粗暴、但有停机时间</Text>的部署方式。
          </Paragraph>
        ),
      },
      {
        title: 'SVG 架构图',
        content: <RecreateSVG />,
      },
      {
        title: '工作流程',
        content: {
          type: 'steps',
          steps: [
            '发布触发',
            '终止所有旧版本实例',
            '等待所有实例完全停止',
            '服务中断（服务不可用）',
            '启动新版本实例',
            '等待新实例就绪',
            '服务恢复',
            '验证新版本',
          ],
        },
      },
      {
        title: 'K8s 配置示例',
        content: (
          <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 13 }}>
{`apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  strategy:
    type: Recreate    # 重建部署策略
  template:
    spec:
      containers:
      - name: app
        image: my-app:v2`}
          </pre>
        ),
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={recreateComparisonData}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>开发/测试环境，可接受短暂服务中断</li>
            <li>单实例部署的应用（如一些内部工具）</li>
            <li>新旧版本完全<Text strong>不兼容</Text>，无法共存</li>
            <li>数据库 Schema 有<Text strong>破坏性变更</Text>，需要确保只有一个版本运行</li>
            <li>有状态应用，不支持多实例同时运行</li>
            <li>资源极度紧张，无法同时运行新旧实例</li>
          </ul>
        ),
      },
      {
        title: '不适用场景',
        content: (
          <ul>
            <li><Text strong>生产环境：</Text>服务中断不可接受</li>
            <li><Text strong>高可用要求：</Text>需要 7×24 持续服务的业务</li>
            <li><Text strong>大规模集群：</Text>全部实例同时重启对下游服务造成冲击</li>
            <li><Text strong>金融/支付系统：</Text>任何中断都可能造成重大损失</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>实现简单：</Text>逻辑清晰，理解成本低</li>
            <li><Text strong>不产生兼容性问题：</Text>新旧版本从不共存</li>
            <li><Text strong>资源消耗低：</Text>不需要同时维护两套环境</li>
            <li><Text strong>状态干净：</Text>旧实例完全清理，无残留问题</li>
            <li><Text strong>适合破坏性变更：</Text>数据库 Schema 大改时唯一可行的方式</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>服务中断：</Text>存在明确的停机窗口，影响用户体验</li>
            <li><Text strong>回滚慢：</Text>需要重新走完整部署流程</li>
            <li><Text strong>风险集中：</Text>所有实例同时切换，问题影响面 100%</li>
            <li><Text strong>启动时间敏感：</Text>新实例启动慢会导致长时间中断</li>
            <li><Text strong>不适合生产环境：</Text>绝大多数生产场景不适用</li>
          </ul>
        ),
      },
      {
        title: '与滚动更新的对比表',
        content: {
          type: 'table',
          columns: ['对比维度', '重建部署', '滚动更新'],
          rows: [
            ['服务可用性', '有中断窗口', '持续可用（零停机）'],
            ['新旧共存', '不共存', '短期内共存'],
            ['兼容性要求', '无', '新旧版本需兼容'],
            ['部署速度', '取决于启动时间', '取决于副本数和参数'],
            ['回滚速度', '慢（需重新部署）', '中（反向滚动更新）'],
            ['资源消耗', '低（1x）', '低（1x + maxSurge）'],
            ['适用环境', '测试/开发', '生产环境'],
            ['K8s 配置', 'strategy.type: Recreate', 'strategy.type: RollingUpdate（默认）'],
          ],
        },
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: 'Recreate 部署在什么情况下是唯一的选择？',
              a: '当新旧版本存在不兼容的破坏性变更时，Recreate 是唯一选择。典型场景包括：1) 数据库 Schema 有破坏性变更（如删除字段、修改字段类型），新旧版本同时运行会导致数据不一致；2) 有状态应用不支持多实例同时运行（如某些嵌入式数据库）；3) 资源极度紧张，无法同时运行两份实例。在这些情况下，任何滚动更新策略都会导致严重问题。',
            },
            {
              q: 'Recreate 部署如何最小化服务中断时间？',
              a: '可以通过以下方式优化：1) 优化应用启动时间——使用轻量级镜像、减少初始化逻辑、使用健康检查快速就绪；2) 预拉取镜像——提前在节点上拉取新版本镜像，避免启动时等待下载；3) 使用蓝绿部署的变体——先创建新实例，验证通过后再停止旧实例（但这就不是 Recreate 了）；4) 在低峰期执行——选择业务流量最低的时间窗口进行部署。',
            },
            {
              q: 'K8s 中 Recreate 和 RollingUpdate 的内部实现有何不同？',
              a: '在 K8s 中，Deployment Controller 的行为完全不同：Recreate 模式下，Controller 会先将旧 ReplicaSet 的副本数缩容到 0，等待所有 Pod 终止后，再创建新 ReplicaSet 并扩容到期望副本数。RollingUpdate 模式下，Controller 会同时管理新旧两个 ReplicaSet，逐步增加新 ReplicaSet 的副本数，同时减少旧 ReplicaSet 的副本数，确保任何时候都有足够的 Pod 在运行。',
            },
            {
              q: '如果在 Recreate 部署过程中新版本启动失败怎么办？',
              a: '这是 Recreate 部署的最大风险——旧实例已停止，新实例启动失败，服务完全不可用。应对措施：1) 部署前充分验证——在预发环境验证新版本启动正常；2) 保留旧版本镜像——快速回滚到旧版本；3) 设置启动超时——如果新版本在超时时间内未就绪，自动回滚；4) 监控告警——立即通知运维人员介入。这也是为什么生产环境不推荐使用 Recreate 的原因。',
            },
          ],
        },
      },
    ],
  },
  {
    key: 'red_black',
    label: '红黑部署（Red-Black Deployment）',
    icon: STRATEGY_ICONS.red_black,
    color: 'red',
    sections: [
      {
        title: '历史背景（Netflix 起源）',
        content: (
          <Paragraph>
            红黑部署（Red-Black Deployment）由<Text strong>Netflix</Text> 在构建其大规模微服务架构时提出并推广。
            Netflix 使用自研的持续交付平台<Text strong>Spinnaker</Text> 来实现红黑部署，
            这是 Netflix 云原生实践的重要组成部分。在 Netflix 的文化中，「红」代表旧版本（即将退役），
            「黑」代表新版本（当前活跃），这种命名方式源自 Netflix 内部的部署术语。
            <br /><br />
            Netflix 之所以选择红黑而非蓝绿，核心原因是<Text strong>资源优化</Text>：
            在 AWS 上运行数千个微服务，如果每个服务都保留两套环境，成本会非常高昂。
            红黑部署在切换后立即回收旧环境，在保证快速切换的同时，大幅降低了资源成本。
          </Paragraph>
        ),
      },
      {
        title: '核心原理',
        content: (
          <Paragraph>
            红黑部署的核心原理与蓝绿部署相似，但有一个关键区别：<Text strong>切换后旧环境不保留，立即回收销毁</Text>。
            流程：创建新环境（Black）→ 部署新版本 → 验证通过 → 切换流量 → 立即销毁旧环境（Red）。
            其本质是蓝绿部署的<Text strong>资源优化变体</Text>，牺牲了「秒级回滚」的能力，换取了「资源成本减半」的优势。
          </Paragraph>
        ),
      },
      {
        title: 'SVG 架构图',
        content: <RedBlackSVG />,
      },
      {
        title: '关键参数',
        content: (
          <div>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 12 }}>
              <Descriptions.Item label="切换时间" span={2}>
                <Text strong>流量切换耗时</Text> — 与蓝绿部署相同，通常秒级完成。通过负载均衡器或 Service Mesh 路由规则切换。
              </Descriptions.Item>
              <Descriptions.Item label="旧环境保留时间" span={2}>
                <Text strong>关键区别：</Text>与蓝绿不同，旧环境在切换后<Text type="danger">立即回收（0 保留时间）</Text>。
                这是红黑与蓝绿最本质的区别。如果需要在切换后快速回滚，需提前准备旧版本快照。
              </Descriptions.Item>
              <Descriptions.Item label="预热时间" span={2}>
                <Text strong>预热时间</Text> — 新环境在切换前需要充分预热，确保切换后能立即提供稳定服务。
                因为切换后没有旧环境兜底，预热质量直接影响服务质量。
              </Descriptions.Item>
              <Descriptions.Item label="回滚方式" span={2}>
                <Text strong>回滚方式</Text> — 旧环境已销毁，回滚需要重新创建旧版本环境（从镜像/AMI/快照恢复）。
                回滚时间取决于新环境创建速度，通常需要几分钟。如果需要秒级回滚，应使用蓝绿部署。
              </Descriptions.Item>
            </Descriptions>
          </div>
        ),
      },
      {
        title: '与蓝绿部署的详细对比表',
        content: {
          type: 'table',
          columns: ['对比维度', '蓝绿部署', '红黑部署'],
          rows: [
            ['旧环境保留', '切换后保留旧环境（24-48小时）', '切换后立即销毁旧环境'],
            ['回滚方式', '切换回旧环境（秒级）', '重新创建旧版本（分钟级）'],
            ['回滚速度', '极快（秒级）', '较慢（需重新部署）'],
            ['资源成本', '高（持续 2x 资源）', '中（切换后降至 1x）'],
            ['适用场景', '对回滚速度要求极高的服务', '资源优化优先的服务'],
            ['风险', '低（旧环境随时可用）', '中（回滚需重新部署）'],
            ['典型用户', '金融、支付系统', 'Netflix、流媒体服务'],
            ['实现平台', 'K8s、AWS、GCP 通用', 'Spinnaker 原生支持'],
            ['环境命名', 'Blue / Green', 'Red / Black'],
            ['哲学', '安全第一，保留逃生通道', '效率优先，资源快速回收'],
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={redBlackComparisonData}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '工作流程',
        content: {
          type: 'steps',
          steps: [
            '创建新环境（Black）',
            '部署新版本到 Black',
            '预热 + 验证 Black',
            '切换流量到 Black',
            '立即销毁旧环境（Red）',
            '监控 Black 运行状态',
            '（如需回滚）重新创建旧版本',
          ],
        },
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li><Text strong>大规模微服务架构：</Text>数百个服务同时做蓝绿部署资源成本过高</li>
            <li><Text strong>资源敏感的业务：</Text>需要控制云资源成本</li>
            <li><Text strong>发布频率高：</Text>频繁切换，旧环境保留意义不大</li>
            <li><Text strong>回滚可接受分钟级延迟：</Text>不需要秒级回滚</li>
            <li><Text strong>使用 Spinnaker 的团队：</Text>Spinnaker 原生支持红黑部署</li>
          </ul>
        ),
      },
      {
        title: '不适用场景',
        content: (
          <ul>
            <li><Text strong>金融核心系统：</Text>需要秒级回滚能力</li>
            <li><Text strong>有状态服务：</Text>旧环境销毁会导致状态丢失</li>
            <li><Text strong>数据库变更频繁：</Text>回滚时数据库兼容性难以保证</li>
            <li><Text strong>小规模部署：</Text>资源成本差异不大，蓝绿部署更安全</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>资源效率高：</Text>切换后不保留旧环境，成本低于蓝绿</li>
            <li><Text strong>瞬间切换：</Text>与蓝绿相同，切换在秒级完成</li>
            <li><Text strong>环境干净：</Text>不会积累历史环境，管理简单</li>
            <li><Text strong>充分验证：</Text>切换前可在新环境完整验证</li>
            <li><Text strong>Netflix 验证：</Text>经过大规模生产环境验证的成熟策略</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>回滚慢：</Text>旧环境已销毁，回滚需要重新部署</li>
            <li><Text strong>需要快照机制：</Text>如需回滚，需提前准备旧版本快照</li>
            <li><Text strong>切换时机关键：</Text>切换后没有后悔药，必须一次成功</li>
            <li><Text strong>数据库兼容性：</Text>与蓝绿部署有相同的数据库兼容性挑战</li>
            <li><Text strong>不适合频繁回滚：</Text>如果回滚频率高，重新部署的成本会抵消资源节省</li>
          </ul>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '红黑部署和蓝绿部署的本质区别是什么？为什么 Netflix 选择红黑？',
              a: '本质区别在于旧环境的处理：蓝绿保留旧环境用于快速回滚，红黑在切换后立即销毁旧环境。Netflix 选择红黑的原因是：1) 规模——数千个微服务，如果都用蓝绿，资源成本无法承受；2) 文化——Netflix 推崇「快速失败、快速恢复」，与其保留旧环境不如快速重建；3) 工具链——Spinnaker 为红黑部署提供了完善的支持，包括回滚时自动从 AMI 重建旧版本。',
            },
            {
              q: '红黑部署中，如果切换后发现严重问题，如何回滚？',
              a: '旧环境已销毁，回滚需要走「重建」流程：1) 从镜像仓库或 AMI 快照中获取旧版本制品；2) 创建新环境（新的 Red）；3) 部署旧版本并验证；4) 切换流量到旧版本。整个过程需要几分钟。为了加速这个过程，可以：1) 保留旧版本镜像（不删除）；2) 保持旧版本配置模板；3) 自动化回滚流程。如果回滚速度是核心诉求，应选择蓝绿而非红黑。',
            },
            {
              q: '红黑部署在 K8s 中如何实现？与蓝绿部署的 K8s 实现有何不同？',
              a: '在 K8s 中，红黑部署的实现步骤：1) 创建新 Deployment（black）和对应 Service；2) 验证新版本；3) 修改 Ingress/Gateway 将流量切换到新 Service；4) 立即删除旧 Deployment（red）和旧 Service。蓝绿部署的区别在于第 4 步：蓝绿会保留旧 Deployment，而红黑会删除。从 YAML 配置角度看，两者的 Deployment 配置几乎相同，区别在于部署流程的自动化脚本中是否包含删除旧资源的步骤。',
            },
            {
              q: '红黑部署在什么场景下比蓝绿部署更合适？',
              a: '以下场景红黑优于蓝绿：1) 大规模微服务架构——资源成本是首要考量；2) 频繁发布——每天多次发布，旧环境保留的积累效应明显；3) 云成本敏感——使用按需付费的云资源；4) 拥有成熟的回滚自动化——旧版本镜像和配置模板管理完善，可以从快照快速重建；5) 团队文化接受「重建式回滚」——不依赖保留旧环境，而是信任自动化重建能力。',
            },
          ],
        },
      },
    ],
  },
  {
    key: 'shadow',
    label: '影子部署（Shadow Deployment）',
    icon: STRATEGY_ICONS.shadow,
    color: 'purple',
    sections: [
      {
        title: '历史背景',
        content: (
          <Paragraph>
            影子部署（Shadow Deployment / Traffic Mirroring）的概念最早出现在<Text strong>大规模分布式系统</Text>的测试需求中。
            随着微服务架构的普及，传统的压测工具（如 JMeter、Locust）无法完全模拟真实生产流量的复杂性——
            真实流量包含了各种边界情况、异常请求、复杂的用户行为模式。
            <br /><br />
            <Text strong>Google</Text> 和 <Text strong>Netflix</Text> 等公司在内部大规模使用流量镜像技术，
            后来<Text strong>Istio Service Mesh</Text> 将流量镜像功能标准化，使之成为云原生生态中的通用能力。
            影子部署不是一种「部署策略」而是一种「验证策略」——它不直接替换生产版本，而是在后台默默验证新版本。
          </Paragraph>
        ),
      },
      {
        title: '核心原理（流量镜像）',
        content: (
          <Paragraph>
            影子部署的核心原理是<Text strong>「流量镜像」</Text>：将发送到生产环境的真实请求<Text strong>异步复制</Text>一份，
            发送到新版本的影子实例。影子实例处理这些请求，但<Text strong>其响应被丢弃</Text>，不会返回给用户。
            用户始终与生产版本交互，完全感知不到影子实例的存在。
            <br /><br />
            影子部署的目的是<Text strong>在真实流量下验证新版本</Text>，而不承担任何风险。
            通过对比生产实例和影子实例的指标（响应时间、错误率、资源消耗、输出一致性），
            可以在不影响用户的前提下发现新版本的潜在问题。
          </Paragraph>
        ),
      },
      {
        title: 'SVG 架构图',
        content: <ShadowSVG />,
      },
      {
        title: '实现方式',
        content: (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small" title="方式一：Istio Traffic Mirroring">
                <Paragraph>
                  Istio 的 VirtualService 支持 <Text code>mirror</Text> 字段，可以将流量百分比复制到影子服务。
                  这是目前最成熟的影子部署实现方式。
                </Paragraph>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12 }}>
{`apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
  - my-app
  http:
  - route:
    - destination:
        host: my-app
        subset: v1        # 生产版本
      weight: 100
    mirror:
      host: my-app-shadow
      subset: v2          # 影子版本
    mirrorPercentage:
      value: 100.0        # 镜像 100% 流量`}
                </pre>
              </Card>
              <Card size="small" title="方式二：Nginx mirror 模块">
                <Paragraph>
                  Nginx 从 1.13.4 版本开始支持 <Text code>mirror</Text> 指令，可以将请求复制到内部子请求。
                  适合非 Service Mesh 的传统部署架构。
                </Paragraph>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12 }}>
{`location / {
    mirror /mirror;           # 镜像请求
    mirror_request_body on;   # 复制请求体
    proxy_pass http://prod;   # 生产版本
}

location = /mirror {
    internal;                 # 仅内部访问
    proxy_pass http://shadow; # 影子版本
}`}
                </pre>
              </Card>
              <Card size="small" title="方式三：Envoy 流量镜像">
                <Paragraph>
                  在 Envoy 配置中使用 <Text code>request_mirror_policies</Text> 实现流量镜像，
                  适合使用 Envoy 作为 Sidecar 或 Gateway 的场景。
                </Paragraph>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12 }}>
{`routes:
- match:
    prefix: "/"
  route:
    cluster: prod-v1
    request_mirror_policies:
    - cluster: shadow-v2
      runtime_fraction:
        default_value:
          numerator: 100
          denominator: 100   # 100% 镜像`}
                </pre>
              </Card>
            </Space>
          </div>
        ),
      },
      {
        title: '影子实例的副作用处理（数据库写入隔离）',
        content: (
          <div>
            <Paragraph>
              影子部署面临的最大挑战是<Text strong>副作用隔离</Text>。影子实例虽然不返回响应给用户，
              但它会执行与生产实例相同的代码逻辑——包括数据库写入、消息队列发送、第三方 API 调用等。
              如果影子实例的副作用不加以隔离，会导致严重的数据污染问题。
            </Paragraph>
            <Alert
              type="warning"
              showIcon
              title="核心隔离策略"
              description={
                <div>
                  <ul style={{ marginBottom: 0 }}>
                    <li><Text strong>数据库写入隔离：</Text>影子实例使用独立的影子数据库/影子表，或通过中间件拦截写入操作</li>
                    <li><Text strong>消息队列隔离：</Text>影子实例的消息发送到影子 Topic，不污染生产消息队列</li>
                    <li><Text strong>第三方 API 隔离：</Text>影子实例调用第三方 API 的沙箱环境，或在网关层拦截</li>
                    <li><Text strong>缓存隔离：</Text>影子实例使用独立的 Redis 实例或缓存前缀</li>
                    <li><Text strong>日志隔离：</Text>影子实例的日志标记为 shadow 标签，便于过滤和分析</li>
                  </ul>
                </div>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={shadowComparisonData}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li><Text strong>重构验证：</Text>核心服务重构后，在真实流量下验证新旧版本输出一致性</li>
            <li><Text strong>性能对比：</Text>对比新旧版本在相同流量下的延迟、吞吐量、资源消耗</li>
            <li><Text strong>数据库迁移验证：</Text>新数据库方案的查询结果与旧数据库对比</li>
            <li><Text strong>算法升级：</Text>推荐系统、风控系统等需要真实流量验证的场景</li>
            <li><Text strong>中间件升级：</Text>消息队列、缓存等中间件版本升级的兼容性验证</li>
            <li><Text strong>容量规划：</Text>评估新版本在真实负载下的资源需求</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>零风险：</Text>影子实例的任何错误都不会影响用户</li>
            <li><Text strong>真实负载：</Text>在真实流量下测试，比任何压测工具都更准确</li>
            <li><Text strong>功能验证：</Text>可以对比新旧版本的输出一致性</li>
            <li><Text strong>性能基线：</Text>直接对比新旧版本在相同流量下的性能差异</li>
            <li><Text strong>不增加延迟：</Text>镜像请求是异步的，不影响生产响应时间</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>实现复杂：</Text>需要流量镜像能力和副作用隔离</li>
            <li><Text strong>资源消耗：</Text>影子实例需要额外的计算资源</li>
            <li><Text strong>副作用隔离难：</Text>数据库写入、消息发送等副作用需要精心处理</li>
            <li><Text strong>不是部署策略：</Text>影子部署是验证策略，不能直接替代其他部署策略</li>
            <li><Text strong>监控要求高：</Text>需要对比分析两套环境的大量指标</li>
            <li><Text strong>只读验证：</Text>无法验证写操作的最终结果</li>
          </ul>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '影子部署和灰度发布有什么区别？什么时候用影子部署？',
              a: '本质区别：灰度发布是让少量真实用户使用新版本（用户可见），影子部署是新版本在后台处理流量副本（用户不可见）。灰度发布用于降低部署风险，影子部署用于验证新版本在真实流量下的表现。选择标准：如果新版本不确定是否稳定，用灰度发布（小范围验证）；如果新版本需要大规模性能测试，用影子部署（零风险压测）；如果只是重构（功能不变），用影子部署验证输出一致性。',
            },
            {
              q: '影子部署中，如何处理数据库写入等副作用？',
              a: '这是影子部署最核心的工程挑战。方案：1) 影子数据库——为影子实例配置独立的数据库连接，所有写入操作进入影子数据库；2) 写入拦截——在 DAO 层或 ORM 层通过流量标记拦截写入操作，影子流量只读不写；3) 数据库代理——通过数据库代理（如 ProxySQL）根据请求来源路由到不同的数据库实例；4) 事务回滚——影子实例执行写入后自动回滚事务（性能开销大）。最优方案是影子数据库，但需要额外的数据同步机制。',
            },
            {
              q: '影子部署的流量镜像对性能有什么影响？',
              a: '流量镜像的影响主要在两个方面：1) 对生产环境——镜像操作是异步的，理论上不影响生产请求的延迟，但会增加网关/代理的 CPU 和内存消耗；2) 对影子环境——影子实例接收与生产相同的流量，需要足够的资源来处理。如果影子实例资源不足，会导致影子请求排队，间接影响网关性能。建议：镜像流量比例不要超过 100%，影子实例的资源配比与生产实例保持一致，监控网关的资源使用情况。',
            },
            {
              q: '影子部署在微服务架构中如何实现全链路镜像？',
              a: '全链路镜像比单服务镜像复杂得多。需要在请求入口处注入镜像标记（如 HTTP Header x-shadow: true），并在整个调用链中传递这个标记。下游服务收到带镜像标记的请求后，自动将写入操作路由到影子数据库/影子 Topic。Istio 可以通过 Header 传播实现全链路镜像，但需要所有服务都接入 Service Mesh。对于非 Mesh 架构，需要在 RPC 框架层面传递镜像标记，并在各服务的业务代码中处理标记逻辑。',
            },
          ],
        },
      },
    ],
  },
];

/* ============ 新增发布模式 ============ */

export const releaseModeData = [
  /* ======= 常规发布（丰富版） ======= */
  {
    key: 'regular',
    label: '常规发布（Regular Release）',
    icon: MODE_ICONS.regular,
    color: 'blue',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            常规发布是标准的 CI/CD 全流程发布模式。每次发布都经历完整的流水线：<Text strong>代码构建 → 镜像打包 → 制品推送 → 环境部署 → 功能验证</Text>。
            这是最基本、最常用的发布方式，适用于大多数日常版本迭代。
          </Paragraph>
        ),
      },
      {
        title: '架构流程图',
        content: {
          type: 'steps',
          steps: [
            '代码提交触发构建',
            '编译打包生成制品',
            '推送制品到仓库',
            '部署到开发环境',
            '验证开发环境',
            '部署到测试环境',
            '验证测试环境',
            '提交预发审批',
            '部署到预发环境',
            '验证预发环境',
            '灰度发布',
            '全量发布',
            '最终验证',
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={[
              { key: '1', dimension: '构建方式', ec2: '在 CI 服务器上编译打包，生成 tar.gz 制品', k8s: 'Docker Build + Push 到镜像仓库' },
              { key: '2', dimension: '部署方式', ec2: 'SSH 分发制品到各主机，执行部署脚本', k8s: 'kubectl apply 更新 Deployment 镜像版本' },
              { key: '3', dimension: '环境管理', ec2: '手动维护 dev/test/staging/prod 主机列表', k8s: '通过 Namespace 隔离环境，声明式管理' },
              { key: '4', dimension: '验证方式', ec2: '登录各主机检查服务状态和日志', k8s: 'kubectl rollout status + Readiness Probe 自动验证' },
              { key: '5', dimension: '回滚方式', ec2: '重新部署旧版本制品到各主机', k8s: 'kubectl rollout undo 一键回滚' },
            ]}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>日常功能迭代和版本升级</li>
            <li>新功能首次上线</li>
            <li>需要完整验证流程的重要变更</li>
            <li>有充足时间进行完整流水线的情况</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>流程完整：</Text>每个环节都经过验证，质量有保障</li>
            <li><Text strong>可追溯：</Text>全流程有日志和记录，便于审计</li>
            <li><Text strong>风险可控：</Text>逐阶段推进，问题早发现早处理</li>
            <li><Text strong>标准化：</Text>统一的流程规范，团队协作效率高</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>耗时长：</Text>完整流程可能耗时数十分钟到数小时</li>
            <li><Text strong>资源消耗大：</Text>每次都要完整构建和部署</li>
            <li><Text strong>不适合紧急修复：</Text>紧急 Bug 等不及完整流程</li>
          </ul>
        ),
      },
      {
        title: '常见坑与注意事项',
        content: (
          <div>
            <Alert
              type="warning"
              showIcon
              title="常规发布避坑指南"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>坑1：环境差异导致「测试环境正常，生产环境翻车」</Text>——解决方案：使用相同的容器镜像/制品，确保环境一致性</li>
                  <li><Text strong>坑2：审批流程过长导致发布阻塞</Text>——解决方案：区分风险等级，低风险变更简化审批</li>
                  <li><Text strong>坑3：构建产物过期导致回滚失败</Text>——解决方案：建立制品保留策略，至少保留最近 10 个版本的制品</li>
                  <li><Text strong>坑4：多环境部署顺序混乱</Text>——解决方案：严格按 dev→test→staging→prod 顺序推进，不允许跳跃</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '常规发布中，如何保证多环境的一致性？',
              a: '多环境一致性是 CI/CD 的核心挑战。关键措施：1) 使用相同的容器镜像——同一个镜像 tag 在所有环境部署，不允许重新构建；2) 配置外部化——通过 ConfigMap/环境变量注入环境差异，镜像本身不包含环境配置；3) 基础设施即代码——所有环境的基础设施通过 Terraform/Helm 等工具统一管理；4) 不可变基础设施——环境部署后不允许手动修改，任何变更都通过重新部署实现。',
            },
            {
              q: '常规发布的流水线中，哪个阶段最容易出问题？如何应对？',
              a: '最容易出问题的阶段：1) 构建阶段——依赖版本冲突、编译错误，应对：锁定依赖版本、使用缓存加速构建；2) 部署阶段——资源不足、网络问题，应对：设置资源配额、重试机制、超时控制；3) 验证阶段——测试用例不完善导致漏测，应对：完善自动化测试覆盖、设置质量门禁。其中部署阶段的风险最高，因为涉及真实环境操作，需要最完善的容错机制。',
            },
            {
              q: '常规发布如何平衡「速度」和「安全」？',
              a: '平衡策略：1) 分层流水线——快速阶段（构建、单元测试）先行，慢速阶段（集成测试、部署）并行化；2) 风险分级——高风险变更走完整流程，低风险变更可适当加速；3) 增量验证——不是每次都要跑全量测试，根据变更范围选择性执行；4) 缓存机制——复用未变更模块的构建结果，只重新构建变更部分。核心原则：不让安全成为速度的借口，也不让速度牺牲安全。',
            },
            {
              q: '如果常规发布在生产环境部署到一半失败了，怎么办？',
              a: '分情况处理：1) 滚动更新中部分失败——暂停发布，评估影响范围，决定是继续还是回滚；2) 部署脚本执行失败——检查失败原因，如果是环境问题，修复后重试（补偿发布）；3) 新版本启动后崩溃——立即回滚到旧版本，保留现场日志用于排查；4) 数据库迁移失败——这是最严重的情况，需要数据库回滚方案。关键是要有完善的失败处理预案，而不是临场发挥。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 增量发布（丰富版） ======= */
  {
    key: 'incremental',
    label: '增量发布（Incremental Release）',
    icon: MODE_ICONS.incremental,
    color: 'green',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            增量发布是指只部署<Text strong>新增或发生变化</Text>的目标（主机/Pod/服务实例），
            而不影响未变更的实例。它基于当前运行环境，仅对「新增」的组件进行部署，
            适合在已有集群中逐步扩展服务能力。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑',
        content: (
          <Paragraph>
            增量发布的核心是「<Text strong>只部署新目标，跳过已部署目标</Text>」。
            在发布时，系统会对比当前环境的部署状态，识别出尚未部署或需要更新的目标实例，
            仅对这些目标执行部署操作。这大大减少了部署的范围和影响。
          </Paragraph>
        ),
      },
      {
        title: '架构流程图',
        content: {
          type: 'steps',
          steps: [
            '分析当前部署状态',
            '识别未部署目标',
            '筛选差异目标列表',
            '仅对差异目标执行部署',
            '验证新部署目标',
            '更新部署状态记录',
            '完成',
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={[
              { key: '1', dimension: '目标识别', ec2: '对比主机列表和部署记录，找出未部署的主机', k8s: '对比期望副本数和实际副本数，找出未部署的 Pod' },
              { key: '2', dimension: '部署方式', ec2: '仅 SSH 连接到未部署的主机，执行部署脚本', k8s: '调整 Deployment 副本数，K8s 自动创建新 Pod' },
              { key: '3', dimension: '状态追踪', ec2: '在 CMDB 或数据库中记录每台主机的部署状态', k8s: 'K8s 原生追踪 Pod 状态，通过 label 标识部署版本' },
              { key: '4', dimension: '配置管理', ec2: '主机配置可能不一致，需要检查配置差异', k8s: 'Deployment 声明式配置，新 Pod 与旧 Pod 配置一致' },
              { key: '5', dimension: '回滚方式', ec2: '仅需回滚新增主机，已部署主机不受影响', k8s: '缩容新增 Pod 即可，不影响原有 Pod' },
            ]}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>集群扩容时新增节点的部署</li>
            <li>新增服务实例的部署</li>
            <li>部分目标因各种原因未部署，需要补充部署</li>
            <li>在已有集群中逐步添加新功能组件</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>影响范围小：</Text>只操作新增/变更的目标</li>
            <li><Text strong>速度快：</Text>部署范围小，耗时短</li>
            <li><Text strong>风险低：</Text>不影响已有运行中的实例</li>
            <li><Text strong>资源效率高：</Text>避免重复部署已存在的实例</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>依赖已有状态：</Text>需要准确记录当前部署状态</li>
            <li><Text strong>状态不一致风险：</Text>新旧实例可能有差异</li>
            <li><Text strong>不适合大规模变更：</Text>新增内容多时不如常规发布</li>
          </ul>
        ),
      },
      {
        title: '常见坑与注意事项',
        content: (
          <div>
            <Alert
              type="warning"
              showIcon
              title="增量发布避坑指南"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>坑1：状态记录不准确导致漏部署或重复部署</Text>——解决方案：建立可靠的部署状态追踪机制，每次部署后立即更新状态</li>
                  <li><Text strong>坑2：新增实例配置与已有实例不一致</Text>——解决方案：使用统一的配置模板，不允许手动修改实例配置</li>
                  <li><Text strong>坑3：增量部署后出现「新旧实例表现不一致」</Text>——解决方案：确保使用相同的制品版本，定期对比实例配置</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '增量发布如何确定哪些目标是「未部署」的？',
              a: '确定未部署目标的方式：1) 部署状态表——维护一个部署记录表，记录每个目标+版本的部署状态，对比当前版本和已部署版本；2) 实例标签——K8s 中通过 Pod label 标识版本，对比期望版本和实际版本；3) 主机清单——对比 CMDB 中的主机清单和部署记录，找出未部署的主机。需要处理边界情况：目标存在但版本不一致（需要更新）、目标不存在（需要新增）、目标多余（需要清理）。',
            },
            {
              q: '增量发布和补偿发布有什么区别？',
              a: '核心区别：增量发布针对「新增」目标（之前不存在或未部署），补偿发布针对「失败」目标（上次部署失败）。增量发现的场景是集群扩容、新服务上线；补偿发现的场景是部分节点部署失败需要重试。两者可以结合使用——先增量发布新增目标，再补偿发布失败目标。',
            },
            {
              q: '增量发布中，如果新增目标部署成功后，发现版本与已有目标不一致怎么办？',
              a: '这通常是因为部署状态记录不准确导致的。应对：1) 部署前先做版本一致性检查——对比新增目标的版本和已有目标的版本；2) 如果发现不一致，提示用户确认——是故意使用不同版本还是需要统一；3) 提供「同步」功能——将已有目标也更新到相同版本。预防措施：部署时记录完整的版本信息，建立版本一致性的监控告警。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 补偿发布（丰富版） ======= */
  {
    key: 'compensation',
    label: '补偿发布（Compensation Release）',
    icon: MODE_ICONS.compensation,
    color: 'orange',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            补偿发布是指在上一次发布中，部分目标部署<Text strong>失败或未完成</Text>的情况下，
            仅针对这些<Text strong>失败的目标</Text>进行重新部署。它类似于「补考」机制，
            只处理上次遗留下来的问题，不重新部署已成功的实例。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑',
        content: (
          <Paragraph>
            补偿发布需要结合<Text strong>部署状态记录</Text>来使用。系统会记录每次发布中每个目标的部署结果（成功/失败），
            当整体发布因部分目标失败而终止时，可以选择「补偿发布」模式，
            系统自动筛选出失败的目标列表，仅对这些目标重新执行部署。
          </Paragraph>
        ),
      },
      {
        title: '架构流程图',
        content: {
          type: 'steps',
          steps: [
            '分析上次发布结果',
            '筛选失败目标列表',
            '分析失败原因',
            '（可选）修复环境问题',
            '仅对失败目标执行部署',
            '验证部署结果',
            '更新部署状态',
            '完成',
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={[
              { key: '1', dimension: '失败识别', ec2: '检查每台主机的部署日志，识别失败的主机', k8s: '检查 Pod 状态，识别未成功创建或启动的 Pod' },
              { key: '2', dimension: '重试策略', ec2: '重新 SSH 连接失败主机，执行部署脚本', k8s: '删除失败 Pod，K8s 自动重建；或调整 Deployment 触发重新调度' },
              { key: '3', dimension: '失败原因', ec2: '网络超时、磁盘空间不足、权限问题、依赖缺失', k8s: '镜像拉取失败、资源不足、健康检查失败、节点不可调度' },
              { key: '4', dimension: '重试限制', ec2: '需手动设置重试次数和间隔，避免无限重试', k8s: '通过 backoffLimit 和 restartPolicy 控制重试行为' },
              { key: '5', dimension: '状态追踪', ec2: '记录每次重试的结果，累计失败次数', k8s: 'K8s Events 记录 Pod 创建失败原因，kubectl describe 查看详情' },
            ]}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>大规模发布中部分节点部署失败</li>
            <li>网络抖动或临时故障导致的部署失败</li>
            <li>资源不足导致部分实例未能启动</li>
            <li>依赖服务暂时不可用导致部分部署失败</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>精准修复：</Text>只处理失败目标，效率高</li>
            <li><Text strong>避免重复：</Text>不重复部署已成功的实例</li>
            <li><Text strong>节省时间：</Text>比重新执行完整发布快得多</li>
            <li><Text strong>降低风险：</Text>不影响已成功运行的实例</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>依赖准确的状态记录：</Text>需要可靠的部署状态追踪</li>
            <li><Text strong>可能忽略根因：</Text>如果失败是环境问题，补偿发布可能再次失败</li>
            <li><Text strong>需要手动分析失败原因：</Text>不能盲目补偿</li>
          </ul>
        ),
      },
      {
        title: '常见坑与注意事项',
        content: (
          <div>
            <Alert
              type="warning"
              showIcon
              title="补偿发布避坑指南"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>坑1：盲目重试导致反复失败</Text>——解决方案：先分析失败原因，如果是环境问题（如磁盘满），修复后再补偿</li>
                  <li><Text strong>坑2：补偿发布成功后，出现「部分实例版本不一致」</Text>——解决方案：补偿发布使用与上次发布相同的制品版本，确保一致性</li>
                  <li><Text strong>坑3：多次补偿发布导致状态混乱</Text>——解决方案：设置最大补偿次数，超过后要求走完整发布流程</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '补偿发布和自动重试有什么区别？各自适用什么场景？',
              a: '自动重试是发布流程中的自动化机制——在发布过程中遇到瞬时失败（如网络超时）时自动重试，不需要人工介入。补偿发布是人工触发的模式——当发布因部分目标失败而终止后，运维人员分析失败原因后，选择补偿发布模式重新处理失败目标。自动重试适合瞬时故障，补偿发布适合需要人工分析的故障。两者可以结合：先自动重试 N 次，失败后再走补偿发布流程。',
            },
            {
              q: '补偿发布中，如何避免重复修复已修复的问题？',
              a: '关键是维护准确的部署状态记录。每次部署操作后，立即更新目标的状态（成功/失败/进行中）。补偿发布时，只处理状态为「失败」的目标。需要注意：1) 状态更新必须是原子操作，避免并发问题；2) 如果目标在补偿前已被手动修复，需要同步更新状态；3) 提供「状态刷新」功能，让用户手动检查并更新目标的实际状态。',
            },
            {
              q: '补偿发布失败后，下一步应该怎么办？',
              a: '如果补偿发布仍然失败，说明问题不是瞬时的，需要深入排查：1) 检查失败原因是否与上次相同——如果相同，说明根因未解决，需要先修复环境问题；2) 考虑是否走完整发布——如果失败目标与成功目标存在版本差异风险，建议走完整发布确保一致性；3) 升级处理——如果多次补偿失败，应升级到人工处理，避免自动化流程陷入死循环。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 快速发布（丰富版） ======= */
  {
    key: 'quick',
    label: '快速发布（Quick Release）',
    icon: MODE_ICONS.quick,
    color: 'purple',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            快速发布是<Text strong>跳过构建阶段</Text>，直接复用上一次成功的构建产物进行部署的发布模式。
            它适用于一些紧急的配置变更、环境参数调整，或者代码未变仅需要重新部署的场景。
            快速发布的核心思想是「<Text strong>构建结果不变，只做部署调整</Text>」。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑',
        content: (
          <Paragraph>
            快速发布模式下，系统会<Text strong>自动复用最近一次成功的构建产物</Text>（镜像/制品），
            跳过构建阶段的等待时间，直接进入部署阶段。这通常需要满足以下条件：
            <ul>
              <li>代码未发生变更，或变更仅涉及配置</li>
              <li>最近一次构建产物仍然可用（未被清理）</li>
              <li>部署环境的基础设施未发生变化</li>
            </ul>
          </Paragraph>
        ),
      },
      {
        title: '架构流程图',
        content: {
          type: 'steps',
          steps: [
            '检查构建产物可用性',
            '查找最近成功构建',
            '复用制品/镜像',
            '跳过构建阶段',
            '直接进入部署阶段',
            '部署到目标环境',
            '验证部署结果',
            '完成',
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={[
              { key: '1', dimension: '产物复用', ec2: '从制品仓库下载最近成功的 tar.gz 包', k8s: '直接使用镜像仓库中已有的镜像 tag' },
              { key: '2', dimension: '构建跳过', ec2: '跳过编译和打包步骤，直接使用已构建的制品', k8s: '跳过 docker build 和 push，直接使用已存在的镜像' },
              { key: '3', dimension: '部署方式', ec2: 'SSH 分发已有制品到目标主机，执行部署脚本', k8s: 'kubectl set image 更新 Deployment 镜像版本' },
              { key: '4', dimension: '产物验证', ec2: '验证制品完整性（MD5/SHA256），确保未被篡改', k8s: '验证镜像 digest，确保与上次部署的镜像一致' },
              { key: '5', dimension: '安全保障', ec2: '需要确认制品来源可靠，未被中间人篡改', k8s: '镜像签名验证（如 Notary/Cosign），确保镜像来源可信' },
            ]}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>紧急 Bug 修复，需要快速上线</li>
            <li>配置变更或环境参数调整</li>
            <li>服务重启或重新调度</li>
            <li>扩缩容后需要重新部署</li>
            <li>上一次发布仅部署失败，构建已成功</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>速度极快：</Text>跳过构建，直接部署</li>
            <li><Text strong>资源节省：</Text>不需要重新编译和打包</li>
            <li><Text strong>适合紧急情况：</Text>快速响应线上问题</li>
            <li><Text strong>产物一致：</Text>复用已验证的构建产物</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>依赖历史产物：</Text>如果产物被清理则无法使用</li>
            <li><Text strong>不适用于代码变更：</Text>代码变更必须走完整构建</li>
            <li><Text strong>可能跳过必要的验证：</Text>不适合重大变更</li>
          </ul>
        ),
      },
      {
        title: '常见坑与注意事项',
        content: (
          <div>
            <Alert
              type="warning"
              showIcon
              title="快速发布避坑指南"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>坑1：构建产物被清理导致快速发布失败</Text>——解决方案：建立制品保留策略，快速发布依赖的产物至少保留 7 天</li>
                  <li><Text strong>坑2：复用了错误版本的构建产物</Text>——解决方案：严格校验产物版本，必须与发布单指定的版本一致</li>
                  <li><Text strong>坑3：快速发布后忘记更新版本记录</Text>——解决方案：快速发布也要记录完整的发布日志，不因快速而省略</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '快速发布和常规发布在安全方面有什么区别？如何保证快速发布的安全性？',
              a: '快速发布跳过了构建阶段，因此也跳过了构建阶段的安全检查（如 SAST、依赖扫描）。安全措施：1) 只允许复用经过安全扫描的构建产物，不能复用未扫描的产物；2) 产物签名验证——确保复用的产物未被篡改；3) 限制快速发布的使用范围——仅允许对特定环境、特定应用使用；4) 审计日志——快速发布必须记录详细的审计日志，方便事后追溯。',
            },
            {
              q: '快速发布中，如何确保复用的产物是最新且正确的？',
              a: '确保产物正确性的机制：1) 产物版本关联——构建产物与代码版本（Git commit SHA）绑定，快速发布时校验版本匹配；2) 产物完整性校验——通过 MD5/SHA256 校验产物完整性；3) 产物元数据——记录构建时间、构建者、构建环境等信息，快速发布前验证元数据；4) 最新产物查找——按时间倒序查找最近成功的产物，排除标记为「不可用」的产物。',
            },
            {
              q: '什么情况下不应该使用快速发布？',
              a: '不应使用快速发布的场景：1) 代码发生了变更——快速发布的核心前提是「代码未变」，代码变了必须走完整构建；2) 构建产物已被标记为「不安全」——如发现了安全漏洞；3) 上次构建产物已过期——如超过保留期限；4) 部署环境发生重大变化——如基础设施升级、依赖版本变更，需要重新构建以适配新环境；5) 合规要求——某些行业合规要求每次发布都必须有完整的构建记录。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 回滚发布（丰富版） ======= */
  {
    key: 'rollback',
    label: '回滚发布（Rollback Release）',
    icon: MODE_ICONS.rollback,
    color: 'red',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            回滚发布是指将服务<Text strong>恢复到上一个稳定版本</Text>的发布模式。
            当新版本发布后出现严重问题（如功能异常、性能下降、兼容性问题等），
            需要立即恢复到之前的版本以保证服务可用性。回滚发布是发布系统的<Text strong>最后一道安全防线</Text>。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑',
        content: (
          <Paragraph>
            回滚发布的核心机制：
            <ul>
              <li>每个发布单都记录了<Text strong>回滚来源（rollback_from）</Text>，形成版本链</li>
              <li>回滚时，系统自动获取目标版本的构建产物/镜像</li>
              <li>使用上一次成功的部署配置重新部署</li>
              <li>可以根据部署模式选择不同的回滚策略：
                <ul>
                  <li><Text strong>K8s 模式：</Text>通过修改 Deployment 镜像版本触发滚动更新</li>
                  <li><Text strong>EC2 模式：</Text>重新部署旧版本产物到目标主机</li>
                </ul>
              </li>
            </ul>
          </Paragraph>
        ),
      },
      {
        title: '架构流程图',
        content: {
          type: 'steps',
          steps: [
            '触发回滚',
            '确定回滚目标版本',
            '获取回滚版本制品',
            '验证制品可用性',
            '执行回滚部署',
            '验证回滚结果',
            '记录回滚日志',
            '通知相关人员',
          ],
        },
      },
      {
        title: '回滚策略对比',
        content: {
          type: 'table',
          columns: ['策略', '描述', '适用场景', '影响'],
          rows: [
            ['立即回滚', '直接恢复到上一个版本', '严重故障，服务不可用', '全部实例同时切换'],
            ['逐步回滚', '按批次逐步回滚', '部分功能异常，非致命', '逐步减少影响'],
            ['金丝雀回滚', '先回滚少量实例验证', '不确定回滚是否有效', '先验证再全量'],
            ['版本偏移', '回滚到指定版本（非上一个）', '多个版本后发现更早版本更稳定', '跳过中间版本'],
          ],
        },
      },
      {
        title: 'EC2 vs K8s 实现对比',
        content: (
          <Table
            dataSource={[
              { key: '1', dimension: '回滚机制', ec2: '重新部署旧版本制品到目标主机，需完整部署流程', k8s: 'kubectl rollout undo 基于 ReplicaSet 历史版本回滚' },
              { key: '2', dimension: '回滚速度', ec2: '取决于制品分发速度和主机数量，通常分钟级', k8s: '秒级到分钟级，取决于滚动更新速率和副本数' },
              { key: '3', dimension: '版本管理', ec2: '需要自行维护制品版本历史，确保旧版本制品可用', k8s: 'K8s 自动保留 ReplicaSet 历史，通过 revisionHistoryLimit 控制保留数量' },
              { key: '4', dimension: '数据库回滚', ec2: '需要手动执行数据库回滚脚本', k8s: '与 EC2 相同，数据库回滚需要独立处理' },
              { key: '5', dimension: '回滚验证', ec2: '登录主机检查服务版本和运行状态', k8s: 'kubectl rollout status 自动追踪回滚进度' },
            ]}
            columns={ec2VsK8sColumns}
            pagination={false}
            size="small"
            bordered
          />
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li>新版本发布后出现严重 Bug</li>
            <li>性能退化或资源泄露</li>
            <li>数据库兼容性问题</li>
            <li>依赖服务不兼容</li>
            <li>功能异常影响用户体验</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>快速恢复：</Text>最大限度地减少故障时间</li>
            <li><Text strong>安全可靠：</Text>使用已验证的旧版本，风险低</li>
            <li><Text strong>自动化：</Text>系统自动处理回滚流程</li>
            <li><Text strong>版本可追溯：</Text>完整记录版本变更历史</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>数据兼容性问题：</Text>回滚后新数据结构可能不兼容</li>
            <li><Text strong>功能回退：</Text>用户会失去新版本的功能</li>
            <li><Text strong>依赖回滚链：</Text>多次回滚后版本链可能复杂</li>
            <li><Text strong>不是万能药：</Text>某些问题（如数据损坏）回滚无法解决</li>
          </ul>
        ),
      },
      {
        title: '常见坑与注意事项',
        content: (
          <div>
            <Alert
              type="warning"
              showIcon
              title="回滚发布避坑指南"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>坑1：回滚成功但数据不一致</Text>——最危险的坑！新版本写入的数据格式旧版本无法解析。解决方案：设计时考虑向前兼容，必要时执行数据修复脚本</li>
                  <li><Text strong>坑2：回滚版本不存在</Text>——旧版本制品被清理。解决方案：保留至少 10 个历史版本的制品，回滚版本的制品永久保留</li>
                  <li><Text strong>坑3：回滚后问题依然存在</Text>——说明问题不在代码版本，而在环境或数据。解决方案：回滚的同时排查根因</li>
                  <li><Text strong>坑4：多次回滚导致版本链混乱</Text>——A→B→A→C→A，不知道当前运行的到底是哪个版本。解决方案：每次回滚都记录完整的版本链，提供版本可视化</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '回滚发布中最危险的问题是什么？如何预防？',
              a: '最危险的是数据兼容性问题——新版本运行期间产生了新格式的数据，回滚后旧版本无法处理。预防措施：1) 设计阶段就考虑向前兼容，新字段必须有默认值；2) 数据库 Schema 变更分阶段进行——先加字段（兼容旧代码），再部署新代码，最后清理旧字段；3) 回滚后执行数据修复脚本——将新格式数据转换为旧格式；4) 限制新版本运行时间——尽快发现问题并回滚，减少数据不一致的窗口。',
            },
            {
              q: 'K8s 中 kubectl rollout undo 的原理是什么？',
              a: 'K8s Deployment 每次更新都会创建新的 ReplicaSet，并保留旧 ReplicaSet 的历史记录。kubectl rollout undo 的工作原理：1) 查找当前 Deployment 的上一个 ReplicaSet（通过 revision 编号）；2) 将 Deployment 的 Pod Template 回滚到上一个 ReplicaSet 的模板；3) 触发新的滚动更新，将 Pod 从当前版本逐步替换为回滚版本。K8s 通过 revisionHistoryLimit（默认 10）控制保留的历史 ReplicaSet 数量。',
            },
            {
              q: '回滚发布和「重新部署旧版本」有什么区别？',
              a: '回滚发布是一个有状态的、可追溯的流程：1) 记录回滚来源——rollback_from 字段记录回滚目标版本，形成版本链；2) 审计日志——回滚操作被记录为一次独立的发布，包含操作人、时间、原因；3) 自动关联——回滚发布自动关联到原始发布，方便追溯问题。而「重新部署旧版本」只是手动选择旧版本制品重新部署，缺少上述的追溯和关联能力。',
            },
            {
              q: '如果回滚发布本身也失败了怎么办？',
              a: '这是最糟糕的情况——「回滚失败」。应急预案：1) 保留多版本制品——长期保留至少 3 个稳定版本的制品，确保总有可回滚的版本；2) 备份当前配置——回滚前备份当前部署配置，失败后可恢复；3) 手动干预——如果自动化回滚失败，需要运维人员手动恢复；4) 蓝绿部署的蓝环境——如果使用蓝绿部署，旧环境仍然保留，可以不依赖回滚流程直接切换。预防重于治疗——定期演练回滚流程，确保自动化回滚的可靠性。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 紧急发布（新增） ======= */
  {
    key: 'emergency',
    label: '紧急发布 / Hotfix（Emergency Release）',
    icon: MODE_ICONS.emergency,
    color: 'red',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            紧急发布（Emergency Release / Hotfix）是一种<Text strong>跳过常规审批流程</Text>、
            快速将修复版本部署到生产环境的发布模式。当线上出现严重故障（如安全漏洞、服务不可用、
            数据损坏等），常规发布流程的审批和验证环节会延误修复时间，此时需要紧急发布来
            <Text strong>以最快速度恢复服务</Text>。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑（紧急通道机制）',
        content: (
          <Paragraph>
            紧急发布的核心是<Text strong>「紧急通道」</Text>机制：
            <ul>
              <li><Text strong>简化审批：</Text>将多级审批简化为单人审批或自动审批</li>
              <li><Text strong>跳过非关键阶段：</Text>跳过部分测试阶段，直接部署到生产</li>
              <li><Text strong>并行处理：</Text>构建和审批并行进行，减少等待时间</li>
              <li><Text strong>事后补流程：</Text>紧急发布后需要补充完整的变更记录和审批</li>
              <li><Text strong>自动回滚保障：</Text>紧急发布必须配置自动回滚条件，一旦异常立即回滚</li>
            </ul>
          </Paragraph>
        ),
      },
      {
        title: '流程图',
        content: {
          type: 'steps',
          steps: [
            '发现紧急问题',
            '快速修复代码',
            '提交紧急发布申请',
            '简化审批（单人/自动）',
            '快速构建',
            '跳过部分测试',
            '直接部署生产',
            '监控 + 自动回滚',
            '事后补流程',
          ],
        },
      },
      {
        title: '与常规发布的差异对比表',
        content: {
          type: 'table',
          columns: ['对比维度', '常规发布', '紧急发布'],
          rows: [
            ['审批流程', '多级审批（AppOwner → 运维 → 安全）', '简化审批（单人审批或自动通过）'],
            ['构建流程', '完整 CI 流水线', '最小化构建，仅编译必要模块'],
            ['测试阶段', '单元测试 → 集成测试 → 预发验证', '跳过非关键测试，仅保留冒烟测试'],
            ['部署策略', '按既定策略（滚动/蓝绿/灰度）', '选择最快策略（通常为滚动更新）'],
            ['发布耗时', '30分钟 - 数小时', '5-15分钟'],
            ['事后要求', '无额外要求', '需补充完整变更记录和审批流程'],
            ['适用场景', '日常迭代', '线上故障、安全漏洞'],
            ['风险等级', '低', '中高'],
            ['回滚配置', '可选', '必须配置自动回滚条件'],
          ],
        },
      },
      {
        title: '审批简化策略',
        content: (
          <div>
            <Paragraph>
              紧急发布的审批简化不是「不审批」，而是<Text strong>「高效审批」</Text>：
            </Paragraph>
            <Alert
              type="info"
              showIcon
              title="紧急发布审批策略"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>单人审批：</Text>将多级审批压缩为一级，由值班负责人审批</li>
                  <li><Text strong>自动审批：</Text>对于已定义的紧急修复模板（如回滚到已知版本），自动通过</li>
                  <li><Text strong>事后审批：</Text>先发布后审批，但必须在 24 小时内补充完整审批记录</li>
                  <li><Text strong>审批通知：</Text>紧急发布自动通知所有相关方，即使审批已简化</li>
                  <li><Text strong>审批记录：</Text>所有操作（包括自动审批）都记录在审计日志中</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li><Text strong>安全漏洞修复：</Text>如 CVE 漏洞需要立即修复</li>
            <li><Text strong>服务不可用：</Text>线上服务大面积故障，需要紧急恢复</li>
            <li><Text strong>数据损坏修复：</Text>数据问题导致业务无法正常运作</li>
            <li><Text strong>关键功能异常：</Text>核心功能（如支付、登录）不可用</li>
            <li><Text strong>合规紧急变更：</Text>法律法规要求的紧急变更</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>速度快：</Text>最大限度缩短修复时间，减少故障影响</li>
            <li><Text strong>流程简化：</Text>减少审批和测试环节，集中精力修复问题</li>
            <li><Text strong>自动回滚：</Text>内置自动回滚机制，降低紧急发布的风险</li>
            <li><Text strong>可追溯：</Text>事后补流程确保合规性</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>风险较高：</Text>跳过测试和审批可能导致新问题</li>
            <li><Text strong>可能引入新 Bug：</Text>快速修复可能在压力下引入新缺陷</li>
            <li><Text strong>流程绕过风险：</Text>可能被滥用，将非紧急发布包装为紧急发布</li>
            <li><Text strong>事后成本：</Text>需要补充文档和审批，增加后续工作量</li>
          </ul>
        ),
      },
      {
        title: '安全风险与防范',
        content: (
          <div>
            <Alert
              type="error"
              showIcon
              title="紧急发布安全风险"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><Text strong>风险1：恶意利用紧急通道</Text>——防范：限制紧急发布的使用频率，异常高频触发告警</li>
                  <li><Text strong>风险2：修复引入新漏洞</Text>——防范：紧急发布后自动触发安全扫描，发现问题立即告警</li>
                  <li><Text strong>风险3：审批绕过导致合规问题</Text>——防范：事后审批必须在 24 小时内完成，超时自动通知管理层</li>
                  <li><Text strong>风险4：紧急发布后无人跟进</Text>——防范：紧急发布自动创建后续任务，跟踪补充流程完成情况</li>
                </ul>
              }
              style={{ marginBottom: 12 }}
            />
          </div>
        ),
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '紧急发布如何平衡「速度」和「安全」？',
              a: '平衡策略：1) 分层紧急——根据故障等级定义不同的紧急发布策略（P0 全自动、P1 单人审批、P2 简化审批）；2) 自动回滚——紧急发布必须配置自动回滚条件，一旦指标异常自动回滚；3) 灰度紧急——即使是紧急发布，也可以先部署 1 个实例验证，再全量；4) 事后审计——紧急发布后强制补充完整流程，确保合规。核心原则：快但不乱，急但不慌。',
            },
            {
              q: '紧急发布的审批简化会不会被滥用？如何防止？',
              a: '防止滥用措施：1) 频率限制——每个应用每周紧急发布次数限制（如不超过 3 次），超过需要高级审批；2) 事后审计——紧急发布后 24 小时内必须补充完整审批，否则标记为违规；3) 自动告警——紧急发布自动通知管理层，增加滥用成本；4) 原因分析——统计紧急发布的原因，如果同一类问题反复出现，说明常规流程有问题；5) 定期回顾——每月回顾紧急发布记录，评估是否有可以避免的紧急发布。',
            },
            {
              q: '紧急发布中，如何确保回滚的可靠性？',
              a: '紧急发布必须配置自动回滚：1) 回滚条件——定义明确的自动回滚触发条件（如错误率大于 5%、延迟大于 2x）；2) 回滚预案——紧急发布前先确认回滚路径（制品可用、配置正确）；3) 回滚演练——定期演练紧急发布和回滚流程；4) 监控覆盖——确保紧急发布的目标服务有完善的监控；5) 回滚自动化——一键回滚或自动回滚，不需要人工操作。如果回滚也失败，需要立即升级到人工处理。',
            },
            {
              q: '什么时候应该使用紧急发布而不是常规发布？',
              a: '使用紧急发布的判断标准：1) 故障影响范围——影响超过 50% 用户或核心功能不可用；2) 故障持续时间——预计常规发布流程的延迟会导致超过 SLA 的停机时间；3) 安全风险——存在可利用的安全漏洞，需要立即修复；4) 业务损失——每延迟一分钟都会造成显著的业务损失。如果不满足以上条件，应该走常规发布流程。紧急发布是「救火」工具，不是「加速」工具。',
            },
          ],
        },
      },
    ],
  },
  /* ======= 定时发布（新增） ======= */
  {
    key: 'scheduled',
    label: '定时发布（Scheduled Release）',
    icon: MODE_ICONS.scheduled,
    color: 'cyan',
    sections: [
      {
        title: '概念',
        content: (
          <Paragraph>
            定时发布（Scheduled Release）是一种<Text strong>预先设定发布时间</Text>，
            由系统在指定时间<Text strong>自动触发</Text>发布流程的模式。发布内容（构建产物、部署配置）
            可以提前准备好，到时间后系统自动执行。这种方式适用于<Text strong>需要在特定时间窗口发布</Text>的场景，
            如业务低峰期、维护窗口期、或与外部系统协调的发布时间。
          </Paragraph>
        ),
      },
      {
        title: '核心逻辑',
        content: (
          <Paragraph>
            定时发布的核心机制：
            <ul>
              <li><Text strong>提前准备：</Text>在发布窗口前完成构建、测试、审批等所有准备工作</li>
              <li><Text strong>定时触发：</Text>系统在指定时间自动发起发布流程</li>
              <li><Text strong>时间窗口：</Text>支持定义发布时间窗口（如 02:00-04:00），在窗口内自动执行</li>
              <li><Text strong>前置检查：</Text>触发前自动检查前置条件（如构建产物可用、目标环境正常）</li>
              <li><Text strong>失败处理：</Text>如果前置条件不满足或执行失败，自动取消并通知发布者</li>
            </ul>
          </Paragraph>
        ),
      },
      {
        title: '实现方式',
        content: (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small" title="方式一：Cron 定时任务">
                <Paragraph>
                  通过系统的 Cron 调度器定时触发发布任务。适用于简单的定时发布需求。
                </Paragraph>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12 }}>
{`# 每天凌晨 2:00 执行发布
0 2 * * * /usr/local/bin/release --app=my-app --env=prod --version=v2.1.0`}
                </pre>
              </Card>
              <Card size="small" title="方式二：CI/CD 平台的 Scheduled Pipeline">
                <Paragraph>
                  使用 GitLab CI、Jenkins 等 CI/CD 平台的定时触发功能，在指定时间触发完整的发布流水线。
                </Paragraph>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12 }}>
{`# GitLab CI Scheduled Pipeline 示例
# 可在 GitLab UI 中配置 Cron 表达式
# 或通过 API 创建 Scheduled Pipeline`}
                </pre>
              </Card>
              <Card size="small" title="方式三：发布系统的定时任务模块">
                <Paragraph>
                  在发布系统内部实现定时任务管理模块，支持创建、编辑、暂停、删除定时发布任务。
                  提供可视化的定时任务管理界面。
                </Paragraph>
              </Card>
            </Space>
          </div>
        ),
      },
      {
        title: '适用场景',
        content: (
          <ul>
            <li><Text strong>业务低峰期发布：</Text>在凌晨或周末等业务低峰期自动发布</li>
            <li><Text strong>维护窗口期：</Text>在预定的维护窗口内自动执行发布</li>
            <li><Text strong>跨团队协调：</Text>与外部系统约定的发布时间</li>
            <li><Text strong>定期更新：</Text>如每周安全补丁的自动发布</li>
            <li><Text strong>减少人工操作：</Text>避免运维人员深夜值班发布</li>
          </ul>
        ),
      },
      {
        title: '优点',
        content: (
          <ul>
            <li><Text strong>减少人工成本：</Text>不需要运维人员深夜值班</li>
            <li><Text strong>时间精准：</Text>在指定时间准时执行，不会延误</li>
            <li><Text strong>提前准备：</Text>有充足时间准备发布内容，减少临时问题</li>
            <li><Text strong>可计划：</Text>发布计划透明，团队可以提前协调</li>
            <li><Text strong>降低风险：</Text>在低峰期发布，影响范围最小</li>
          </ul>
        ),
      },
      {
        title: '缺点',
        content: (
          <ul>
            <li><Text strong>缺乏灵活性：</Text>如果发布前发现问题，需要手动取消</li>
            <li><Text strong>问题响应慢：</Text>深夜自动发布出现问题，可能需要叫醒运维人员</li>
            <li><Text strong>前置依赖：</Text>需要确保发布前所有准备工作已完成</li>
            <li><Text strong>不适合紧急修复：</Text>紧急问题不能等定时发布</li>
            <li><Text strong>需要监控覆盖：</Text>自动发布必须有完善的监控和告警</li>
          </ul>
        ),
      },
      {
        title: '与常规发布的对比',
        content: {
          type: 'table',
          columns: ['对比维度', '常规发布', '定时发布'],
          rows: [
            ['触发方式', '人工触发', '系统定时自动触发'],
            ['发布时间', '即时', '预设时间点'],
            ['准备工作', '发布前准备', '提前完成所有准备'],
            ['人工参与', '需要人工操作', '无需人工（发布时）'],
            ['适用时间', '工作时间', '任意时间（含深夜）'],
            ['失败处理', '人工处理', '自动通知 + 人工介入'],
            ['灵活性', '高（随时可调整）', '低（需提前设定）'],
            ['风险', '有人值守，快速响应', '无人值守，响应可能延迟'],
          ],
        },
      },
      {
        title: '面试重点',
        content: {
          type: 'interview',
          items: [
            {
              q: '定时发布和 CI/CD 的 Scheduled Pipeline 有什么区别？',
              a: '区别在于范围和目的：1) 定时发布是发布系统内部的定时执行能力，专注于部署环节；Scheduled Pipeline 是 CI/CD 平台的定时触发能力，覆盖从构建到部署的完整流程；2) 定时发布通常已经完成了构建，只是在等待部署窗口；Scheduled Pipeline 从构建开始，整个流程都定时触发；3) 定时发布更适合「已准备好，等待窗口」的场景，Scheduled Pipeline 更适合「定期自动构建+部署」的场景。',
            },
            {
              q: '定时发布中，如果发布失败怎么办？',
              a: '定时发布失败的处理策略：1) 自动回滚——如果配置了自动回滚，失败后自动回滚到旧版本；2) 自动通知——通过短信、电话、IM 等方式通知值班人员；3) 自动取消——如果前置条件不满足（如构建产物未就绪），自动取消发布并通知；4) 升级策略——如果无人响应，自动升级到更高级别的通知方式（如电话通知）；5) 事后分析——发布失败后自动生成故障报告。',
            },
            {
              q: '如何设计一个可靠的定时发布系统？',
              a: '设计要点：1) 任务持久化——定时任务存储在数据库中，系统重启不丢失；2) 分布式调度——支持多节点部署，通过分布式锁避免重复执行；3) 前置检查——发布前自动检查所有前置条件，不满足则取消；4) 时间窗口——支持定义发布时间窗口，窗口内自动重试；5) 失败重试——在窗口内支持自动重试，但需设置最大重试次数；6) 监控告警——发布过程全链路监控，异常实时告警；7) 手动干预——支持在发布过程中手动暂停或取消。',
            },
          ],
        },
      },
    ],
  },
];

/* ============ Demo 实现对比 Tab 数据 ============ */

export const demoComparisonData = {
  overall: {
    title: '总体架构对比',
    icon: <ApartmentOutlined />,
    sections: [
      {
        title: '真实 Spug vs Demo 系统对比',
        content: {
          type: 'table',
          columns: ['对比维度', '真实 Spug 系统', '本 Demo 系统'],
          rows: [
            ['技术栈', 'Python (Django) + React', 'Python (Django REST Framework) + React + TypeScript'],
            ['部署方式', '主机 Agent 模式（SSH）', '支持 EC2（SSH）和 K8s（kubectl）双模式'],
            ['发布能力', '5 种发布模式', '7 种发布模式（含紧急发布、定时发布）'],
            ['部署策略', '基本滚动更新', '6 种部署策略（滚动/蓝绿/灰度/重建/红黑/影子）'],
            ['K8s 支持', '不支持原生 K8s 集成', '支持 K8s 原生操作（通过 k8s_client）'],
            ['审批流程', '基本审批', '多级审批 + 紧急通道 + 定时发布'],
            ['面试学习', '运维实践', '系统设计 + 部署策略 + 面试指南'],
            ['定位', '生产级运维工具', '教学演示 + 面试准备系统'],
          ],
        },
      },
    ],
  },
  strategy: {
    title: '部署策略实现对比',
    icon: <SafetyOutlined />,
    sections: [
      {
        title: '部署策略实现对比',
        content: {
          type: 'table',
          columns: ['功能', '真实实现', 'Demo 实现', '差异等级'],
          rows: [
            ['滚动更新', 'K8s Deployment Controller 自动滚动', '通过 k8s_client 真实操作（需 kind 集群）/ 模拟降级', '可真实'],
            ['蓝绿部署', '两套 Service + Deployment 切换', '仅模拟返回', '仅模拟'],
            ['灰度发布', 'Istio 权重路由 / 副本数比例', '仅模拟返回', '仅模拟'],
            ['重建部署', '先缩容到 0 再扩容新版本', '未实现', '未实现'],
            ['红黑部署', '创建新环境 → 切换 → 销毁旧环境', '未实现', '未实现'],
            ['影子部署', 'Istio Traffic Mirroring', '未实现', '未实现'],
          ],
        },
      },
    ],
  },
  mode: {
    title: '发布模式实现对比',
    icon: <ExperimentOutlined />,
    sections: [
      {
        title: '发布模式实现对比',
        content: {
          type: 'table',
          columns: ['模式', '真实实现', 'Demo 实现', '差异等级'],
          rows: [
            ['常规发布', '完整 CI/CD 流水线', '11 阶段任务存在但执行简化', '流程简化'],
            ['增量发布', '检测未部署目标，仅部署新目标', 'release_mode 字段存在但逻辑未实现', '逻辑未实现'],
            ['补偿发布', '筛选失败目标，仅重试失败目标', '同上', '逻辑未实现'],
            ['快速发布', '复用最近构建产物，跳过构建', '同上', '逻辑未实现'],
            ['回滚发布', '恢复历史版本产物', '有 rollback API 但逻辑简化', '部分实现'],
            ['紧急发布', '跳过审批、快速构建', '未实现', '未实现'],
            ['定时发布', 'Cron 定时触发发布', '未实现', '未实现'],
          ],
        },
      },
    ],
  },
  pipeline: {
    title: '流水线各阶段模拟说明',
    icon: <BuildOutlined />,
    sections: [
      {
        title: '11 阶段模拟说明',
        content: (
          <div>
            <Paragraph>
              发布流水线共 11 个阶段，各阶段在 Demo 系统中的实现程度不同：
            </Paragraph>
            <Table
              dataSource={[
                { key: '1', stage: '代码提交', real: 'Git Webhook 触发', demo: '模拟 Git 提交事件', level: '模拟', levelColor: 'orange' },
                { key: '2', stage: '代码审查', real: 'Code Review + CI 检查', demo: '模拟审查通过', level: '模拟', levelColor: 'orange' },
                { key: '3', stage: '构建编译', real: 'Docker Build / 编译打包', demo: '模拟构建过程（生成虚拟制品）', level: '模拟', levelColor: 'orange' },
                { key: '4', stage: '单元测试', real: 'pytest / Jest 运行测试', demo: '模拟测试执行（返回假结果）', level: '模拟', levelColor: 'orange' },
                { key: '5', stage: '镜像打包', real: 'docker build + push', demo: '可真实执行（需 Docker 环境）/ 模拟降级', level: '可真实', levelColor: 'green' },
                { key: '6', stage: '镜像推送', real: 'Push 到镜像仓库', demo: '可真实执行（需配置 Registry）/ 模拟降级', level: '可真实', levelColor: 'green' },
                { key: '7', stage: '部署开发', real: 'kubectl apply / SSH 部署', demo: '可真实执行（需 kind 集群）/ 模拟降级', level: '可真实', levelColor: 'green' },
                { key: '8', stage: '部署测试', real: 'kubectl apply / SSH 部署', demo: '可真实执行（需 kind 集群）/ 模拟降级', level: '可真实', levelColor: 'green' },
                { key: '9', stage: '预发审批', real: '多级审批流程', demo: '模拟审批（一键通过）', level: '模拟', levelColor: 'orange' },
                { key: '10', stage: '部署预发', real: 'kubectl apply / SSH 部署', demo: '可真实执行（需 kind 集群）/ 模拟降级', level: '可真实', levelColor: 'green' },
                { key: '11', stage: '生产发布', real: 'kubectl apply / SSH 部署', demo: '可真实执行（需 kind 集群）/ 模拟降级', level: '可真实', levelColor: 'green' },
              ]}
              columns={[
                { title: '阶段', dataIndex: 'stage', key: 'stage', width: 100 },
                { title: '真实实现', dataIndex: 'real', key: 'real' },
                { title: 'Demo 实现', dataIndex: 'demo', key: 'demo' },
                {
                  title: '真实程度',
                  dataIndex: 'level',
                  key: 'level',
                  render: (text: string, record: any) => (
                    <Tag color={record.levelColor}>{text}</Tag>
                  ),
                },
              ]}
              pagination={false}
              size="small"
              bordered
            />
          </div>
        ),
      },
    ],
  },
  approval: {
    title: '审批流程对比',
    icon: <SafetyOutlined />,
    sections: [
      {
        title: '审批流程对比',
        content: {
          type: 'table',
          columns: ['对比维度', '真实审批流程', 'Demo 审批流程'],
          rows: [
            ['审批层级', '多级审批：AppOwner → 运维负责人 → 安全审核', '一键通过（模拟审批）'],
            ['审批方式', 'IM 通知 + 审批系统 + 邮件确认', '系统内模拟审批状态'],
            ['审批条件', '灰度检查、安全扫描、合规检查', '无条件通过'],
            ['紧急审批', '简化审批链 + 事后补流程', '不支持（未实现紧急发布）'],
            ['审批记录', '完整审批日志 + 审计追踪', '模拟审批记录'],
            ['审批超时', '超时自动升级 + 通知上级', '无超时机制'],
          ],
        },
      },
    ],
  },
  k8sGuide: {
    title: '如何启用真实 K8s 部署',
    icon: <ContainerOutlined />,
    sections: [
      {
        title: 'Kind 集群配置指南',
        content: (
          <div>
            <Alert
              type="info"
              showIcon
              title="让 Demo 系统真正操作 K8s 集群"
              description="通过配置本地 Kind（Kubernetes in Docker）集群，可以让 Demo 系统的部署操作真正生效，而不是模拟返回。"
              style={{ marginBottom: 16 }}
            />
            <Paragraph><Text strong>前置条件：</Text></Paragraph>
            <List
              size="small"
              dataSource={[
                { step: '1', title: '安装 Docker', desc: '确保 Docker Desktop 或 Docker Engine 已安装并运行。Kind 依赖 Docker 来运行 K8s 节点。' },
                { step: '2', title: '安装 Kind', desc: 'brew install kind（macOS）或从 GitHub Releases 下载二进制文件。Kind 是 K8s SIG 维护的官方工具。' },
                { step: '3', title: '安装 kubectl', desc: 'brew install kubectl（macOS）。kubectl 是 K8s 的命令行工具，用于与集群交互。' },
                { step: '4', title: '创建 Kind 集群', desc: '运行 kind create cluster --name demo-release。会创建一个单节点的 K8s 集群。' },
                { step: '5', title: '加载 kubeconfig', desc: 'kind get kubeconfig --name demo-release 获取集群配置，配置到 Demo 系统的 K8s 连接设置中。' },
                { step: '6', title: '验证连接', desc: 'kubectl cluster-info 确认集群状态正常。然后在 Demo 系统测试 K8s 连接。' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Tag color="blue">{item.step}</Tag>}
                    title={<Text strong>{item.title}</Text>}
                    description={item.desc}
                  />
                </List.Item>
              )}
            />
            <Divider />
            <Paragraph><Text strong>配置后效果：</Text></Paragraph>
            <ul>
              <li>发布流水线的部署阶段（阶段 7-11）将真实操作 Kind 集群</li>
              <li>滚动更新策略通过 kubectl 真实操作 Deployment</li>
              <li>可以在 Kind 集群中查看 Pod 的创建和销毁过程</li>
              <li>发布历史记录反映真实的部署状态</li>
              <li>未配置 Kind 集群时，系统自动降级为模拟模式</li>
            </ul>
          </div>
        ),
      },
    ],
  },
};

/* ============ 导出所有内容 ============ */

export { STRATEGY_ICONS, MODE_ICONS };