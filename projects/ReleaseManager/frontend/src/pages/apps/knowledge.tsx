import { Typography, Card, Collapse, Tag, Alert, Divider, Table, Descriptions, Space } from 'antd';
import {
  BookOutlined, InfoCircleOutlined, QuestionCircleOutlined,
  AppstoreOutlined, ApartmentOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const knowledgePanels = [
  {
    key: '1',
    label: (
      <Space>
        <AppstoreOutlined />
        <span>应用管理核心概念</span>
      </Space>
    ),
    children: (
      <div>
        <Paragraph>
          <strong>什么是应用（Application）？</strong>
        </Paragraph>
        <Paragraph>
          在发布系统中，<Text code>Application</Text> 是服务部署和运维管理的基本单元。一个「应用」对应一个可独立部署、独立运行的服务实例。它关联了代码仓库、构建配置、部署配置、环境配置等所有与发布运维相关的元信息。
        </Paragraph>
        <Paragraph>
          应用是发布系统数据模型的核心枢纽，串联起「代码 → 构建 → 制品 → 部署 → 运维」整个 CI/CD 流程。
        </Paragraph>

        <Divider />

        <Paragraph>
          <strong>应用管理 vs 发布管理：两个模块的职责划分</strong>
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '关注点', app: '应用的「配置」：谁来管、怎么部署、部署到哪里', release: '应用的「变更」：改了什么、何时上线、如何上线' },
            { key: '2', dimension: '核心对象', app: '应用、环境、部署配置', release: '发布单、流水线、发布策略' },
            { key: '3', dimension: '操作频率', app: '低频（新建/修改应用配置时）', release: '高频（每次功能上线都需要）' },
            { key: '4', dimension: '典型角色', app: '应用负责人、架构师', release: '开发工程师、SRE、审批人' },
            { key: '5', dimension: '权限特征', app: '编辑权限（配置变更）', release: '操作权限（执行发布）' },
          ]}
          columns={[
            { title: '对比维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '应用管理', dataIndex: 'app', key: 'app' },
            { title: '发布管理', dataIndex: 'release', key: 'release' },
          ]}
          pagination={false}
          size="small"
          bordered
          style={{ marginBottom: 16 }}
        />

        <Divider />

        <Paragraph>
          <strong>应用的生命周期</strong>
        </Paragraph>
        <Space size={[8, 8]} wrap>
          <Tag color="blue">创建</Tag>
          <Text type="secondary">→</Text>
          <Tag color="cyan">配置</Tag>
          <Text type="secondary">→</Text>
          <Tag color="green">发布</Tag>
          <Text type="secondary">→</Text>
          <Tag color="orange">运维</Tag>
          <Text type="secondary">→</Text>
          <Tag color="red">下线</Tag>
        </Space>
        <ul>
          <li><strong>创建：</strong>注册应用基本信息（名称、编码、开发语言、Git 仓库、负责人等）。</li>
          <li><strong>配置：</strong>为各环境配置部署参数（集群、命名空间、副本数、部署策略等）。</li>
          <li><strong>发布：</strong>通过发布单将应用的新版本部署到目标环境。</li>
          <li><strong>运维：</strong>日常的监控、扩缩容、重启、回滚等运维操作。</li>
          <li><strong>下线：</strong>应用不再需要时，从环境中移除并归档。</li>
        </ul>
      </div>
    ),
  },
  {
    key: '2',
    label: (
      <Space>
        <ApartmentOutlined />
        <span>应用与环境的绑定关系</span>
      </Space>
    ),
    children: (
      <div>
        <Paragraph>
          <strong>一个应用对应多个环境</strong>
        </Paragraph>
        <Paragraph>
          在发布系统中，一个应用通常需要部署到多个环境，例如：
        </Paragraph>
        <Space size={[4, 4]} wrap style={{ marginBottom: 16 }}>
          <Tag color="blue">dev</Tag>
          <Tag color="cyan">test1</Tag>
          <Tag color="cyan">test2</Tag>
          <Tag color="cyan">test3</Tag>
          <Tag color="cyan">test4</Tag>
          <Tag color="orange">pre</Tag>
          <Tag color="red">prod</Tag>
        </Space>
        <Paragraph>
          每个环境独立部署运行，服务于不同阶段的验证需求。开发环境（dev）用于开发自测，测试环境（test1-4）用于 QA 测试，预发环境（pre）用于上线前最终验证，生产环境（prod）面向真实用户。
        </Paragraph>

        <Divider />

        <Paragraph>
          <strong>每个环境的配置独立</strong>
        </Paragraph>
        <ul>
          <li><strong>集群：</strong>不同环境可能部署在不同的 K8s 集群或 EC2 集群中。</li>
          <li><strong>命名空间：</strong>K8s 环境下，每个环境对应独立的 Namespace，实现资源隔离。</li>
          <li><strong>副本数：</strong>测试环境通常 1-2 个副本，生产环境需要更多副本保障高可用。</li>
          <li><strong>部署策略：</strong>测试环境可用滚动更新快速迭代，生产环境可能需要灰度发布逐步放量。</li>
          <li><strong>资源配置：</strong>测试环境资源配额较低，生产环境资源充足。</li>
        </ul>

        <Divider />

        <Paragraph>
          <strong>环境配置的继承与覆盖机制</strong>
        </Paragraph>
        <Paragraph>
          为减少重复配置，系统支持环境配置的继承关系。例如，test1-test4 可以继承 test 基础配置，仅覆盖差异部分（如数据库连接串、域名等）。生产环境配置通常独立维护，不与测试环境共享任何敏感信息。
        </Paragraph>

        <Divider />

        <Paragraph>
          <strong>为什么需要环境隔离？</strong>
        </Paragraph>
        <ul>
          <li><strong>安全隔离：</strong>测试环境的 Bug 或异常不会影响生产环境真实用户。</li>
          <li><strong>资源隔离：</strong>测试负载不会抢占生产环境的 CPU、内存、网络等资源。</li>
          <li><strong>数据隔离：</strong>测试环境使用测试数据库，不会污染生产数据。</li>
          <li><strong>权限隔离：</strong>不同环境有不同的访问和操作权限，生产环境操作需要更严格的审批。</li>
          <li><strong>并行验证：</strong>多个测试环境（test1-4）可以同时验证不同版本或不同功能特性。</li>
        </ul>
      </div>
    ),
  },
  {
    key: '3',
    label: (
      <Space>
        <SettingOutlined />
        <span>应用元信息设计</span>
      </Space>
    ),
    children: (
      <div>
        <Paragraph>
          <strong>基础属性</strong>
        </Paragraph>
        <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="名称">应用的可读名称，如「用户中心」</Descriptions.Item>
          <Descriptions.Item label="编码">应用的唯一标识符，如「user-center」</Descriptions.Item>
          <Descriptions.Item label="开发语言">Python / Go / Node.js / Java 等</Descriptions.Item>
          <Descriptions.Item label="Git 仓库">代码仓库地址，用于关联 CI 构建</Descriptions.Item>
          <Descriptions.Item label="负责人" span={2}>应用的第一责任人，负责应用配置和发布审批</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Paragraph>
          <strong>构建配置</strong>
        </Paragraph>
        <Descriptions bordered size="small" column={1} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="构建镜像（环境基础镜像）">
            包含编译工具链的镜像，如 JDK + Maven、Node.js + npm。用于 CI 阶段的代码编译和构建。
          </Descriptions.Item>
          <Descriptions.Item label="应用基础镜像">
            预装应用运行所需环境的镜像，如 JRE、Python 运行时。不含编译工具，体积小巧，作为最终运行镜像的基础层。
          </Descriptions.Item>
        </Descriptions>
        <Paragraph type="secondary">
          这与「双镜像设计」理念一致：构建镜像负责编译，应用基础镜像负责运行，两者解耦使最终镜像体积更小、安全性更高。
        </Paragraph>

        <Divider />

        <Paragraph>
          <strong>部署配置</strong>
        </Paragraph>
        <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="部署模式">
            <Tag color="blue">EC2</Tag> 传统服务器部署 / <Tag color="purple">K8s</Tag> 容器化部署
          </Descriptions.Item>
          <Descriptions.Item label="部署策略">
            <Tag>滚动更新</Tag> <Tag color="cyan">蓝绿部署</Tag> <Tag color="orange">灰度发布</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="集群">目标 K8s 集群或 EC2 集群</Descriptions.Item>
          <Descriptions.Item label="命名空间">K8s Namespace（K8s 模式）</Descriptions.Item>
          <Descriptions.Item label="副本数">Pod 或实例数量</Descriptions.Item>
          <Descriptions.Item label="资源配额">CPU / 内存限制</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Paragraph>
          <strong>权限关联</strong>
        </Paragraph>
        <ul>
          <li><strong>所属业务线：</strong>应用归属的业务线，决定了权限继承的基础范围。同一业务线的成员默认拥有该业务线下应用的查看权限。</li>
          <li><strong>负责人：</strong>应用的第一责任人，拥有该应用的编辑权限，同时也是发布审批的默认审批人。</li>
        </ul>
      </div>
    ),
  },
  {
    key: '4',
    label: (
      <Space>
        <InfoCircleOutlined />
        <span>真实 Spug 中的应用管理</span>
      </Space>
    ),
    children: (
      <div>
        <Paragraph>
          以下结合实际项目经验（Spug 发布系统），说明应用管理模块的演进过程：
        </Paragraph>

        <Divider orientation={'left' as any}>V1 版本：以发布记录为中心</Divider>
        <ul>
          <li>应用信息散落在各发布记录中，没有统一的应用管理入口。</li>
          <li>查看应用配置时需要先找到该应用的发布记录，再从发布记录中查看。</li>
          <li>修改应用配置需要重新创建发布单，操作路径长、效率低。</li>
          <li>应用的「配置」和「发布」强耦合，难以独立管理。</li>
        </ul>

        <Divider orientation={'left' as any}>V2 版本：以应用为中心</Divider>
        <ul>
          <li>新增独立的「应用管理」模块，以应用为中心组织信息。</li>
          <li>应用详情页统一展示所有环境配置和发布历史，一目了然。</li>
          <li>操作面板将发布、回滚、重启等操作集中在应用详情页右侧，一键触达。</li>
          <li>配置变更与发布操作解耦，修改配置不需要创建发布单。</li>
        </ul>

        <Divider orientation={'left' as any}>权限分离</Divider>
        <Table
          dataSource={[
            { key: '1', module: '发布管理', permission: '只读 + 操作', desc: '查看发布历史，执行发布、回滚、重启等操作' },
            { key: '2', module: '应用管理', permission: '编辑配置', desc: '修改应用的基本信息、环境部署配置、构建配置等' },
          ]}
          columns={[
            { title: '模块', dataIndex: 'module', key: 'module', width: 120 },
            { title: '权限特征', dataIndex: 'permission', key: 'permission', width: 120 },
            { title: '说明', dataIndex: 'desc', key: 'desc' },
          ]}
          pagination={false}
          size="small"
          bordered
          style={{ marginBottom: 16 }}
        />
        <Paragraph>
          <Alert
            title="设计要点"
            description="将「配置管理」和「变更操作」分离，是发布系统设计的核心原则之一。应用管理关注「是什么」，发布管理关注「怎么变」，两者职责清晰、边界明确。"
            type="info"
            showIcon
          />
        </Paragraph>
      </div>
    ),
  },
  {
    key: '5',
    label: (
      <Space>
        <QuestionCircleOutlined />
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>面试重点</span>
      </Space>
    ),
    children: (
      <div style={{ background: '#f6ffed', padding: '16px 20px', borderRadius: 8 }}>
        <Paragraph style={{ marginBottom: 24 }}>
          <Text strong style={{ fontSize: 16 }}>
            以下是应用管理模块相关的面试重点问题，建议结合项目经验回答：
          </Text>
        </Paragraph>

        <Card size="small" style={{ marginBottom: 16, borderColor: '#b7eb8f' }}>
          <Paragraph strong>
            <Tag color="green">Q1</Tag> 应用管理模块的核心职责是什么？
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            应用管理模块负责应用的全生命周期管理，包括：注册应用基本信息（名称、编码、语言、仓库）、管理应用的部署配置（集群、命名空间、副本数、部署策略）、维护应用与环境的绑定关系、控制应用的权限归属（业务线 + 负责人）。它是发布系统的「配置中心」，为发布管理提供基础的元数据支撑。
          </Paragraph>
        </Card>

        <Card size="small" style={{ marginBottom: 16, borderColor: '#b7eb8f' }}>
          <Paragraph strong>
            <Tag color="green">Q2</Tag> 一个应用如何管理多个环境的配置？环境之间如何隔离？
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            一个应用通过「环境配置」表关联多个环境（dev/test1-4/pre/prod），每个环境有独立的集群、命名空间、副本数、部署策略等配置。环境之间通过以下方式隔离：① 部署在不同的 K8s 集群或 Namespace 中实现资源隔离；② 使用不同的数据库实例实现数据隔离；③ 通过 RBAC 权限控制实现操作隔离；④ 支持配置继承机制，子环境继承父环境配置并覆盖差异项，减少重复配置。
          </Paragraph>
        </Card>

        <Card size="small" style={{ marginBottom: 16, borderColor: '#b7eb8f' }}>
          <Paragraph strong>
            <Tag color="green">Q3</Tag> 应用管理和发布管理的权限如何划分？
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            应用管理授予「编辑配置」权限，允许修改应用的基本信息、环境部署配置、构建配置等；发布管理授予「只读 + 操作」权限，允许查看发布历史和配置，执行发布、回滚、重启等操作。这种设计将「配置管理」和「变更操作」分离，各角色职责清晰。应用负责人通常拥有应用管理的编辑权限，而开发工程师和 SRE 拥有发布管理的操作权限。
          </Paragraph>
        </Card>

        <Card size="small" style={{ marginBottom: 16, borderColor: '#b7eb8f' }}>
          <Paragraph strong>
            <Tag color="green">Q4</Tag> 应用的生命周期管理包含哪些阶段？
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            应用的生命周期分为五个阶段：<strong>创建</strong>（注册应用基本信息）→ <strong>配置</strong>（为各环境配置部署参数）→ <strong>发布</strong>（通过发布单将新版本部署到目标环境）→ <strong>运维</strong>（日常监控、扩缩容、重启、回滚等）→ <strong>下线</strong>（从环境中移除并归档）。每个阶段都有对应的操作入口和权限控制，确保应用从创建到下线的全流程可管理、可追溯。
          </Paragraph>
        </Card>

        <Card size="small" style={{ borderColor: '#b7eb8f' }}>
          <Paragraph strong>
            <Tag color="green">Q5</Tag> 新建一个应用时，需要配置哪些信息？
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            新建应用需要配置三类信息：① <strong>基础属性</strong>（名称、编码、描述、开发语言、Git 仓库地址、业务线、负责人）；② <strong>构建配置</strong>（构建镜像/环境基础镜像、应用基础镜像、构建命令等）；③ <strong>部署配置</strong>（部署模式 EC2/K8s、部署策略滚动/蓝绿/灰度、目标集群、命名空间、副本数、资源配额等）。此外还需要为各环境（dev/test/pre/prod）分别配置差异化参数，如环境变量、配置文件、健康检查策略等。
          </Paragraph>
        </Card>
      </div>
    ),
  },
];

export default function AppKnowledgePage() {
  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <BookOutlined style={{ fontSize: 24, color: '#1677ff' }} />
        <Title level={3} style={{ margin: 0 }}>应用管理知识库</Title>
      </div>

      <Collapse
        items={knowledgePanels}
        defaultActiveKey={['1']}
        style={{ background: '#fff' }}
      />
    </div>
  );
}