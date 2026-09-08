import { Typography, Table, Card, Descriptions, Alert, Divider } from 'antd';

const { Title, Paragraph, Text } = Typography;

/* =============================================================================
 * 一、常规面试题（~40道，16个领域）
 * ============================================================================= */

export const regularQuestions = [
  /* ---- 1. CI/CD 基础 ---- */
  {
    key: 'r1-1',
    label: 'CI/CD 分别是什么？发布系统在 CI/CD 中处于什么位置？',
    category: 'CI/CD 基础',
    q: 'CI/CD 分别是什么？发布系统在 CI/CD 中处于什么位置？',
    a: (
      <div>
        <Paragraph>
          <Text strong>CI（持续集成 Continuous Integration）</Text> 是指开发人员频繁地将代码变更合并到主干分支，每次合并都自动触发构建和自动化测试，确保代码变更不会破坏已有功能。CI 的核心价值在于 <Text strong>「早发现、早修复」</Text>——在代码合并阶段就发现集成问题，而不是等到发布前才暴露。
        </Paragraph>
        <Paragraph>
          <Text strong>CD 有两个含义：</Text>
          <ul>
            <li><Text strong>持续交付（Continuous Delivery）：</Text>在 CI 的基础上，确保代码随时处于可发布状态。每次变更通过自动化测试后，可以一键部署到生产环境，但部署操作仍需要人工触发。</li>
            <li><Text strong>持续部署（Continuous Deployment）：</Text>持续交付的进一步自动化——代码变更通过所有测试后，自动部署到生产环境，无需人工干预。</li>
          </ul>
        </Paragraph>
        <Paragraph>
          <Text strong>发布系统在 CI/CD 中的位置：</Text>发布系统处于 CI/CD 流水线的<Text strong>末端</Text>，负责将构建好的制品部署到目标环境。它承接 CI 阶段产出的制品，执行 CD 阶段的部署操作。具体来说：CI 负责「构建和验证」，CD 负责「部署和发布」，发布系统是 CD 的核心执行引擎。
        </Paragraph>
        <Paragraph>
          <Text type="secondary">面试加分：能清晰区分 CI 和 CD 的职责边界，并指出发布系统在 CD 中的角色，体现对整体流程的理解。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r1-2',
    label: '持续交付和持续部署的区别',
    category: 'CI/CD 基础',
    q: '持续交付（Continuous Delivery）和持续部署（Continuous Deployment）有什么区别？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '核心定义', delivery: '代码随时可发布，部署需人工触发', deployment: '代码通过验证后自动部署到生产' },
            { key: '2', dimension: '人工干预', delivery: '部署到生产需要人工确认', deployment: '完全自动化，无需人工干预' },
            { key: '3', dimension: '发布频率', delivery: '由业务需求决定，可随时发布', deployment: '每次代码变更都可能触发部署' },
            { key: '4', dimension: '风险控制', delivery: '人工决策，风险可控', deployment: '需要高度完善的自动化测试和监控' },
            { key: '5', dimension: '适用团队', delivery: '大多数团队', deployment: '成熟的 DevOps 团队（如 Netflix、Amazon）' },
            { key: '6', dimension: '审批流程', delivery: '保留生产环境审批', deployment: '自动化代替审批，依赖事后审计' },
          ]}
          columns={[
            { title: '对比维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '持续交付', dataIndex: 'delivery', key: 'delivery' },
            { title: '持续部署', dataIndex: 'deployment', key: 'deployment' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>关键理解：</Text>持续交付是持续部署的<Text strong>前置条件</Text>。没有完善的持续交付能力，就不可能实现持续部署。持续部署是持续交付的「终极形态」，但并非所有团队都需要追求持续部署。
        </Paragraph>
        <Paragraph>
          <Text type="secondary">面试加分：能用表格对比，并能指出「持续交付是基础，持续部署是进阶」的递进关系。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r1-3',
    label: 'CI/CD 流水线包含哪些阶段',
    category: 'CI/CD 基础',
    q: '一个标准的 CI/CD 流水线包含哪些阶段？每个阶段做什么？',
    a: (
      <div>
        <Paragraph>一个标准的 CI/CD 流水线通常包含以下阶段：</Paragraph>
        <ol>
          <li><Text strong>代码提交（Commit）：</Text>开发者提交代码到 Git 仓库，触发流水线</li>
          <li><Text strong>代码审查（Code Review）：</Text>自动化代码风格检查、静态代码分析（SonarQube、ESLint 等）</li>
          <li><Text strong>构建编译（Build）：</Text>编译源代码、打包依赖、生成可执行文件或制品</li>
          <li><Text strong>单元测试（Unit Test）：</Text>运行单元测试，验证代码逻辑正确性</li>
          <li><Text strong>镜像打包（Image Build）：</Text>将制品打包为 Docker 镜像</li>
          <li><Text strong>制品推送（Artifact Push）：</Text>将镜像推送到镜像仓库（如 Harbor、ECR）</li>
          <li><Text strong>部署开发环境（Deploy Dev）：</Text>自动部署到开发环境，开发自测</li>
          <li><Text strong>集成测试（Integration Test）：</Text>在测试环境运行集成测试</li>
          <li><Text strong>预发审批（Pre-release Approval）：</Text>生产环境部署前需要审批通过</li>
          <li><Text strong>部署预发环境（Deploy Staging）：</Text>部署到预发环境，做最后的验证</li>
          <li><Text strong>生产发布（Production Release）：</Text>使用选定的部署策略（滚动/蓝绿/灰度）上线</li>
        </ol>
        <Paragraph>
          <Text strong>关键设计原则：</Text>流水线应该<Text strong>「快速失败」</Text>——将耗时短、失败率高的阶段放在前面（如代码检查、单元测试），将耗时长的阶段放在后面（如镜像构建、部署）。这样可以在早期快速发现问题，避免浪费资源。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 2. 发布系统核心概念 ---- */
  {
    key: 'r2-1',
    label: '部署和发布的区别',
    category: '发布系统核心概念',
    q: '部署（Deploy）和发布（Release）是一回事吗？区别是什么？',
    a: (
      <div>
        <Paragraph>
          <Text strong>不是一回事。</Text>这是发布系统面试中最高频的基础概念题，很多候选人会混淆。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '定义', deploy: '将代码/制品安装到目标环境的过程', release: '让用户能够使用新功能的过程' },
            { key: '2', dimension: '关注点', deploy: '技术层面：文件传输、进程启动、配置更新', release: '业务层面：功能启用、流量切换、用户体验' },
            { key: '3', dimension: '可逆性', deploy: '部署后可以保持不对外服务', release: '一旦发布，用户就开始使用' },
            { key: '4', dimension: '方式', deploy: '通过脚本、CI/CD 工具执行', release: '通过流量切换、Feature Flag 等方式' },
            { key: '5', dimension: '例子', deploy: '将 v2 镜像部署到 K8s 集群', release: '打开 Feature Flag 让用户看到新功能' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 100 },
            { title: '部署 Deploy', dataIndex: 'deploy', key: 'deploy' },
            { title: '发布 Release', dataIndex: 'release', key: 'release' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>记忆技巧：</Text>「部署是技术动作，发布是业务动作」。Feature Flag 就是一个典型的「部署未发布」的例子——代码已经部署到生产环境，但功能开关关闭，用户看不到。蓝绿部署中，新版本部署到绿色环境但流量未切换，也是「部署未发布」。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r2-2',
    label: '发布单包含哪些核心信息',
    category: '发布系统核心概念',
    q: '什么是发布单（Release Order）？它包含哪些核心信息？',
    a: (
      <div>
        <Paragraph>
          <Text strong>发布单</Text>是发布系统中的核心数据实体，它记录了<Text strong>一次完整的发布操作</Text>的所有信息，是发布流程的「工作票」和「档案记录」。
        </Paragraph>
        <Paragraph><Text strong>发布单包含的核心信息：</Text></Paragraph>
        <Descriptions column={1} size="small" bordered style={{ marginBottom: 12 }}>
          <Descriptions.Item label="基本信息"><Text strong>发布标题、创建人、创建时间、发布状态</Text>（待审批/审批中/发布中/成功/失败/已回滚）</Descriptions.Item>
          <Descriptions.Item label="目标信息"><Text strong>应用名称、目标环境</Text>（开发/测试/预发/生产）、<Text strong>部署目标</Text>（主机列表/K8s 集群）</Descriptions.Item>
          <Descriptions.Item label="版本信息"><Text strong>Git 分支/Tag、Commit ID、构建产物地址</Text>（镜像 Tag、制品 URL）</Descriptions.Item>
          <Descriptions.Item label="策略信息"><Text strong>发布模式</Text>（常规/增量/补偿/快速/回滚）、<Text strong>部署策略</Text>（滚动/蓝绿/灰度）</Descriptions.Item>
          <Descriptions.Item label="审批信息"><Text strong>审批人、审批状态、审批时间、审批意见</Text></Descriptions.Item>
          <Descriptions.Item label="执行信息"><Text strong>开始时间、结束时间、执行耗时、每台主机的部署结果</Text></Descriptions.Item>
          <Descriptions.Item label="回滚信息"><Text strong>回滚来源发布单 ID、回滚版本号</Text></Descriptions.Item>
        </Descriptions>
        <Paragraph>
          <Text strong>为什么需要发布单：</Text>发布单是<Text strong>发布操作的可追溯单位</Text>。它解决了「谁在什么时间、对什么应用、在什么环境、做了什么操作、结果如何」的问题，是发布审计和问题排查的基础。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r2-3',
    label: '发布策略和发布模式的区别',
    category: '发布系统核心概念',
    q: '发布策略（Deploy Strategy）和发布模式（Release Mode）有什么区别？',
    a: (
      <div>
        <Paragraph>
          <Text strong>发布策略</Text>和<Text strong>发布模式</Text>是发布系统中两个不同维度的概念，经常被混淆。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '回答的问题', strategy: '「怎么上线？」——如何将新版本平稳地部署到生产环境', mode: '「做什么范围？」——是否需要完整构建？是否跳过某些步骤？' },
            { key: '2', dimension: '典型例子', strategy: '滚动更新、蓝绿部署、灰度发布、重建部署', mode: '常规发布、增量发布、补偿发布、快速发布、回滚发布' },
            { key: '3', dimension: '关注点', strategy: '流量切换方式、实例替换策略、风险控制', mode: '流水线执行范围、构建是否需要重做、目标选择范围' },
            { key: '4', dimension: '独立性', strategy: '独立于发布模式，同一模式可使用不同策略', mode: '独立于发布策略，同一策略可用于不同模式' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '发布策略 Deploy Strategy', dataIndex: 'strategy', key: 'strategy' },
            { title: '发布模式 Release Mode', dataIndex: 'mode', key: 'mode' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>组合示例：</Text>
          <ul>
            <li>「常规发布 + 滚动更新」：完整 CI/CD 流水线，使用滚动更新策略上线</li>
            <li>「快速发布 + 灰度发布」：跳过构建阶段，复用已有制品，使用灰度策略逐步放量</li>
            <li>「回滚发布 + 蓝绿部署」：回滚到旧版本，使用蓝绿切换方式快速恢复</li>
          </ul>
        </Paragraph>
        <Paragraph>
          <Text type="secondary">面试加分：能清晰区分这两个概念，并给出组合示例，体现系统设计思维。</Text>
        </Paragraph>
      </div>
    ),
  },

  /* ---- 3. 版本管理 ---- */
  {
    key: 'r3-1',
    label: '语义化版本',
    category: '版本管理',
    q: '什么是语义化版本（Semantic Versioning）？发布系统如何管理版本号？',
    a: (
      <div>
        <Paragraph>
          <Text strong>语义化版本（SemVer）</Text>的格式为 <Text strong>MAJOR.MINOR.PATCH</Text>（如 2.3.1）：
        </Paragraph>
        <ul>
          <li><Text strong>MAJOR（主版本号）：</Text>不兼容的 API 修改，如 1.x.x → 2.0.0</li>
          <li><Text strong>MINOR（次版本号）：</Text>向下兼容的功能新增，如 2.1.x → 2.2.0</li>
          <li><Text strong>PATCH（修订号）：</Text>向下兼容的问题修复，如 2.2.1 → 2.2.2</li>
        </ul>
        <Paragraph>
          <Text strong>发布系统中版本号的管理策略：</Text>
        </Paragraph>
        <ul>
          <li><Text strong>自动生成：</Text>基于 Git Tag 或 CI 构建号自动生成版本号，避免人工指定</li>
          <li><Text strong>与 Git 关联：</Text>每个版本号对应一个 Git Commit/Tag，确保代码可追溯</li>
          <li><Text strong>与制品关联：</Text>版本号同时作为镜像 Tag 和制品标识，例如 <Text code>my-app:2.3.1</Text></li>
          <li><Text strong>版本递增策略：</Text>PATCH 自动递增（每次构建 +1），MINOR 和 MAJOR 由开发者手动指定</li>
          <li><Text strong>预发布版本：</Text>支持 alpha/beta/rc 等后缀，如 2.4.0-beta.1</li>
        </ul>
        <Paragraph>
          <Text type="secondary">面试加分：能说出「版本号应该由 CI 系统自动生成，不应人工指定」，体现自动化思维。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r3-2',
    label: 'Git 分支策略与发布系统',
    category: '版本管理',
    q: 'Git 分支策略（Git Flow / Trunk-based）与发布系统如何配合？',
    a: (
      <div>
        <Paragraph><Text strong>两种主流分支策略：</Text></Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '核心思想', gitflow: '多分支并行开发，通过分支管理发布节奏', trunk: '所有开发者在主干分支上协作，短生命周期分支' },
            { key: '2', dimension: '分支类型', gitflow: 'main / develop / feature / release / hotfix', trunk: 'main + 短生命周期 feature 分支（< 1天）' },
            { key: '3', dimension: '发布方式', gitflow: '从 release 分支发布，发布后合并回 main 和 develop', trunk: '从 main 分支发布，依赖 Feature Flag 控制功能上线' },
            { key: '4', dimension: '发布频率', gitflow: '较低，适合有固定发布周期的团队', trunk: '高，适合持续部署的团队' },
            { key: '5', dimension: '版本管理', gitflow: '每次发布打 Tag，版本号清晰', trunk: '每次提交都可能触发发布，版本号频繁变更' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: 'Git Flow', dataIndex: 'gitflow', key: 'gitflow' },
            { title: 'Trunk-based', dataIndex: 'trunk', key: 'trunk' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>发布系统如何配合：</Text>
        </Paragraph>
        <ul>
          <li><Text strong>Git Flow 模式：</Text>发布系统从 release 分支或 master 分支拉取代码，发布完成后自动打 Tag。发布系统需要支持「选择分支/Tag」作为发布源。</li>
          <li><Text strong>Trunk-based 模式：</Text>发布系统从 main 分支拉取代码，每次提交都触发 CI 构建。发布系统需要配合 Feature Flag 系统，确保未完成的功能不会暴露给用户。</li>
          <li><Text strong>通用做法：</Text>发布系统不强依赖某种分支策略，而是通过「发布源」配置来适配不同的分支策略。</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r3-3',
    label: '版本溯源',
    category: '版本管理',
    q: '发布系统中如何做版本溯源？怎么知道当前生产环境运行的是哪个版本？',
    a: (
      <div>
        <Paragraph>
          <Text strong>版本溯源</Text>是发布系统的基础能力，需要回答「当前生产环境运行的是哪个版本、什么时候发布的、谁发布的」。
        </Paragraph>
        <Paragraph><Text strong>实现方案：</Text></Paragraph>
        <ul>
          <li><Text strong>发布记录：</Text>每次发布都在数据库中记录一条发布记录，包含应用名、环境、版本号、Git Commit、发布时间、操作人等</li>
          <li><Text strong>版本端点：</Text>每个应用暴露 <Text code>/version</Text> 或 <Text code>/health</Text> 端点，返回当前运行版本信息（版本号、Commit ID、构建时间）</li>
          <li><Text strong>K8s 标签：</Text>在 Deployment 的 Pod Template 中添加版本标签，方便通过 kubectl 查询</li>
          <li><Text strong>CMDB 集成：</Text>发布系统更新 CMDB 中的应用版本信息，形成统一的配置管理视图</li>
          <li><Text strong>GitOps 模式：</Text>使用 Git 仓库作为唯一真实来源（Single Source of Truth），Git 仓库中的配置文件记录了每个环境的期望版本</li>
        </ul>
        <Paragraph>
          <Text strong>最佳实践：</Text>将版本信息写入应用镜像的元数据中（如 Docker Label），这样无论应用部署在哪里，都能通过容器元数据获取版本信息，实现「版本自描述」。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 4. 制品管理 ---- */
  {
    key: 'r4-1',
    label: '制品与 Docker 镜像的区别',
    category: '制品管理',
    q: '什么是制品（Artifact）？制品和 Docker 镜像的区别？',
    a: (
      <div>
        <Paragraph>
          <Text strong>制品（Artifact）</Text>是构建过程产出的<Text strong>可部署单元</Text>，可能是 JAR 包、WAR 包、二进制文件、静态资源包、Docker 镜像等。制品是发布系统的「原材料」，发布系统根据制品类型选择不同的部署方式。
        </Paragraph>
        <Paragraph>
          <Text strong>Docker 镜像</Text>是制品的一种<Text strong>具体形式</Text>。在容器化部署场景中，Docker 镜像就是制品。但在非容器化场景中，制品可能是其他形式。两者的关系是<Text strong>「制品是抽象概念，Docker 镜像是具体实现」</Text>。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '定义', artifact: '构建产出的可部署单元', image: '符合 OCI 标准的容器镜像格式' },
            { key: '2', dimension: '范围', artifact: '更广泛的概念，包含各种格式', image: '制品的子集，容器化场景的制品' },
            { key: '3', dimension: '部署方式', artifact: 'SSH 分发、SCP 传输、kubectl apply 等', image: 'Docker pull/run、K8s 部署等' },
            { key: '4', dimension: '存储', artifact: '制品仓库（Nexus、Artifactory、对象存储）', image: '镜像仓库（Harbor、Docker Hub、ECR）' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '制品 Artifact', dataIndex: 'artifact', key: 'artifact' },
            { title: 'Docker 镜像', dataIndex: 'image', key: 'image' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
      </div>
    ),
  },
  {
    key: 'r4-2',
    label: '制品晋级',
    category: '制品管理',
    q: '制品晋级（Artifact Promotion）是什么？为什么需要它？',
    a: (
      <div>
        <Paragraph>
          <Text strong>制品晋级</Text>是指同一个制品（同一构建产物）在不同环境之间<Text strong>逐级推进</Text>的过程，而不是在每个环境都重新构建。
        </Paragraph>
        <Paragraph><Text strong>核心原则：一次构建，多处部署（Build Once, Deploy Everywhere）。</Text></Paragraph>
        <Paragraph><Text strong>制品的晋级路径：</Text></Paragraph>
        <ol>
          <li><Text strong>构建阶段：</Text>CI 构建产出制品，推送到制品仓库的开发区域</li>
          <li><Text strong>开发环境验证：</Text>在开发环境中部署该制品，通过基本功能验证</li>
          <li><Text strong>晋级到测试：</Text>制品从开发区域「晋级」到测试区域（可以是制品仓库中的位置变更或标签变更）</li>
          <li><Text strong>测试环境验证：</Text>在测试环境中运行自动化测试</li>
          <li><Text strong>晋级到预发：</Text>制品晋级到预发区域，在预发环境做最终验证</li>
          <li><Text strong>晋级到生产：</Text>制品晋级到生产区域，部署到生产环境</li>
        </ol>
        <Paragraph>
          <Text strong>为什么需要制品晋级：</Text>
          <ul>
            <li><Text strong>一致性保证：</Text>确保生产环境部署的制品和测试环境验证的是同一个制品，避免「测试通过的版本和生产的版本不一致」</li>
            <li><Text strong>安全性：</Text>通过晋级机制控制制品流向，防止未经测试的制品进入生产环境</li>
            <li><Text strong>审计追溯：</Text>记录制品在每个环境的部署历史，形成完整的制品生命周期追溯</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r4-3',
    label: '制品不可变性',
    category: '制品管理',
    q: '如何保证制品的不可变性？构建产物被篡改的风险如何防范？',
    a: (
      <div>
        <Paragraph>
          <Text strong>制品的不可变性</Text>是指制品一旦构建完成，其内容就<Text strong>不再修改</Text>。任何代码变更都应该产生新的制品，而不是修改已有制品。
        </Paragraph>
        <Paragraph><Text strong>保证不可变性的措施：</Text></Paragraph>
        <ul>
          <li><Text strong>内容寻址存储：</Text>使用 SHA256 作为制品标识（如 Docker 镜像的 Digest），同一个内容永远对应同一个标识</li>
          <li><Text strong>制品仓库不可变策略：</Text>配置制品仓库（Harbor、Nexus）禁止覆盖已有 Tag，强制使用新 Tag 或 Digest</li>
          <li><Text strong>签名验证：</Text>使用 Cosign/Notary 对制品进行数字签名，部署时验证签名，确保制品未被篡改</li>
          <li><Text strong>不可变 Tag：</Text>使用 Git Commit SHA 作为镜像 Tag，而不是使用可变的 <Text code>latest</Text> Tag</li>
          <li><Text strong>供应链安全：</Text>使用 SLSA（Supply-chain Levels for Software Artifacts）框架，确保构建过程的完整性和可追溯性</li>
        </ul>
        <Paragraph>
          <Text strong>被篡改的风险场景：</Text>
          <ul>
            <li>攻击者通过 CI 系统漏洞注入恶意代码到构建产物中</li>
            <li>中间人攻击替换制品仓库中的制品</li>
            <li>运维人员手动修改服务器上的制品文件</li>
          </ul>
        </Paragraph>
        <Paragraph>
          <Text type="secondary">面试加分：能提到制品签名和供应链安全（SLSA/SBOM），体现安全意识和深度。</Text>
        </Paragraph>
      </div>
    ),
  },

  /* ---- 5. 部署策略概念 ---- */
  {
    key: 'r5-1',
    label: '滚动/蓝绿/灰度的核心区别',
    category: '部署策略概念',
    q: '滚动更新、蓝绿部署、灰度发布这三种策略的核心区别是什么？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '核心机制', rolling: '逐步替换实例', blue: '环境切换', canary: '渐进式放量' },
            { key: '2', dimension: '资源需求', rolling: '1x（无额外资源）', blue: '2x（两套环境）', canary: '1x+（少量额外实例）' },
            { key: '3', dimension: '切换速度', rolling: '分钟级（逐批替换）', blue: '秒级（路由切换）', canary: '小时级（逐步放大）' },
            { key: '4', dimension: '回滚速度', rolling: '分钟级（反向滚动）', blue: '秒级（切回旧环境）', canary: '秒级（回滚灰度实例）' },
            { key: '5', dimension: '风险等级', rolling: '中', blue: '低', canary: '极低' },
            { key: '6', dimension: '新旧共存', rolling: '是（更新过程中）', blue: '否（切换后只有新版本）', canary: '是（灰度期间）' },
            { key: '7', dimension: '推荐场景', rolling: '日常更新', blue: '重大版本', canary: '高风险变更' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '滚动更新', dataIndex: 'rolling', key: 'rolling' },
            { title: '蓝绿部署', dataIndex: 'blue', key: 'blue' },
            { title: '灰度发布', dataIndex: 'canary', key: 'canary' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>记忆技巧：</Text>滚动更新像「接力赛」（逐个替换），蓝绿部署像「变魔术」（瞬间切换），灰度发布像「温水煮青蛙」（逐步渗透）。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r5-2',
    label: '重建部署与滚动更新',
    category: '部署策略概念',
    q: '什么是重建部署（Recreate）？它和滚动更新的本质区别是什么？',
    a: (
      <div>
        <Paragraph>
          <Text strong>重建部署（Recreate）</Text>是最简单也最粗暴的部署策略：<Text strong>先停止所有旧版本实例，再启动所有新版本实例</Text>。在停止和启动之间，服务完全不可用。
        </Paragraph>
        <Paragraph><Text strong>与滚动更新的本质区别：</Text></Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '服务可用性', recreate: '有停机时间（停止→启动之间）', rolling: '零停机（始终有实例在运行）' },
            { key: '2', dimension: '新旧共存', recreate: '不会共存（先全停，再全启）', rolling: '更新过程中新旧共存' },
            { key: '3', dimension: '资源需求', recreate: '1x（但可能浪费资源在等待中）', rolling: '1x + maxSurge 额外资源' },
            { key: '4', dimension: '实现复杂度', recreate: '极低', rolling: '中等' },
            { key: '5', dimension: '适用场景', recreate: '开发环境、离线任务、允许停机的服务', rolling: '需要持续可用的生产服务' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '重建部署', dataIndex: 'recreate', key: 'recreate' },
            { title: '滚动更新', dataIndex: 'rolling', key: 'rolling' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text type="secondary">面试加分：能指出重建部署在 K8s 中是 Deployment 的 strategy.type 选项之一，虽然不常用但仍有其存在价值。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r5-3',
    label: '红黑部署与蓝绿部署',
    category: '部署策略概念',
    q: '什么是红黑部署（Red-Black）？和蓝绿部署有什么异同？',
    a: (
      <div>
        <Paragraph>
          <Text strong>红黑部署</Text>是 Netflix 提出并广泛采用的部署策略。它与蓝绿部署非常相似，核心区别在于：<Text strong>切换后立即回收旧环境</Text>。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '环境保持', blue: '切换后旧环境保留一段时间', red: '切换后旧环境立即销毁' },
            { key: '2', dimension: '回滚方式', blue: '切换回保留的旧环境', red: '需要重新部署旧版本' },
            { key: '3', dimension: '回滚速度', blue: '秒级', red: '分钟级（重新部署）' },
            { key: '4', dimension: '资源成本', blue: '持续 2x 资源消耗', red: '切换后释放资源，成本更低' },
            { key: '5', dimension: '命名来源', blue: 'Netflix 原版为蓝绿，后改名红黑', red: 'Netflix 在 Spinnaker 中的实现' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '蓝绿部署', dataIndex: 'blue', key: 'blue' },
            { title: '红黑部署', dataIndex: 'red', key: 'red' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>为什么 Netflix 选择红黑：</Text>Netflix 的部署频率极高（每天数千次），如果每次部署都保留旧环境，资源成本将不可接受。红黑部署在「快速回滚」和「资源效率」之间做了取舍，选择了资源效率优先。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 6. 发布模式概念 ---- */
  {
    key: 'r6-1',
    label: '常规/增量/补偿发布的区别',
    category: '发布模式概念',
    q: '常规发布、增量发布、补偿发布的区别是什么？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '目标范围', regular: '所有目标实例', incremental: '仅新增/未部署的实例', compensation: '仅上次发布失败的实例' },
            { key: '2', dimension: '前置条件', regular: '无', incremental: '已存在已部署的实例', compensation: '上次发布有部分失败' },
            { key: '3', dimension: '构建阶段', regular: '是，完整构建', incremental: '可选，取决于是否有变更', compensation: '复用上次构建产物' },
            { key: '4', dimension: '典型场景', regular: '日常版本迭代', incremental: '集群扩容', compensation: '发布失败后的重试' },
            { key: '5', dimension: '是否影响已部署实例', regular: '是（全部替换）', incremental: '否（仅新增）', compensation: '否（仅重试失败）' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '常规发布', dataIndex: 'regular', key: 'regular' },
            { title: '增量发布', dataIndex: 'incremental', key: 'incremental' },
            { title: '补偿发布', dataIndex: 'compensation', key: 'compensation' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
      </div>
    ),
  },
  {
    key: 'r6-2',
    label: '快速发布与常规发布',
    category: '发布模式概念',
    q: '快速发布和常规发布的区别是什么？什么场景下使用快速发布？',
    a: (
      <div>
        <Paragraph>
          <Text strong>快速发布</Text>的核心特点是<Text strong>跳过构建阶段</Text>，直接复用最近一次成功的构建产物进行部署。它和常规发布的关键区别在于<Text strong>是否重新构建</Text>。
        </Paragraph>
        <Paragraph><Text strong>使用场景：</Text></Paragraph>
        <ul>
          <li><Text strong>紧急 Bug 修复：</Text>代码已修复并构建过，需要快速上线</li>
          <li><Text strong>配置变更：</Text>只修改了环境配置，代码未变</li>
          <li><Text strong>服务重启：</Text>需要重新部署但不需要重新构建</li>
          <li><Text strong>上次构建成功但部署失败：</Text>复用构建产物重试部署</li>
        </ul>
        <Paragraph>
          <Text strong>注意事项：</Text>快速发布依赖于上次构建产物仍然可用（未被清理）。如果制品仓库有清理策略，长期未使用的产物可能被清理，快速发布就会失败。因此，快速发布通常在<Text strong>构建完成后短期内</Text>使用。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r6-3',
    label: '回滚发布和紧急发布',
    category: '发布模式概念',
    q: '回滚发布和紧急发布有什么区别？各自的适用场景？',
    a: (
      <div>
        <Paragraph>
          <Text strong>回滚发布</Text>是将服务恢复到<Text strong>上一个稳定版本</Text>，而<Text strong>紧急发布</Text>（通常以快速发布模式执行）是部署一个<Text strong>新的修复版本</Text>。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '目标版本', rollback: '历史已知稳定版本', emergency: '新的修复版本（Hotfix）' },
            { key: '2', dimension: '是否需要构建', rollback: '否（复用旧制品）', emergency: '是（需要构建修复版本）' },
            { key: '3', dimension: '数据兼容性', rollback: '可能不兼容（新数据旧代码）', emergency: '修复版本可设计为兼容' },
            { key: '4', dimension: '适用场景', rollback: '新版本有严重 Bug，快速恢复', emergency: '安全漏洞、数据损坏等需要修复的场景' },
            { key: '5', dimension: '决策依据', rollback: '"先恢复服务，再分析问题"', emergency: '"先修复问题，再发布上线"' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '回滚发布', dataIndex: 'rollback', key: 'rollback' },
            { title: '紧急发布', dataIndex: 'emergency', key: 'emergency' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>决策思路：</Text>如果问题是「新版本引入的 Bug」，回滚是首选（快速恢复）。如果问题是「数据损坏、安全漏洞」，回滚无法解决根本问题，需要紧急修复发布。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 7. 环境管理 ---- */
  {
    key: 'r7-1',
    label: '环境隔离与一致性',
    category: '环境管理',
    q: '开发、测试、预发、生产环境应该怎么隔离？环境一致性如何保证？',
    a: (
      <div>
        <Paragraph><Text strong>环境隔离策略：</Text></Paragraph>
        <ul>
          <li><Text strong>网络隔离：</Text>不同环境使用不同的 VPC/子网，网络层面完全隔离</li>
          <li><Text strong>资源隔离：</Text>不同环境使用独立的 K8s 集群或 Namespace，计算资源不共享</li>
          <li><Text strong>数据隔离：</Text>不同环境使用独立的数据库实例，测试数据不污染生产数据</li>
          <li><Text strong>权限隔离：</Text>开发环境允许开发者自由操作，生产环境需要严格审批</li>
          <li><Text strong>配置隔离：</Text>不同环境使用独立的配置（数据库连接、API Key 等），通过环境变量注入</li>
        </ul>
        <Paragraph><Text strong>环境一致性保证：</Text></Paragraph>
        <ul>
          <li><Text strong>同一镜像/制品：</Text>所有环境使用相同的 Docker 镜像，只是配置不同</li>
          <li><Text strong>基础设施即代码（IaC）：</Text>使用 Terraform/CloudFormation 定义基础设施，确保环境配置一致</li>
          <li><Text strong>配置版本化：</Text>环境配置存储在 Git 中，变更可追溯</li>
          <li><Text strong>预发环境 = 生产镜像：</Text>预发环境应该和生产环境使用完全相同的配置和资源规格</li>
          <li><Text strong>定期巡检：</Text>自动化检查各环境间的配置差异，及时发现漂移</li>
        </ul>
        <Paragraph>
          <Text type="secondary">面试加分：能指出「预发环境应该和生产环境 1:1 配置」，这是发现环境差异问题的关键。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r7-2',
    label: '配置漂移',
    category: '环境管理',
    q: '什么是配置漂移（Configuration Drift）？如何避免？',
    a: (
      <div>
        <Paragraph>
          <Text strong>配置漂移</Text>是指环境配置在运行过程中<Text strong>逐渐偏离预期状态</Text>的现象。例如：有人手动修改了服务器配置、运维临时调整了参数忘记恢复、不同环境中同一配置项的值不一致等。
        </Paragraph>
        <Paragraph><Text strong>配置漂移的危害：</Text></Paragraph>
        <ul>
          <li>测试环境通过的功能在生产环境失败（因为配置不一致）</li>
          <li>回滚后配置未恢复到期望状态</li>
          <li>故障排查困难（不知道当前配置是什么）</li>
        </ul>
        <Paragraph><Text strong>避免配置漂移的措施：</Text></Paragraph>
        <ul>
          <li><Text strong>不可变基础设施：</Text>不修改运行中的实例，通过重新部署来变更</li>
          <li><Text strong>声明式配置管理：</Text>使用 K8s YAML、Terraform 等声明式工具，系统自动将实际状态调整到期望状态</li>
          <li><Text strong>配置中心：</Text>所有配置集中管理（如 Consul、Nacos），杜绝手动修改</li>
          <li><Text strong>GitOps：</Text>Git 仓库作为配置的唯一真实来源，任何配置变更都通过 Git PR 进行</li>
          <li><Text strong>定期巡检：</Text>使用工具（如 AWS Config、Open Policy Agent）自动检测配置漂移并告警</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r7-3',
    label: '多环境配置差异管理',
    category: '环境管理',
    q: '同一个应用在不同环境中的配置差异如何管理？',
    a: (
      <div>
        <Paragraph><Text strong>常见方案：</Text></Paragraph>
        <ul>
          <li><Text strong>环境变量注入：</Text>通过 K8s ConfigMap/Secret 或系统环境变量注入环境相关配置，代码中通过环境变量读取</li>
          <li><Text strong>配置中心分层：</Text>公共配置（所有环境相同）放在基础层，环境差异配置按环境覆盖</li>
          <li><Text strong>配置文件模板：</Text>使用模板引擎（如 Helm Chart 的 values.yaml）定义不同环境的配置差异</li>
          <li><Text strong>K8s Namespace 隔离：</Text>每个 Namespace 有独立的 ConfigMap/Secret，通过 Namespace 实现环境隔离</li>
        </ul>
        <Paragraph><Text strong>最佳实践：</Text></Paragraph>
        <ul>
          <li>配置差异<Text strong>最小化</Text>——能相同的配置尽量相同，差异只保留真正需要区分的（如数据库连接、外部 API 地址）</li>
          <li>敏感配置（密码、密钥）使用<Text strong>Secret 管理</Text>，不要明文存储在配置文件中</li>
          <li>配置变更应该有<Text strong>版本控制和审计记录</Text></li>
        </ul>
      </div>
    ),
  },

  /* ---- 8. 配置管理 ---- */
  {
    key: 'r8-1',
    label: '配置与代码分离',
    category: '配置管理',
    q: '为什么配置要和代码分离？在发布系统中配置如何管理？',
    a: (
      <div>
        <Paragraph>
          <Text strong>配置与代码分离</Text>是云原生十二因子应用的核心原则之一（第三因子：配置存储在环境中）。
        </Paragraph>
        <Paragraph><Text strong>为什么需要分离：</Text></Paragraph>
        <ul>
          <li><Text strong>安全性：</Text>数据库密码、API Key 等敏感信息不能硬编码在代码中，更不能提交到 Git 仓库</li>
          <li><Text strong>灵活性：</Text>同一个代码版本可以部署到不同环境（开发/测试/生产），只需调整配置</li>
          <li><Text strong>变更频率不同：</Text>配置变更（如调整日志级别）比代码变更频繁得多，不应该每次配置变更都重新构建发布</li>
          <li><Text strong>权限分离：</Text>配置管理可能需要运维人员操作，代码管理由开发人员操作</li>
        </ul>
        <Paragraph><Text strong>发布系统中配置管理的方式：</Text></Paragraph>
        <ul>
          <li><Text strong>K8s ConfigMap/Secret：</Text>在发布时注入或更新 ConfigMap/Secret</li>
          <li><Text strong>配置中心（Nacos/Consul/Apollo）：</Text>发布系统更新配置中心的配置项，应用动态读取</li>
          <li><Text strong>Helm values：</Text>通过 Helm Chart 的 values.yaml 管理不同环境的配置</li>
          <li><Text strong>环境变量：</Text>在发布时设置环境变量，应用启动时读取</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r8-2',
    label: 'ConfigMap 和 Secret',
    category: '配置管理',
    q: 'K8s 中 ConfigMap 和 Secret 的使用场景和最佳实践？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '用途', configmap: '存储非敏感配置（环境变量、配置文件）', secret: '存储敏感信息（密码、Token、证书）' },
            { key: '2', dimension: '数据编码', configmap: '明文存储', secret: 'Base64 编码（非加密，仅混淆）' },
            { key: '3', dimension: '存储限制', configmap: '单个 ConfigMap 最大 1MB', secret: '单个 Secret 最大 1MB' },
            { key: '4', dimension: '挂载方式', configmap: '环境变量、Volume 挂载', secret: '环境变量、Volume 挂载（tmpfs 内存文件系统）' },
            { key: '5', dimension: '安全性', configmap: '无特殊安全保护', secret: 'etcd 中可配置加密存储，RBAC 控制访问' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: 'ConfigMap', dataIndex: 'configmap', key: 'configmap' },
            { title: 'Secret', dataIndex: 'secret', key: 'secret' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}><Text strong>最佳实践：</Text></Paragraph>
        <ul>
          <li>Secret 的 Base64 只是编码不是加密，<Text strong>不要将 Secret YAML 提交到 Git</Text></li>
          <li>使用外部密钥管理工具（如 Vault、AWS Secrets Manager、Sealed Secrets）管理 Secret</li>
          <li>ConfigMap 变更后，Pod 不会自动重启，需要配合 Reloader 或滚动更新 Pod</li>
          <li>使用 <Text strong>Immutable ConfigMap/Secret</Text>（K8s 1.21+），变更时创建新的而非修改旧的</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r8-3',
    label: '配置变更是否走发布流程',
    category: '配置管理',
    q: '配置变更是否应该走发布流程？为什么？',
    a: (
      <div>
        <Paragraph>
          <Text strong>应该走发布流程，但可以简化。</Text>配置变更虽然不涉及代码变更，但仍然可能影响服务行为，需要被记录和追溯。
        </Paragraph>
        <Paragraph><Text strong>为什么需要走发布流程：</Text></Paragraph>
        <ul>
          <li><Text strong>可追溯性：</Text>谁在什么时间修改了什么配置？出现问题时需要回溯</li>
          <li><Text strong>审批控制：</Text>生产环境的配置变更（如数据库连接、限流阈值）需要审批</li>
          <li><Text strong>回滚能力：</Text>配置变更后发现问题，需要能回滚到上一个配置版本</li>
          <li><Text strong>变更通知：</Text>配置变更后需要通知相关人员</li>
        </ul>
        <Paragraph><Text strong>简化方案：</Text></Paragraph>
        <ul>
          <li>配置变更可以使用<Text strong>快速发布</Text>模式（跳过构建阶段）</li>
          <li>对于非敏感的配置变更（如日志级别调整），可以降低审批级别</li>
          <li>使用 GitOps 方式管理配置，配置变更通过 Git PR 进行，自动触发配置更新</li>
        </ul>
      </div>
    ),
  },

  /* ---- 9. 审批流程 ---- */
  {
    key: 'r9-1',
    label: '发布审批的作用',
    category: '审批流程',
    q: '发布审批的作用是什么？哪些环境需要审批？',
    a: (
      <div>
        <Paragraph>
          <Text strong>发布审批</Text>是发布系统的重要安全控制机制，其核心作用是<Text strong>「在变更进入生产环境前，确保有足够的人审核和确认变更的风险」</Text>。
        </Paragraph>
        <Paragraph><Text strong>审批的具体作用：</Text></Paragraph>
        <ul>
          <li><Text strong>风险控制：</Text>确保发布的变更已经过充分测试和验证</li>
          <li><Text strong>责任明确：</Text>审批人确认后，变更的责任链条清晰</li>
          <li><Text strong>协作沟通：</Text>审批过程让相关方知晓即将发生的变更</li>
          <li><Text strong>合规要求：</Text>满足 ISO 27001、SOC 2 等合规审计要求</li>
        </ul>
        <Paragraph><Text strong>环境审批策略：</Text></Paragraph>
        <ul>
          <li><Text strong>开发环境：</Text>通常不需要审批，开发者自主部署</li>
          <li><Text strong>测试环境：</Text>通常不需要审批，自动化测试通过即可</li>
          <li><Text strong>预发环境：</Text>建议审批，作为生产前的最后检查</li>
          <li><Text strong>生产环境：</Text>必须审批，通常需要技术负责人或值班运维审批</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r9-2',
    label: '审批与自动化平衡',
    category: '审批流程',
    q: '审批流程和自动化发布如何平衡？紧急情况如何绕过审批？',
    a: (
      <div>
        <Paragraph>
          <Text strong>审批与自动化的平衡</Text>是发布系统设计中的经典矛盾：审批太严格会拖慢发布速度，审批太宽松会增加风险。
        </Paragraph>
        <Paragraph><Text strong>平衡策略：</Text></Paragraph>
        <ul>
          <li><Text strong>分级审批：</Text>低风险变更（配置调整、小 Bug 修复）→ 自动审批；中风险变更（功能新增）→ 技术负责人审批；高风险变更（架构变更、数据库迁移）→ 多人审批</li>
          <li><Text strong>自动化代替审批：</Text>通过完善的自动化测试，让「测试通过」代替「人工审批」</li>
          <li><Text strong>变更窗口：</Text>设置变更窗口（如非高峰时段），窗口内的发布自动审批</li>
        </ul>
        <Paragraph><Text strong>紧急情况绕过审批：</Text></Paragraph>
        <ul>
          <li><Text strong>紧急发布通道：</Text>提供「紧急发布」功能，绕过常规审批流程，但需要事后补审批</li>
          <li><Text strong>事后审计：</Text>紧急发布的记录会被标记，事后进行审计和复盘</li>
          <li><Text strong>限制范围：</Text>紧急发布仅限于修复严重问题，不允许在紧急通道中上线新功能</li>
          <li><Text strong>通知机制：</Text>紧急发布时自动通知所有相关人员，确保团队知晓</li>
        </ul>
      </div>
    ),
  },

  /* ---- 10. 回滚机制 ---- */
  {
    key: 'r10-1',
    label: '回滚策略对比',
    category: '回滚机制',
    q: '回滚有哪些策略？滚动回滚、蓝绿切回、灰度回滚各有什么特点？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', strategy: '滚动回滚', desc: '反向滚动更新，逐步替换回旧版本', speed: '分钟级（逐批替换）', suitable: '滚动更新部署的场景', feature: '回滚过程仍保持服务可用' },
            { key: '2', strategy: '蓝绿切回', desc: '切换路由回旧环境', speed: '秒级', suitable: '蓝绿部署的场景', feature: '回滚速度最快，旧环境保持运行' },
            { key: '3', strategy: '灰度回滚', desc: '将灰度实例恢复到旧版本', speed: '秒级', suitable: '灰度发布阶段发现问题', feature: '仅影响灰度范围内的用户' },
            { key: '4', strategy: '版本指定回滚', desc: '回滚到任意历史版本（非上一个）', speed: '同滚动回滚', suitable: '多个版本后发现历史版本更稳定', feature: '需要保留历史版本制品' },
          ]}
          columns={[
            { title: '策略', dataIndex: 'strategy', key: 'strategy' },
            { title: '描述', dataIndex: 'desc', key: 'desc' },
            { title: '速度', dataIndex: 'speed', key: 'speed' },
            { title: '适用场景', dataIndex: 'suitable', key: 'suitable' },
            { title: '特点', dataIndex: 'feature', key: 'feature' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
      </div>
    ),
  },
  {
    key: 'r10-2',
    label: '回滚的数据兼容性问题',
    category: '回滚机制',
    q: '回滚可能遇到哪些问题？数据兼容性怎么处理？',
    a: (
      <div>
        <Paragraph><Text strong>回滚可能遇到的问题：</Text></Paragraph>
        <ul>
          <li><Text strong>数据兼容性：</Text>新版本可能写入了新格式的数据，旧版本代码无法读取——这是回滚中最常见也最棘手的问题</li>
          <li><Text strong>级联影响：</Text>多个服务同时发布，回滚一个服务可能影响其他服务</li>
          <li><Text strong>配置漂移：</Text>回滚后配置可能与旧版本期望不一致</li>
          <li><Text strong>依赖服务版本：</Text>回滚的服务可能依赖了新版本的 API，旧版本不兼容</li>
          <li><Text strong>缓存不一致：</Text>Redis/本地缓存中可能有新版本的数据，回滚后缓存未清理</li>
        </ul>
        <Paragraph><Text strong>数据兼容性处理策略：</Text></Paragraph>
        <ul>
          <li><Text strong>向前兼容设计：</Text>新版本代码必须兼容旧版本数据格式——这是根本解决方案</li>
          <li><Text strong>分阶段变更：</Text>数据库 Schema 变更分阶段执行，每阶段都兼容上一个版本</li>
          <li><Text strong>扩展字段：</Text>使用 JSON 字段存储新增数据，避免 Schema 变更</li>
          <li><Text strong>数据回滚：</Text>对关键数据变更提供反向迁移脚本</li>
          <li><Text strong>只读模式：</Text>回滚后先以只读模式运行，清理兼容数据后再恢复写入</li>
        </ul>
      </div>
    ),
  },

  /* ---- 11. 监控与可观测性 ---- */
  {
    key: 'r11-1',
    label: '发布过程监控指标',
    category: '监控与可观测性',
    q: '发布过程中应该监控哪些指标？如何判断发布是否成功？',
    a: (
      <div>
        <Paragraph><Text strong>发布过程中需要监控的关键指标：</Text></Paragraph>
        <Table
          dataSource={[
            { key: '1', category: '服务健康', metrics: '错误率（5xx/4xx）、请求成功率', threshold: '错误率不超过基线 ±10%' },
            { key: '2', category: '性能指标', metrics: '延迟（P50/P95/P99）、吞吐量 QPS', threshold: 'P99 延迟不超过基线 ±20%' },
            { key: '3', category: '资源使用', metrics: 'CPU 使用率、内存使用率、磁盘 IO、网络 IO', threshold: '不超过告警阈值' },
            { key: '4', category: '业务指标', metrics: '订单量、转化率、登录成功率等核心业务指标', threshold: '不低于基线 ±5%' },
            { key: '5', category: '部署状态', metrics: 'Pod 就绪数、滚动更新进度、就绪探针状态', threshold: '100% 就绪' },
            { key: '6', category: '应用日志', metrics: '错误日志数量、异常堆栈出现频率', threshold: '无新增异常类型' },
          ]}
          columns={[
            { title: '类别', dataIndex: 'category', key: 'category', width: 100 },
            { title: '指标', dataIndex: 'metrics', key: 'metrics' },
            { title: '判断标准', dataIndex: 'threshold', key: 'threshold' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>判断发布成功的标准：</Text>
          <ul>
            <li>所有核心指标在发布后<Text strong>5-10 分钟内</Text>保持稳定</li>
            <li>灰度发布：每个灰度阶段都观察足够时间，指标正常再继续</li>
            <li>使用<Text strong>自动化判定</Text>：系统自动对比新旧版本的指标，异常时自动触发回滚</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r11-2',
    label: '可观测性三大支柱',
    category: '监控与可观测性',
    q: '可观测性三大支柱（Logs/Metrics/Traces）在发布系统中如何应用？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', pillar: '日志 Logs', desc: '不可变的事件记录，包含时间戳和上下文', usage: '发布过程中的错误日志、业务异常日志', tool: 'ELK / Loki / Splunk' },
            { key: '2', pillar: '指标 Metrics', desc: '可聚合的数值型数据，具有时间维度', usage: '错误率、延迟、CPU/内存、QPS 等聚合指标', tool: 'Prometheus + Grafana / Datadog' },
            { key: '3', pillar: '链路追踪 Traces', desc: '请求在分布式系统中的完整调用链', usage: '定位发布后性能退化的具体环节', tool: 'Jaeger / Zipkin / SkyWalking' },
          ]}
          columns={[
            { title: '支柱', dataIndex: 'pillar', key: 'pillar', width: 100 },
            { title: '描述', dataIndex: 'desc', key: 'desc' },
            { title: '在发布中的应用', dataIndex: 'usage', key: 'usage' },
            { title: '常用工具', dataIndex: 'tool', key: 'tool', width: 180 },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>发布系统中的协同应用：</Text>
          <ul>
            <li><Text strong>发布前：</Text>建立基线指标快照，用于发布后对比</li>
            <li><Text strong>发布中：</Text>实时监控 Metrics 的变化趋势，异常时触发告警</li>
            <li><Text strong>发布后：</Text>通过 Traces 分析性能变化的原因，通过 Logs 排查具体错误</li>
            <li><Text strong>回滚决策：</Text>三大支柱的数据共同支撑回滚决策——Metrics 发现异常 → Traces 定位环节 → Logs 确认根因</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },

  /* ---- 12. 安全与合规 ---- */
  {
    key: 'r12-1',
    label: '发布系统安全考虑',
    category: '安全与合规',
    q: '发布系统需要考虑哪些安全方面？权限、审计、密钥管理怎么做？',
    a: (
      <div>
        <Paragraph><Text strong>发布系统的安全考虑：</Text></Paragraph>
        <ul>
          <li><Text strong>权限控制（RBAC）：</Text>谁可以发布什么应用到什么环境？按角色（开发者/运维/管理员）和资源（应用/环境）进行权限控制</li>
          <li><Text strong>操作审计：</Text>记录所有发布操作（谁、什么时间、做了什么、结果如何），满足合规审计要求</li>
          <li><Text strong>密钥管理：</Text>部署密钥、数据库密码、API Token 等敏感信息不能明文存储或传输</li>
          <li><Text strong>制品安全：</Text>制品签名验证、镜像漏洞扫描、供应链安全</li>
          <li><Text strong>网络安全：</Text>发布系统与目标主机之间的通信加密（SSH/TLS）</li>
          <li><Text strong>审批流程：</Text>关键操作需要审批，防止误操作或恶意操作</li>
        </ul>
        <Paragraph><Text strong>密钥管理最佳实践：</Text></Paragraph>
        <ul>
          <li>使用外部密钥管理系统（Vault、AWS Secrets Manager）</li>
          <li>密钥不写入代码或配置文件，通过环境变量注入或 Secret 挂载</li>
          <li>密钥定期轮换，发布系统支持自动更新密钥</li>
          <li>部署密钥与个人密钥分离，使用专门的部署密钥</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'r12-2',
    label: '发布操作审计追溯',
    category: '安全与合规',
    q: '如何实现发布操作的审计追溯？谁在什么时间做了什么操作？',
    a: (
      <div>
        <Paragraph>
          <Text strong>审计追溯</Text>是发布系统合规性的核心要求，需要回答「谁在什么时间对什么应用做了什么操作，结果如何」。
        </Paragraph>
        <Paragraph><Text strong>实现方案：</Text></Paragraph>
        <ul>
          <li><Text strong>操作日志：</Text>每次发布操作都记录一条审计日志，包含：操作人、操作时间、操作类型（创建/审批/执行/回滚）、目标应用、目标环境、操作结果</li>
          <li><Text strong>不可篡改存储：</Text>审计日志存储在不可篡改的存储中（如 Append-only 日志、区块链审计），防止被篡改</li>
          <li><Text strong>发布单关联：</Text>所有操作都关联到发布单，形成完整的操作链</li>
          <li><Text strong>变更快照：</Text>记录发布前后的配置、版本快照，便于对比</li>
          <li><Text strong>导出报表：</Text>支持按时间范围、应用、环境等维度导出审计报告</li>
        </ul>
        <Paragraph>
          <Text strong>面试加分：</Text>能提到「审计日志的不可篡改性」和「与 SIEM 系统集成」，体现安全合规深度。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 13. K8s 发布 ---- */
  {
    key: 'r13-1',
    label: 'K8s Deployment 滚动更新原理',
    category: 'K8s 发布',
    q: 'K8s Deployment 滚动更新的原理？maxSurge 和 maxUnavailable 的作用？',
    a: (
      <div>
        <Paragraph>
          <Text strong>K8s Deployment 滚动更新原理：</Text>
        </Paragraph>
        <ol>
          <li>用户修改 Deployment 的 Pod Template（通常是镜像版本）</li>
          <li>Deployment Controller 检测到变更，创建新的 ReplicaSet</li>
          <li>根据 maxSurge 限制，逐步创建新 ReplicaSet 的 Pod</li>
          <li>新 Pod 通过 Readiness Probe 后，加入 Service 的 Endpoint</li>
          <li>根据 maxUnavailable 限制，逐步缩容旧 ReplicaSet 的 Pod</li>
          <li>重复以上步骤，直到所有 Pod 更新完成</li>
        </ol>
        <Paragraph>
          <Text strong>maxSurge：</Text>滚动更新时<Text strong>允许超出期望副本数</Text>的最大实例数。例如期望 10 副本、maxSurge=2，则最多可以有 12 个实例同时运行。增大此值可以加快更新速度，但会消耗更多资源。
        </Paragraph>
        <Paragraph>
          <Text strong>maxUnavailable：</Text>滚动更新时<Text strong>允许多少个实例不可用</Text>。例如期望 10 副本、maxUnavailable=1，则至少保持 9 个实例可用。减小此值可以提高服务可用性，但会减慢更新速度。
        </Paragraph>
        <Paragraph>
          <Text strong>关键关系：</Text>maxSurge 和 maxUnavailable 共同决定了更新速度和服务可用性的平衡。两者都不能设为 0（除非使用 Recreate 策略）。可以设置为绝对数或百分比。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r13-2',
    label: 'Deployment/StatefulSet/DaemonSet 发布差异',
    category: 'K8s 发布',
    q: 'Deployment、StatefulSet、DaemonSet 的发布策略有什么不同？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '适用场景', deploy: '无状态应用（Web 服务、API）', stateful: '有状态应用（数据库、消息队列）', daemon: '每个节点运行一个实例（日志收集、监控 Agent）' },
            { key: '2', dimension: '更新策略', deploy: 'RollingUpdate / Recreate', stateful: 'RollingUpdate / OnDelete', daemon: 'RollingUpdate / OnDelete' },
            { key: '3', dimension: '更新顺序', deploy: '随机，与 Pod 名称无关', stateful: '逆序更新（从最大序号开始）', daemon: '可配置 maxUnavailable，逐节点更新' },
            { key: '4', dimension: '回滚方式', deploy: 'kubectl rollout undo', stateful: 'kubectl rollout undo（需手动管理 PVC）', daemon: 'kubectl rollout undo' },
            { key: '5', dimension: '网络标识', deploy: 'Pod 名称随机，IP 可变', stateful: 'Pod 名称固定（如 app-0, app-1）', daemon: 'Pod 名称包含节点名' },
            { key: '6', dimension: '存储', deploy: '通常使用共享存储或无状态', stateful: '每个 Pod 有独立的 PVC', daemon: '通常使用 hostPath 或节点本地存储' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: 'Deployment', dataIndex: 'deploy', key: 'deploy' },
            { title: 'StatefulSet', dataIndex: 'stateful', key: 'stateful' },
            { title: 'DaemonSet', dataIndex: 'daemon', key: 'daemon' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>StatefulSet 发布注意事项：</Text>StatefulSet 的更新是<Text strong>逆序逐个</Text>进行的，这保证了有状态服务的数据一致性。更新时需要注意 PVC 的生命周期——PVC 不会随 Pod 删除而删除，需要手动管理。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r13-3',
    label: 'Service Mesh 在发布中的作用',
    category: 'K8s 发布',
    q: 'Service Mesh（Istio）在发布中的作用是什么？',
    a: (
      <div>
        <Paragraph>
          <Text strong>Service Mesh</Text> 在发布系统中扮演<Text strong>「流量控制层」</Text>的角色，提供了比 K8s Service 更精细的流量管理能力。
        </Paragraph>
        <Paragraph><Text strong>在发布中的核心作用：</Text></Paragraph>
        <ul>
          <li><Text strong>精确流量分割：</Text>通过 VirtualService 的 weight 字段，精确控制灰度比例（如 5%→20%→50%→100%），粒度可达 1%</li>
          <li><Text strong>基于请求特征的灰度：</Text>根据 HTTP Header（如 User-Agent、Cookie）、用户 ID 等特征路由流量，实现用户级别的灰度</li>
          <li><Text strong>全链路灰度：</Text>在请求 Header 中传递灰度标签，确保灰度请求在整个微服务调用链中都走灰度版本</li>
          <li><Text strong>流量镜像：</Text>将生产流量复制一份到新版本，用于影子部署测试</li>
          <li><Text strong>故障注入：</Text>模拟延迟、错误等故障场景，验证服务的容错能力</li>
          <li><Text strong>可观测性增强：</Text>自动收集 Metrics、Traces，无需修改应用代码</li>
        </ul>
        <Paragraph>
          <Text strong>Istio 在灰度发布中的典型配置：</Text>使用 DestinationRule 定义版本子集（v1、v2），使用 VirtualService 配置权重路由。当需要调整灰度比例时，只需修改 VirtualService 的 weight 值，无需重新部署。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 14. 灰度/实验 ---- */
  {
    key: 'r14-1',
    label: '灰度发布和 A/B 测试的区别',
    category: '灰度/实验',
    q: '灰度发布和 A/B 测试的本质区别是什么？',
    a: (
      <div>
        <Table
          dataSource={[
            { key: '1', dimension: '目的', canary: '降低部署风险，验证新版本稳定性', ab: '验证功能效果，比较哪个版本更好' },
            { key: '2', dimension: '本质', canary: '运维策略', ab: '产品实验' },
            { key: '3', dimension: '持续时间', canary: '数小时', ab: '数天到数周' },
            { key: '4', dimension: '结束方式', canary: '稳定后全量切换', ab: '根据实验数据决定胜负' },
            { key: '5', dimension: '流量分配', canary: '从小比例开始逐步放大', ab: '通常 50/50 分流' },
            { key: '6', dimension: '关注指标', canary: '错误率、延迟、资源消耗', ab: '转化率、点击率、留存率等业务指标' },
            { key: '7', dimension: '最终状态', canary: '新版本 100% 上线', ab: '可能保留旧版本，也可能全量新版本' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '灰度发布', dataIndex: 'canary', key: 'canary' },
            { title: 'A/B 测试', dataIndex: 'ab', key: 'ab' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>记忆技巧：</Text>灰度发布是「金丝雀探路」，A/B 测试是「赛马机制」。两者可以结合使用——在灰度发布的过程中同时进行 A/B 测试对比数据。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r14-2',
    label: 'Feature Flag 系统设计',
    category: '灰度/实验',
    q: 'Feature Flag 在发布系统中扮演什么角色？如何设计一个 Feature Flag 系统？',
    a: (
      <div>
        <Paragraph>
          <Text strong>Feature Flag</Text> 在发布系统中扮演<Text strong>「发布与部署的解耦器」</Text>角色。它使得代码部署和功能上线成为两个独立的事件——代码可以部署到生产环境，但功能通过开关控制是否对用户可见。
        </Paragraph>
        <Paragraph><Text strong>Feature Flag 系统的设计要点：</Text></Paragraph>
        <ul>
          <li><Text strong>配置中心化：</Text>所有 Flag 集中管理，支持实时更新，无需重启服务</li>
          <li><Text strong>多维度目标：</Text>支持按用户 ID、IP 段、地域、用户属性、随机百分比等维度控制</li>
          <li><Text strong>渐进式放量：</Text>支持 0%→10%→50%→100% 的逐步放量策略</li>
          <li><Text strong>生命周期管理：</Text>Flag 有创建、激活、全量、清理的生命周期，过期 Flag 自动告警</li>
          <li><Text strong>审计日志：</Text>记录 Flag 的创建、修改、删除历史</li>
          <li><Text strong>性能保障：</Text>Flag 评估必须在毫秒级完成，不能成为性能瓶颈</li>
          <li><Text strong>降级策略：</Text>当 Flag 服务不可用时，应用应使用安全的默认值</li>
        </ul>
        <Paragraph>
          <Text strong>Flag 的类型：</Text>
          <ul>
            <li>Release Flag（发布开关）：控制功能上线的灰度，短期存在</li>
            <li>Experiment Flag（实验开关）：A/B 测试分组，短期存在</li>
            <li>Ops Flag（运维开关）：控制系统行为（降级/熔断），长期存在</li>
            <li>Permission Flag（权限开关）：控制功能可见性，长期存在</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },

  /* ---- 15. 发布系统架构 ---- */
  {
    key: 'r15-1',
    label: '高可用发布系统设计',
    category: '发布系统架构',
    q: '如何设计一个高可用的发布系统？',
    a: (
      <div>
        <Paragraph><Text strong>高可用发布系统的核心设计原则：</Text></Paragraph>
        <ul>
          <li><Text strong>发布系统自身高可用：</Text>发布系统本身需要多副本部署，支持故障转移。如果发布系统挂了，所有发布操作都无法进行</li>
          <li><Text strong>幂等性：</Text>每个发布操作都是幂等的，重复执行不会产生副作用</li>
          <li><Text strong>可回滚：</Text>任何发布操作都有对应的回滚方案，确保出错时可以快速恢复</li>
          <li><Text strong>渐进式：</Text>支持灰度、蓝绿等渐进式部署策略，降低单次发布的风险</li>
          <li><Text strong>可观测：</Text>完整的监控、日志、告警体系，发布状态实时可见</li>
          <li><Text strong>审批流：</Text>关键环境需要审批控制，避免误操作</li>
          <li><Text strong>隔离性：</Text>不同应用、不同环境的发布互不影响</li>
          <li><Text strong>逃生通道：</Text>保留手动发布的能力，作为自动化系统的最后保障</li>
        </ul>
        <Paragraph>
          <Text strong>架构设计要点：</Text>发布系统通常采用<Text strong>微服务架构</Text>，将发布引擎、审批引擎、通知引擎等模块解耦。核心数据（发布单、版本记录）存储在数据库中，确保发布系统重启后可以恢复状态。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r15-2',
    label: '非功能性需求',
    category: '发布系统架构',
    q: '发布系统的非功能性需求有哪些？',
    a: (
      <div>
        <Paragraph><Text strong>非功能性需求：</Text></Paragraph>
        <ul>
          <li><Text strong>可用性（Availability）：</Text>发布系统本身必须高可用，99.9%+ 的可用性</li>
          <li><Text strong>性能（Performance）：</Text>支持大规模并发发布（如同时发布 1000+ 实例），发布操作延迟在可接受范围内</li>
          <li><Text strong>扩展性（Scalability）：</Text>支持新增发布策略、部署模式、环境类型、部署目标类型</li>
          <li><Text strong>安全性（Security）：</Text>权限控制（RBAC）、操作审计、敏感信息加密、供应链安全</li>
          <li><Text strong>可观测性（Observability）：</Text>发布状态实时展示、发布历史可追溯、失败原因可分析</li>
          <li><Text strong>容错性（Fault Tolerance）：</Text>部分失败不影响整体、自动重试、手动干预能力</li>
          <li><Text strong>合规性（Compliance）：</Text>符合审批流程、变更管理规范、审计要求</li>
          <li><Text strong>易用性（Usability）：</Text>Web 界面清晰、操作流程简单、学习成本低</li>
        </ul>
        <Paragraph>
          <Text type="secondary">面试加分：能按优先级排序这些需求，并解释为什么某些需求比其他需求更重要。</Text>
        </Paragraph>
      </div>
    ),
  },

  /* ---- 16. DORA/DevOps ---- */
  {
    key: 'r16-1',
    label: 'DORA 四大指标',
    category: 'DORA/DevOps',
    q: 'DORA 四大指标是什么？每个指标的含义和优秀标准？',
    a: (
      <div>
        <Paragraph>
          <Text strong>DORA（DevOps Research and Assessment）</Text> 是 Google 提出的 DevOps 效能评估框架，包含四个核心指标：
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', metric: '部署频率 Deployment Frequency', desc: '多久发布一次', elite: '每天多次（On-demand）', good: '每周一次到每月一次', poor: '每月一次到每半年一次' },
            { key: '2', metric: '变更前置时间 Lead Time for Changes', desc: '从代码提交到生产上线的时间', elite: '小于 1 小时', good: '1 天到 1 周', poor: '1 周到 1 个月' },
            { key: '3', metric: '恢复时间 MTTR', desc: '从故障发生到恢复服务的时间', elite: '小于 1 小时', good: '小于 1 天', poor: '1 天到 1 周' },
            { key: '4', metric: '变更失败率 Change Failure Rate', desc: '发布导致服务降级或故障的比例', elite: '0-15%', good: '16-30%', poor: '31-45%' },
          ]}
          columns={[
            { title: '指标', dataIndex: 'metric', key: 'metric' },
            { title: '说明', dataIndex: 'desc', key: 'desc' },
            { title: '精英级', dataIndex: 'elite', key: 'elite' },
            { title: '良好', dataIndex: 'good', key: 'good' },
            { title: '需改进', dataIndex: 'poor', key: 'poor' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>关键理解：</Text>DORA 指标不是孤立存在的——高的部署频率和低的变更失败率通常同时出现（精英团队），这反驳了「快速发布必然带来更多故障」的传统观念。良好的发布系统设计可以同时提升频率和降低失败率。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'r16-2',
    label: '通过发布系统优化 DORA 指标',
    category: 'DORA/DevOps',
    q: '如何通过发布系统的设计来优化 DORA 指标？',
    a: (
      <div>
        <Paragraph><Text strong>针对每个指标的系统设计优化：</Text></Paragraph>
        <ul>
          <li><Text strong>提升部署频率：</Text>简化发布流程、自动化审批、支持快速发布模式、并行发布能力</li>
          <li><Text strong>缩短变更前置时间：</Text>优化 CI/CD 流水线速度（并行构建、缓存、增量构建）、减少审批环节、快速发布模式</li>
          <li><Text strong>缩短恢复时间（MTTR）：</Text>一键回滚、蓝绿部署秒级回滚、灰度发布即时回滚、自动化回滚触发</li>
          <li><Text strong>降低变更失败率：</Text>灰度发布降低影响范围、蓝绿部署提供即时回滚、完善的发布前验证、自动化测试门禁</li>
        </ul>
        <Paragraph>
          <Text strong>核心思路：</Text>发布系统不是「执行部署的工具」，而是<Text strong>「降低发布风险的平台」</Text>。通过提供多样化的部署策略、完善的审批和回滚机制、全面的监控可观测性，发布系统可以从根本上降低发布的风险和成本，从而鼓励团队更频繁地发布。
        </Paragraph>
      </div>
    ),
  },
];

/* =============================================================================
 * 二、进阶面试题（~15道，3类）
 * ============================================================================= */

export const advancedQuestions = [
  /* ---- 技术深入 ---- */
  {
    key: 'a1-1',
    label: '数据库迁移与 Schema 变更',
    category: '技术深入',
    q: '发布过程中数据库迁移和 Schema 变更如何处理？',
    a: (
      <div>
        <Paragraph>
          这是发布系统中最具挑战性的问题之一。<Text strong>核心原则：数据库变更必须与代码变更解耦，确保新旧版本都能正常工作。</Text>
        </Paragraph>
        <Paragraph><Text strong>推荐的分阶段方案：</Text></Paragraph>
        <ol>
          <li><Text strong>阶段一（兼容性变更）：</Text>先执行向下兼容的 Schema 变更——新增字段（允许 NULL 或有默认值）、新建表。此时旧代码完全不受影响，新代码的部署可以稍后进行。</li>
          <li><Text strong>阶段二（代码部署）：</Text>部署新版本代码，新代码使用新字段/新表。此时新旧代码都能正常工作，因为 Schema 是向下兼容的。</li>
          <li><Text strong>阶段三（清理阶段）：</Text>确认新版本稳定运行后，执行清理——删除废弃字段、删除废弃表。此阶段需要确保旧代码已经完全下线。</li>
        </ol>
        <Paragraph><Text strong>无法向下兼容的情况：</Text></Paragraph>
        <ul>
          <li>使用 Feature Flag 控制新旧代码路径，数据库变更在 Flag 关闭时不影响</li>
          <li>使用双写方案——同时写入新旧两种数据结构，确保回滚时数据不丢失</li>
          <li>使用数据库视图隔离新旧 Schema</li>
        </ul>
        <Paragraph>
          <Text strong>关键工具：</Text>Flyway、Liquibase 等数据库迁移工具，支持版本化管理和回滚。迁移工具应集成到 CI/CD 流水线中，在部署前自动执行。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a1-2',
    label: 'K8s 滚动更新安全保障',
    category: '技术深入',
    q: 'K8s 中 Deployment 滚动更新的原理，如何保障发布安全？',
    a: (
      <div>
        <Paragraph>
          <Text strong>K8s Deployment 滚动更新的核心机制：</Text>Deployment Controller 通过创建新 ReplicaSet 并逐步调整新旧 ReplicaSet 的副本数来实现滚动更新。
        </Paragraph>
        <Paragraph><Text strong>安全保障措施：</Text></Paragraph>
        <ul>
          <li><Text strong>PodDisruptionBudget（PDB）：</Text>限制自愿中断时最少可用的 Pod 数量。例如 PDB 设置 minAvailable=8，则 K8s 不会同时驱逐超过 2 个 Pod。这是防止「发布风暴」的关键保护。</li>
          <li><Text strong>Readiness Probe：</Text>确保新 Pod 真正就绪后才接收流量。不只是「进程启动了」，而是「应用可以处理请求了」。常见的实践是检查 HTTP 健康端点、数据库连接等。</li>
          <li><Text strong>Progress Deadline：</Text>设置滚动更新的最大时间限制（progressDeadlineSeconds）。如果更新在规定时间内未完成，Deployment 会被标记为失败，避免无限期卡住。</li>
          <li><Text strong>Revision History：</Text>保留历史 ReplicaSet（默认 10 个），支持快速回滚到任意历史版本。</li>
          <li><Text strong>minReadySeconds：</Text>新 Pod 就绪后等待的最小时间，防止 Pod 刚就绪就接收大量流量导致过载。</li>
        </ul>
        <Paragraph>
          <Text strong>发布安全的最佳实践：</Text>
          <ul>
            <li>先部署到预发环境验证，再部署到生产环境</li>
            <li>使用 Kubectl rollout status 监控发布进度</li>
            <li>设置合理的 maxSurge 和 maxUnavailable 值，避免过快或过慢</li>
            <li>配置发布通知（Slack/钉钉），发布完成后自动通知</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a1-3',
    label: '发布后发现严重性能问题',
    category: '技术深入',
    q: '发布过程中如果发现新版本有严重性能问题，如何处理？',
    a: (
      <div>
        <Paragraph><Text strong>分场景处理：</Text></Paragraph>
        <ul>
          <li><Text strong>灰度阶段：</Text>立即停止灰度扩大，将灰度 Pod 副本数缩为 0（或回滚镜像），问题影响范围可控</li>
          <li><Text strong>蓝绿切换后：</Text>立即切换回旧环境（蓝绿部署的核心优势），秒级恢复</li>
          <li><Text strong>滚动更新中：</Text>暂停滚动更新，使用 kubectl rollout undo 回滚到上一个版本</li>
          <li><Text strong>全量发布后（最坏情况）：</Text>启动紧急回滚流程，创建回滚发布单，可能需要走紧急审批通道</li>
        </ul>
        <Paragraph><Text strong>处理流程：</Text></Paragraph>
        <ol>
          <li><Text strong>止血（1-5 分钟）：</Text>立即回滚，恢复服务。不要先分析问题，先恢复服务。</li>
          <li><Text strong>保留现场（并行）：</Text>保留问题版本的日志、监控数据、堆栈信息，用于后续分析</li>
          <li><Text strong>分析根因（事后）：</Text>分析性能问题的根本原因，确定是代码问题还是配置问题</li>
          <li><Text strong>修复验证（修复后）：</Text>在预发环境充分验证修复后，再重新发布</li>
        </ol>
        <Paragraph>
          <Text strong>关键原则：</Text>「先止血，再分析」。不要因为想保留现场而延迟回滚——每多一秒，就有更多用户受影响。可以先回滚，同时通过日志系统保留现场信息。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a1-4',
    label: '多微服务协调发布',
    category: '技术深入',
    q: '多个微服务同时发布，如何协调发布顺序和依赖关系？',
    a: (
      <div>
        <Paragraph>
          <Text strong>多微服务协调发布</Text>是微服务架构中的核心挑战。核心原则是：<Text strong>被依赖的服务先发布，依赖方后发布；所有服务保持 API 向前兼容。</Text>
        </Paragraph>
        <Paragraph><Text strong>协调策略：</Text></Paragraph>
        <ul>
          <li><Text strong>依赖拓扑排序：</Text>分析服务间的调用依赖关系，构建 DAG，按拓扑顺序发布</li>
          <li><Text strong>API 版本化：</Text>每个服务支持多个 API 版本，新旧版本并存，降低发布顺序的耦合</li>
          <li><Text strong>契约测试：</Text>在发布前运行契约测试，确保新版本服务与依赖方的契约兼容</li>
          <li><Text strong>发布编排：</Text>发布系统支持「发布编排」功能，定义多服务的发布顺序和条件</li>
          <li><Text strong>回滚联动：</Text>如果一个服务发布失败，自动回滚依赖它的服务</li>
        </ul>
        <Paragraph><Text strong>最佳实践：</Text></Paragraph>
        <ul>
          <li>尽量<Text strong>避免多服务同时发布</Text>——将变更拆分为独立的、可独立发布的单元</li>
          <li>使用<Text strong>Feature Flag</Text>解耦服务间的发布依赖</li>
          <li>每个服务都应该<Text strong>独立可发布</Text>，不依赖其他服务的发布状态</li>
        </ul>
      </div>
    ),
  },
  {
    key: 'a1-5',
    label: '发布系统幂等性',
    category: '技术深入',
    q: '发布系统的幂等性如何保证？同一发布请求被执行两次怎么办？',
    a: (
      <div>
        <Paragraph>
          <Text strong>幂等性</Text>是指同一个操作执行一次和执行多次，产生的结果相同。发布系统的幂等性是系统可靠性的基础。
        </Paragraph>
        <Paragraph><Text strong>幂等性保证策略：</Text></Paragraph>
        <ul>
          <li><Text strong>幂等键设计：</Text>每次发布请求携带唯一幂等键（如 UUID），系统通过幂等键去重——相同幂等键的请求只执行一次</li>
          <li><Text strong>状态机设计：</Text>发布单的状态流转是严格的状态机（如：待审批 → 审批中 → 待执行 → 执行中 → 成功），不允许从未定义的状态转换</li>
          <li><Text strong>数据库唯一约束：</Text>对关键字段（如发布单编号 + 尝试次数）添加唯一约束，防止重复插入</li>
          <li><Text strong>分布式锁：</Text>在执行发布前获取分布式锁，确保同一时间只有一个进程在执行该发布</li>
          <li><Text strong>发布结果检查：</Text>在执行前检查目标环境是否已经运行了目标版本，如果已运行则跳过</li>
        </ul>
        <Paragraph>
          <Text strong>如果所有手段都失效了：</Text>即使幂等性被破坏，部署操作本身也应该是幂等的——K8s 的声明式 API 天然支持幂等（同样的 Deployment YAML 执行多次结果相同），SSH 部署脚本应该检查当前状态再决定是否执行。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 真实项目经验（Spug 经验） ---- */
  {
    key: 'a2-1',
    label: '发布系统技术架构设计',
    category: '真实项目经验',
    q: '你之前的发布系统是怎么设计的？技术架构是怎样的？',
    a: (
      <div>
        <Paragraph>
          <Text strong>技术架构：</Text>基于 Spug 开源项目，采用 <Text strong>Python Django + React + Ant Design</Text> 技术栈。后端提供 REST API，前端提供 Web 管理界面，通过 SSH 协议连接目标主机执行部署操作。
        </Paragraph>
        <Paragraph><Text strong>核心模块：</Text></Paragraph>
        <ul>
          <li><Text strong>发布管理模块：</Text>创建发布单、选择发布模式、指定目标主机、执行发布、状态跟踪</li>
          <li><Text strong>主机管理模块：</Text>主机注册、分组管理、SSH 连接管理</li>
          <li><Text strong>应用管理模块：</Text>应用配置、部署路径、启动脚本、环境变量</li>
          <li><Text strong>权限管理模块：</Text>基于角色的权限控制（RBAC），控制用户对不同应用和环境的操作权限</li>
          <li><Text strong>审批模块：</Text>生产环境发布需要审批，支持多级审批</li>
          <li><Text strong>历史记录模块：</Text>发布历史查询、版本追溯、回滚操作</li>
        </ul>
        <Paragraph>
          <Text strong>架构特点：</Text>轻量级、Agentless 架构（通过 SSH 直接管理，无需在目标主机安装 Agent），适合中小规模的主机管理（数十到数百台）。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a2-2',
    label: '权限管理经验',
    category: '真实项目经验',
    q: '你们之前怎么处理权限的？遇到过什么坑？后来怎么优化的？',
    a: (
      <div>
        <Paragraph>
          <Text strong>权限模型演进 V1 → V2：</Text>
        </Paragraph>
        <Paragraph>
          <Text strong>V1 版本（简单角色模型）：</Text>用户 → 角色（管理员/开发者/只读），权限在代码中硬编码。这个方案的问题是粒度太粗——无法实现「开发者 A 只能发布应用 X 到测试环境，不能发布到生产环境」这样的细粒度控制。
        </Paragraph>
        <Paragraph>
          <Text strong>V2 版本（RBAC 模型）：</Text>引入「用户 → 角色 → 权限 → 资源」四层模型。
          <ul>
            <li><Text strong>用户（User）：</Text>操作主体</li>
            <li><Text strong>角色（Role）：</Text>权限的集合，如「应用负责人」「环境运维」「只读用户」</li>
            <li><Text strong>权限（Permission）：</Text>具体的操作权限，如「发布到生产环境」「审批发布」「查看发布历史」</li>
            <li><Text strong>资源（Resource）：</Text>权限作用的对象，如「应用 A」「环境 生产」</li>
          </ul>
        </Paragraph>
        <Paragraph>
          <Text strong>遇到的坑和优化：</Text>
          <ul>
            <li><Text strong>坑 1：权限检查遗漏。</Text>有些 API 端点忘记做权限检查，导致越权操作。优化：引入中间件层统一做权限检查，不在每个 Controller 中单独处理。</li>
            <li><Text strong>坑 2：角色爆炸。</Text>随着业务增长，角色数量爆炸式增长，权限管理变得混乱。优化：引入「权限继承」和「角色组合」，减少角色数量。</li>
            <li><Text strong>坑 3：审批绕过。</Text>紧急情况下有人直接操作数据库修改审批状态。优化：审批记录增加数字签名，防止篡改；紧急发布走独立通道，事后补审批。</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a2-3',
    label: '审批流程设计',
    category: '真实项目经验',
    q: '你们之前发布流程中审批是怎么设计的？生产环境发布需要经过哪些人？',
    a: (
      <div>
        <Paragraph>
          <Text strong>审批流程设计：</Text>
        </Paragraph>
        <ol>
          <li><Text strong>开发环境、测试环境：</Text>无需审批，开发者或自动化流水线自主发布</li>
          <li><Text strong>预发环境：</Text>建议审批（可配置），通常由技术负责人或团队 Lead 审批</li>
          <li><Text strong>生产环境：</Text>必须审批，审批流程为：
            <ul>
              <li>第一级：<Text strong>应用负责人</Text>审批——确认发布内容正确、测试充分</li>
              <li>第二级（可选）：<Text strong>运维负责人</Text>审批——确认发布窗口合适、资源充足</li>
              <li>第三级（可选）：<Text strong>部门负责人</Text>审批——重大变更需要更高层级审批</li>
            </ul>
          </li>
        </ol>
        <Paragraph>
          <Text strong>审批设计的关键点：</Text>
          <ul>
            <li>审批人可以在 Web 界面直接审批，无需额外工具</li>
            <li>审批超时自动提醒（如 30 分钟未审批，发送通知）</li>
            <li>审批记录永久保存，支持审计查询</li>
            <li>紧急发布可以绕过常规审批，但需要事后补审批和复盘</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a2-4',
    label: '最大技术挑战',
    category: '真实项目经验',
    q: '你之前做过的发布系统，最大的技术挑战是什么？怎么解决的？',
    a: (
      <div>
        <Paragraph>
          <Text strong>最大技术挑战：大规模 SSH 并发连接的性能瓶颈。</Text>当同时发布到 200+ 台主机时，Spug Server 需要同时维护 200+ 个 SSH 连接，这导致：
          <ul>
            <li>Server 的 CPU 和内存消耗急剧上升</li>
            <li>网络带宽成为瓶颈</li>
            <li>部分 SSH 连接超时导致发布失败</li>
          </ul>
        </Paragraph>
        <Paragraph><Text strong>解决方案：</Text></Paragraph>
        <ul>
          <li><Text strong>分批并发：</Text>将主机分成多个批次，每批次 20-30 台并发执行，批次间串行</li>
          <li><Text strong>连接池复用：</Text>使用 SSH 连接池，复用已建立的 SSH 连接</li>
          <li><Text strong>异步执行：</Text>将 SSH 操作改为异步非阻塞模式，使用事件循环（asyncio）提高并发处理能力</li>
          <li><Text strong>增加 Server 实例：</Text>部署多个 Spug Server 实例，通过负载均衡分配发布任务</li>
          <li><Text strong>Agent 模式：</Text>对于超大规模（500+ 主机），引入 Agent 模式，由 Agent 代理执行部署操作</li>
        </ul>
        <Paragraph>
          <Text strong>经验教训：</Text>架构设计时就要考虑扩展性，不要在问题出现后才被动优化。同时，不是所有场景都需要全量并发——分批发布本身也是风险控制的手段。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a2-5',
    label: 'EC2 与 K8s 发布流程差异',
    category: '真实项目经验',
    q: '你们的发布系统支持哪些部署目标？EC2 和 K8s 的发布流程有什么不同？',
    a: (
      <div>
        <Paragraph>
          <Text strong>支持的部署目标：</Text>EC2 主机（传统虚拟机/物理机）和 K8s 集群（容器化部署）。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '连接方式', ec2: 'SSH 连接到主机', k8s: 'kubectl API 调用' },
            { key: '2', dimension: '部署单元', ec2: '制品文件（JAR、二进制、静态资源）', k8s: 'Docker 镜像' },
            { key: '3', dimension: '部署方式', ec2: '上传制品 → 执行部署脚本 → 重启服务', k8s: '推送镜像 → 更新 Deployment → K8s Controller 自动滚动更新' },
            { key: '4', dimension: '状态管理', ec2: '发布系统追踪每台主机的部署状态', k8s: '依赖 K8s 的声明式状态管理，查询 Deployment 状态' },
            { key: '5', dimension: '回滚方式', ec2: '重新部署旧版本制品', k8s: 'kubectl rollout undo 或 更新镜像版本' },
            { key: '6', dimension: '健康检查', ec2: '发布系统主动检查进程状态/端口', k8s: '依赖 Readiness Probe 自动检查' },
            { key: '7', dimension: '流量切换', ec2: '依赖 ELB/Nginx 的健康检查', k8s: 'Service 自动管理 Endpoint' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: 'EC2 模式', dataIndex: 'ec2', key: 'ec2' },
            { title: 'K8s 模式', dataIndex: 'k8s', key: 'k8s' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>核心差异：</Text>EC2 模式下发布系统需要「主动管理」部署的每个步骤，K8s 模式下发布系统更多是「声明期望状态」然后依赖 K8s Controller 来执行。K8s 模式将很多复杂的工作（滚动更新、健康检查、流量切换）交给了平台，发布系统需要做的是「调用 K8s API」。
        </Paragraph>
      </div>
    ),
  },

  /* ---- 高级策略 ---- */
  {
    key: 'a3-1',
    label: 'A/B 测试在发布系统中的应用',
    category: '高级策略',
    q: 'A/B 测试和灰度发布有什么本质区别？A/B 测试在发布系统中如何实现？',
    a: (
      <div>
        <Paragraph>
          <Text strong>本质区别：</Text>灰度发布是<Text strong>运维策略</Text>（降低部署风险），A/B 测试是<Text strong>产品实验</Text>（验证功能效果）。灰度发布的目标是「安全上线」，A/B 测试的目标是「数据驱动决策」。
        </Paragraph>
        <Paragraph><Text strong>在发布系统中的实现方式：</Text></Paragraph>
        <ul>
          <li><Text strong>基于 Feature Flag：</Text>通过 Feature Flag 系统实现 A/B 分组，不同用户看到不同版本的功能</li>
          <li><Text strong>基于 Service Mesh：</Text>通过 Istio VirtualService 按用户 ID 哈希路由到不同版本</li>
          <li><Text strong>基于网关：</Text>在 API 网关层根据请求特征（Header、Cookie）路由到不同版本</li>
        </ul>
        <Paragraph>
          <Text strong>数据采集与分析：</Text>A/B 测试的核心不只是「分流」，更重要的是「数据采集和统计分析」。需要：
          <ul>
            <li>追踪用户分组标识（实验组 vs 对照组）</li>
            <li>采集用户行为数据（点击、转化、留存）</li>
            <li>进行统计显著性检验（T 检验、卡方检验）</li>
            <li>确定实验结果的置信度</li>
          </ul>
        </Paragraph>
        <Paragraph>
          <Text type="secondary">面试加分：能区分「灰度发布是运维策略，A/B 测试是产品实验」，并指出两者可以结合使用。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a3-2',
    label: '影子部署',
    category: '高级策略',
    q: '影子部署（Shadow Deployment）是什么？它有什么独特的应用场景？',
    a: (
      <div>
        <Paragraph>
          <Text strong>影子部署（Shadow Deployment / Traffic Mirroring）</Text>是一种将新版本部署到生产环境，接收<Text strong>真实流量的副本</Text>，但<Text strong>不直接响应用户</Text>的部署策略。新版本（影子）的响应被丢弃或仅用于分析，不会影响用户。
        </Paragraph>
        <Paragraph><Text strong>核心特点：</Text></Paragraph>
        <ul>
          <li><Text strong>零风险：</Text>影子实例的任何错误都不会影响用户</li>
          <li><Text strong>真实负载：</Text>在真实流量下测试性能和稳定性，比任何压测工具都更准确</li>
          <li><Text strong>功能验证：</Text>可以对比影子实例和生产实例的输出是否一致</li>
          <li><Text strong>性能基线：</Text>直接对比新旧版本在相同流量下的性能差异</li>
        </ul>
        <Paragraph><Text strong>独特应用场景：</Text></Paragraph>
        <ul>
          <li>重构后的核心服务——需要验证新架构在真实流量下的表现</li>
          <li>数据库迁移——影子实例使用新数据库，对比查询结果一致性</li>
          <li>性能优化——验证优化效果，确保不会引入延迟</li>
          <li>算法升级——推荐系统、风控系统等需要真实流量验证的场景</li>
        </ul>
        <Paragraph>
          <Text strong>实现挑战：</Text>影子部署需要流量复制能力（如 Istio 的 Mirroring 功能），且影子实例的副作用（如数据库写入、第三方 API 调用）需要妥善处理，避免产生脏数据或重复调用。
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a3-3',
    label: '红黑部署详解',
    category: '高级策略',
    q: '红黑部署（Red-Black）和蓝绿部署的异同？Netflix 为什么选择红黑？',
    a: (
      <div>
        <Paragraph>
          <Text strong>红黑部署</Text>是 Netflix 在 Spinnaker 中实现的部署策略，与蓝绿部署的核心区别是：<Text strong>切换后立即回收旧环境</Text>。
        </Paragraph>
        <Table
          dataSource={[
            { key: '1', dimension: '环境保持', blue: '切换后旧环境保留一段时间', red: '切换后旧环境立即销毁' },
            { key: '2', dimension: '回滚方式', blue: '切换回保留的旧环境（秒级）', red: '需要重新部署旧版本（分钟级）' },
            { key: '3', dimension: '资源成本', blue: '持续 2x 资源消耗', red: '切换后释放资源，成本更低' },
            { key: '4', dimension: '适用场景', blue: '对回滚速度要求极高的服务', red: '资源优化优先，接受短时间回滚延迟' },
          ]}
          columns={[
            { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
            { title: '蓝绿部署', dataIndex: 'blue', key: 'blue' },
            { title: '红黑部署', dataIndex: 'red', key: 'red' },
          ]}
          pagination={false}
          size="small"
          bordered
        />
        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>Netflix 为什么选择红黑：</Text>
          <ul>
            <li><Text strong>极高的部署频率：</Text>Netflix 每天部署数千次，如果每次部署都保留旧环境，资源成本将不可接受</li>
            <li><Text strong>不可变基础设施理念：</Text>Netflix 信奉「不可变基础设施」，每次部署都是全新的实例，旧实例应该被销毁</li>
            <li><Text strong>回滚策略不同：</Text>Netflix 的回滚不是「切回旧环境」，而是「重新部署旧版本」——他们的部署速度足够快，重新部署旧版本也只需要几分钟</li>
          </ul>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a3-4',
    label: '不可变部署',
    category: '高级策略',
    q: '不可变部署（Immutable Deployment）的核心思想？在容器化时代为什么重要？',
    a: (
      <div>
        <Paragraph>
          <Text strong>不可变部署</Text>的核心思想是：<Text strong>一旦部署，绝不修改</Text>。每次部署都创建全新的实例，而不是在现有实例上更新代码或配置。这与传统的「可变基础设施」（登录服务器、手动修改配置）完全相反。
        </Paragraph>
        <Paragraph><Text strong>核心原则：</Text></Paragraph>
        <ul>
          <li><Text strong>实例不可变：</Text>运行中的实例永远不会被修改——代码更新 = 创建新实例 + 销毁旧实例</li>
          <li><Text strong>配置不可变：</Text>配置随实例一起创建，运行时不修改配置</li>
          <li><Text strong>环境一致性：</Text>开发、测试、生产环境使用完全相同的镜像</li>
          <li><Text strong>版本化：</Text>每个部署版本都有唯一标识，版本之间完全隔离</li>
        </ul>
        <Paragraph><Text strong>在容器化时代的重要性：</Text></Paragraph>
        <ul>
          <li>Docker 镜像天然就是不可变的——镜像构建后内容不变</li>
          <li>K8s 的声明式 API 完美支持不可变部署——修改镜像版本 = 创建新 Pod + 删除旧 Pod</li>
          <li>消除配置漂移——不会有「上次谁手动改了配置」的问题</li>
          <li>简化回滚——回滚 = 使用旧版本镜像重新部署，和之前的部署完全一致</li>
          <li>可复现性——任何版本的部署都可以精确复现</li>
        </ul>
        <Paragraph>
          <Text type="secondary">面试加分：能提到「不可变部署是云原生十二因子应用的核心原则」，并与 K8s 的实践结合讨论。</Text>
        </Paragraph>
      </div>
    ),
  },
  {
    key: 'a3-5',
    label: 'Feature Flag 系统设计',
    category: '高级策略',
    q: '功能开关（Feature Flag）在发布系统中扮演什么角色？如何设计？',
    a: (
      <div>
        <Paragraph>
          <Text strong>Feature Flag</Text> 在发布系统中扮演<Text strong>「发布与部署的解耦器」</Text>角色。它使得代码部署和功能上线成为两个独立的事件，是发布策略的「最后一公里」。
        </Paragraph>
        <Paragraph><Text strong>在发布系统中的角色：</Text></Paragraph>
        <ul>
          <li><Text strong>发布解耦：</Text>代码可以部署到生产环境，但功能通过开关控制是否对用户可见——实现「部署但未发布」</li>
          <li><Text strong>灰度控制：</Text>通过 Flag 的百分比配置，控制新功能的灰度范围</li>
          <li><Text strong>快速回滚：</Text>关闭 Flag 即可回滚功能，无需重新部署</li>
          <li><Text strong>主干开发支持：</Text>未完成的功能可以合并到主干，通过 Flag 关闭，支持 Trunk-based 开发模式</li>
        </ul>
        <Paragraph><Text strong>设计要点：</Text></Paragraph>
        <ul>
          <li>配置中心化，支持实时更新，无需重启服务</li>
          <li>支持多维度目标（用户 ID、百分比、地域、属性）</li>
          <li>有生命周期管理（创建 → 激活 → 全量 → 清理），过期 Flag 自动告警</li>
          <li>有审计日志，记录 Flag 变更历史</li>
          <li>性能保障——Flag 评估在毫秒级完成</li>
          <li>降级策略——Flag 服务不可用时使用安全默认值</li>
        </ul>
        <Paragraph>
          <Text strong>Flag 债务问题：</Text>过多的 Flag 会产生「Flag 债务」，代码中充斥着 if/else 分支。建议：每个 Flag 都设置到期时间，到期未清理的 Flag 自动告警和强制清理。
        </Paragraph>
      </div>
    ),
  },
];

/* =============================================================================
 * 三、刁难面试题（~12道，含完整追问链）
 * ============================================================================= */

export const trickyQuestions = [
  {
    key: 't1',
    label: '灰度发布 1% 恰好全是 VIP',
    q: '灰度发布 1% 流量恰好都是 VIP 大客户，导致重大损失，你怎么看？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察的是<Text strong>灰度发布的流量选择策略</Text>。面试官想看你是否理解「随机灰度」和「定向灰度」的区别，以及「风险兜底」的思维。很多候选人会回答「选择 1% 没问题」，但问题的关键在于<Text strong>灰度用户的选择策略</Text>，而不是比例本身。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这个问题的核心是<Text strong>灰度用户的选择策略</Text>。如果灰度用户是随机选择的，1% 恰好全是 VIP 的概率确实存在（虽然很低）。正确的做法是：
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>灰度用户分层：</Text>灰度用户不应该随机选择，而应该分层选择——先选择内部员工/测试账号，再选择非 VIP 用户，最后再覆盖 VIP 用户</li>
          <li><Text strong>风险隔离：</Text>VIP 用户应该有独立的灰度策略，比如更小的比例、更长的观察期、更严格的监控</li>
          <li><Text strong>兜底策略：</Text>即使灰度用户出问题，也应该有兜底——比如灰度用户自动回退到旧版本</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '灰度比例选择',
        steps: [
          { q: '那你说说灰度比例怎么选？1% 还是 5% 还是 10%？', a: '取决于服务的重要性和实例数量。核心支付系统从 1% 开始，非关键功能可以从 10% 开始。实例太少时（如 5 个实例），1% 没有意义，只能选择 1 个实例（20%）。', note: '考察对灰度比例的实际理解' },
          { q: '如果实例只有 3 个，你怎么灰度？', a: '3 个实例无法做有效的灰度发布（1 个实例 = 33%）。建议：1) 蓝绿部署替代灰度；2) 或者增加实例数到至少 10 个再做灰度；3) 或者使用 Feature Flag 做功能级别的灰度。', note: '考察对实例数量与灰度关系的理解' },
          { q: '灰度比例和实例数的关系是什么？', a: '最小灰度单位 = 1/N（N 为实例数）。例如 10 个实例，最小灰度是 10%（1 个实例）。如果需要 1% 的灰度，至少需要 100 个实例，或者使用 Service Mesh 的流量拆分（不依赖实例数）。', note: '考察对灰度粒度与实例数量的理解' },
        ],
      },
      {
        chain: '用户分组策略',
        steps: [
          { q: '你怎么保证灰度用户不包含 VIP？', a: '在灰度路由层添加用户属性过滤——VIP 用户标记为「免灰度」或「延迟灰度」，灰度流量只路由到非 VIP 用户。这需要用户画像系统和路由系统的配合。', note: '考察系统设计能力' },
          { q: '如果 VIP 用户也需要灰度怎么办？', a: '为 VIP 用户设置独立的灰度通道——更小的比例（如 0.1%）、更长的观察期（如 1 小时）、更严格的监控阈值。VIP 用户的灰度应该在其他用户灰度成功后再进行。', note: '考察分层灰度思维' },
          { q: '用户画像系统挂了怎么办？灰度怎么做？', a: '降级策略：如果无法获取用户属性，全部流量路由到稳定版本，灰度暂停。安全优先——宁可延迟灰度，也不要在无法区分用户的情况下冒险。', note: '考察降级思维' },
        ],
      },
      {
        chain: '风险兜底',
        steps: [
          { q: '如果灰度真的出问题了，你的兜底方案是什么？', a: '多层兜底：1) 自动回滚——错误率超过阈值自动回滚灰度实例；2) 用户降级——灰度用户检测到异常后自动切换到旧版本；3) 监控告警——灰度阶段异常立即通知相关人员；4) 手动回滚——提供一键回滚按钮。', note: '考察多层防御思维' },
          { q: '自动回滚的阈值怎么设？太敏感会误回滚，太迟钝会扩大影响。', a: '建议使用复合阈值：单指标异常（如错误率突然上升 5%）+ 持续时间（如持续 2 分钟）+ 影响比例（如超过 10% 灰度用户）。多个条件同时满足才触发回滚，避免单点误判。', note: '考察对阈值设计的理解' },
        ],
      },
      {
        chain: '真实翻车经历',
        steps: [
          { q: '你们实际遇到过这种情况吗？', a: '（如实回答）如果遇到过，说明具体场景和应对；如果没遇到过，可以说明「我们通过灰度用户分层和自动回滚机制，将风险降到了最低，但理论上这个风险确实存在」。', note: '考察诚实度和经验' },
          { q: '如果现在让你重新设计灰度策略，你会改进什么？', a: '1) 引入用户画像系统，精细化灰度用户选择；2) 增加「灰度用户健康度」监控，实时评估灰度用户是否受影响；3) 引入自动回滚机制，缩短故障响应时间；4) 灰度用户增加「反馈通道」，让用户主动报告问题。', note: '考察反思和改进能力' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「1% 概率很低，不用太担心」</Text>——这是典型的「概率思维陷阱」，在小概率事件发生后的损失面前，概率本身没有意义</li>
          <li><Text type="danger">「我们只灰度内部员工」</Text>——这个回答太简单，面试官会追问「内部员工不够怎么办」</li>
          <li><Text type="danger">「用更多的实例来降低概率」</Text>——这是「用资源换概率」的思路，治标不治本</li>
          <li><Text type="danger">只讨论比例，不讨论用户选择策略</Text>——说明没有真正理解灰度发布的本质</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>诚实承认「这个问题我之前没有深入思考过」，但可以结合自己已知的知识进行分析：「从我了解的情况来看，灰度发布的核心是降低风险，所以用户选择策略应该和风险控制结合起来。比如可以通过用户画像来避免高风险用户被灰度。」然后引导面试官继续追问其他方面。
      </Paragraph>
    ),
  },
  {
    key: 't2',
    label: '发布系统自己挂了',
    q: '发布系统自己挂了，正在进行的发布怎么办？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察的是<Text strong>发布系统自身的高可用设计</Text>和<Text strong>应急处理能力</Text>。面试官想知道你是否考虑过「发布系统也是系统」这个问题，以及你的系统设计是否有「逃生通道」。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这个问题揭示了发布系统设计中一个常被忽略的问题：<Text strong>发布系统本身也是系统，也需要高可用和故障恢复</Text>。
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>发布系统自身高可用：</Text>多副本部署、故障自动转移、数据库主从</li>
          <li><Text strong>状态持久化：</Text>发布状态存储在数据库中，系统重启后可以恢复</li>
          <li><Text strong>逃生通道：</Text>保留手动发布的能力，如 kubectl 命令行、SSH 脚本</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '高可用设计',
        steps: [
          { q: '发布系统怎么做高可用？', a: '1) 多副本部署（至少 2-3 个副本）；2) 数据库主从 + 自动故障转移；3) 负载均衡器分发请求；4) 健康检查 + 自动摘除故障节点。', note: '考察基础架构设计' },
          { q: '如果数据库也挂了怎么办？', a: '这是最坏情况。需要：1) 数据库备份恢复；2) 发布状态可能丢失，但已部署的实例不受影响（它们已经运行了）；3) 需要重新评估哪些发布已经完成、哪些还在进行中。', note: '考察对最坏情况的思考' },
          { q: '发布系统的高可用要花多少钱？值不值得？', a: '发布系统的高可用投入取决于业务规模。对于日活千万的支付系统，发布系统的高可用必须投入；对于小型内部工具，可以接受一定程度的单点故障。关键是要评估发布系统故障的业务影响。', note: '考察成本与收益的权衡' },
        ],
      },
      {
        chain: '状态恢复',
        steps: [
          { q: '发布系统重启后，怎么知道哪些发布已经完成了？', a: '1) 查询数据库中的发布状态记录；2) 查询目标环境的实际状态（如 K8s 中 Deployment 的实际镜像版本）；3) 对比期望状态和实际状态，判断发布是否完成。', note: '考察状态恢复机制' },
          { q: '如果对比发现「部分完成」怎么处理？', a: '根据发布策略决定：1) 滚动更新——继续完成剩余部分；2) 蓝绿部署——判断流量切换是否已完成；3) 提供「继续发布」或「重新发布」选项给用户。', note: '考察对部分失败的处理' },
        ],
      },
      {
        chain: '逃生通道',
        steps: [
          { q: '逃生通道具体怎么设计？', a: '1) 提供命令行工具（CLI）作为 Web 界面的备选；2) 保留手动操作文档（如 kubectl 命令清单）；3) 紧急情况下可以直接操作 K8s（如 kubectl rollout undo）；4) 为关键操作预置脚本。', note: '考察实际操作能力' },
          { q: '逃生通道会不会被滥用？', a: '需要平衡：1) 逃生通道的操作也需要审计记录；2) 逃生通道的使用需要通知相关人员；3) 逃生通道的操作应该被标记为「紧急操作」，事后需要复盘。', note: '考察安全与便利的平衡' },
        ],
      },
      {
        chain: '实际发生过吗',
        steps: [
          { q: '你们实际遇到过发布系统故障吗？', a: '（如实回答）如果遇到过，说明：1) 当时的影响范围；2) 怎么恢复的；3) 事后做了什么改进。如果没遇到过，说明你们的预防措施（但不要掉以轻心）。', note: '考察诚实度和经验' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「我们发布系统从来不会挂」</Text>——这是典型的「过度自信」，任何系统都可能出问题</li>
          <li><Text type="danger">「挂了就等它恢复」</Text>——说明没有考虑过逃生通道，缺乏应急思维</li>
          <li><Text type="danger">「发布系统挂了不影响正在运行的实例」</Text>——虽然技术上正确，但忽略了「发布未完成」的状态恢复问题</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「这个问题我之前没有系统性地考虑过。从我的理解来看，发布系统作为基础设施的一部分，应该和其他系统一样考虑高可用和故障恢复。核心思路是保证发布状态的可恢复性和保留手动操作的逃生通道。」
      </Paragraph>
    ),
  },
  {
    key: 't3',
    label: '多服务发布失败处理',
    q: '多个团队同时发布互相依赖的微服务，A 服务成功 B 服务失败，如何处理？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察的是<Text strong>微服务发布编排</Text>和<Text strong>分布式事务</Text>的思维。面试官想看你在复杂依赖场景下的决策能力，以及你对「发布顺序」「回滚联动」「数据一致性」的理解。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这是微服务发布的经典难题。核心问题是：<Text strong>A 服务的新版本可能依赖 B 服务的新版本，B 服务发布失败意味着 A 服务的新功能可能无法正常工作。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>发布顺序：</Text>被依赖的服务（B）先发布，依赖方（A）后发布。如果 B 失败，A 不应该发布。</li>
          <li><Text strong>回滚决策：</Text>如果 A 已经发布而 B 失败，需要判断 A 是否受影响——如果 A 的新版本不依赖 B 的新功能，可以保留 A 的新版本；如果依赖，应该回滚 A。</li>
          <li><Text strong>避免方案：</Text>通过 API 版本化和 Feature Flag 解耦服务间的发布依赖。</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '发布顺序',
        steps: [
          { q: '你怎么确定发布顺序？', a: '通过服务依赖拓扑图。被依赖的服务先发布，依赖方后发布。如果存在循环依赖，先打破循环依赖再发布。', note: '考察对服务依赖的理解' },
          { q: '如果有 20 个服务互相依赖怎么办？', a: '这是架构问题，不是发布问题。应该先优化服务依赖关系，减少发布耦合。短期方案：1) 使用 Feature Flag 解除依赖；2) 使用 API 版本化让新旧版本共存。', note: '考察架构思维' },
          { q: '发布顺序确定了，但 B 服务发布需要 2 小时，A 服务等不了怎么办？', a: '1) 优化 B 服务的发布速度；2) A 服务的新版本应该兼容 B 服务的旧版本（向前兼容）；3) 使用 Feature Flag 让 A 的新功能在 B 发布后再开启。', note: '考察时间约束下的决策' },
        ],
      },
      {
        chain: '回滚策略',
        steps: [
          { q: 'A 服务已经发布成功，B 服务发布失败，A 要不要回滚？', a: '取决于 A 是否依赖 B 的新功能。如果 A 的新版本兼容 B 的旧版本，A 不需要回滚。如果 A 的新版本必须依赖 B 的新功能，A 需要回滚。', note: '考察依赖判断' },
          { q: '回滚 A 服务会不会影响其他服务？', a: '可能。如果 C 服务也依赖 A 服务的新版本，回滚 A 会影响 C。需要评估整个依赖链的影响。这就是为什么应该尽量减少多服务同时发布的原因。', note: '考察级联影响分析' },
        ],
      },
      {
        chain: '数据一致性',
        steps: [
          { q: 'A 服务回滚了，但 B 服务已经写入了新数据格式，怎么办？', a: '这是最棘手的情况。防范优于补救：1) 数据库变更必须向前兼容；2) 使用分阶段 Schema 变更；3) 最坏情况下，需要手动修复数据。', note: '考察数据一致性思维' },
          { q: '有没有更好的方案避免这种问题？', a: '根本方案是「减少多服务同时发布」。1) 使用 API 版本化，让每个服务独立发布；2) 使用 Feature Flag 解耦发布依赖；3) 使用契约测试确保兼容性。', note: '考察根本解决方案' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「全部回滚」</Text>——这是最简单的答案，但忽略了不需要回滚的情况，缺乏分析能力</li>
          <li><Text type="danger">「A 不用回滚，因为它已经成功了」</Text>——忽略了功能依赖关系，缺乏系统性思维</li>
          <li><Text type="danger">「我们从来不会同时发布多个服务」</Text>——过于理想化，实际场景中多服务同时发布是常见需求</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「这个问题涉及到微服务发布编排的复杂性。从我的理解来看，核心是要分析服务间的依赖关系——被依赖的服务先发布，依赖方后发布。如果出现部分失败，需要根据依赖关系决定回滚范围。最好的解决方案是尽量减少多服务同时发布的需要。」
      </Paragraph>
    ),
  },
  {
    key: 't4',
    label: '幂等性陷阱',
    q: '网络抖动导致发布请求重复执行，如何保证幂等？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察<Text strong>分布式系统幂等性设计</Text>。面试官想看你是否理解幂等性的多层实现（应用层、数据库层、基础设施层），以及当所有手段都失效时的兜底方案。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          <Text strong>幂等性</Text>是发布系统可靠性的基石。核心思路是：<Text strong>通过唯一标识 + 状态检查，确保同一个发布请求只被处理一次。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>幂等键设计：</Text>每个发布请求携带唯一幂等键（UUID），系统通过幂等键去重</li>
          <li><Text strong>分布式锁：</Text>在执行发布前获取分布式锁，确保同一时间只有一个进程在执行</li>
          <li><Text strong>数据库唯一约束：</Text>对关键字段添加唯一约束，防止重复插入</li>
          <li><Text strong>最终兜底：</Text>K8s 声明式 API 天然幂等——同样的 Deployment 执行多次结果相同</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '幂等键设计',
        steps: [
          { q: '幂等键怎么生成？放哪里？', a: '由客户端生成 UUID 作为幂等键，放在请求 Header 中。服务端存储幂等键和请求结果的映射，相同幂等键的请求直接返回缓存结果。', note: '考察幂等键的实现细节' },
          { q: '幂等键的有效期是多久？过期了怎么办？', a: '通常设置 24 小时有效期。过期后，相同幂等键的请求可能被重新执行——但此时需要通过业务逻辑判断是否真的需要执行（如检查目标环境是否已经运行了目标版本）。', note: '考察幂等键生命周期管理' },
          { q: '如果客户端重试时生成了新的幂等键怎么办？', a: '客户端需要保证重试时使用相同的幂等键。可以在客户端侧做幂等键缓存，或者在服务端通过业务逻辑（如「发布单 ID + 发布次数」）作为幂等键。', note: '考察对客户端的幂等要求' },
        ],
      },
      {
        chain: '分布式锁',
        steps: [
          { q: '分布式锁用什么实现？如果锁服务挂了怎么办？', a: 'Redis Redlock 或 ZooKeeper。锁服务挂了需要降级策略：1) 使用数据库级别的唯一约束作为兜底；2) 如果所有手段都失效，需要人工介入判断。', note: '考察分布式锁的可靠性' },
          { q: '分布式锁的超时时间怎么设置？', a: '需要平衡：太短可能导致锁提前释放（重复执行），太长可能导致锁长时间占用（发布失败）。建议设置为「预计发布时间的 2-3 倍」，并支持锁续期。', note: '考察对锁超时的理解' },
        ],
      },
      {
        chain: '如果所有手段都失效了',
        steps: [
          { q: '如果幂等键、分布式锁、数据库约束都失效了，怎么办？', a: '最后一层兜底是「部署操作本身的幂等性」。K8s 的声明式 API 天然幂等——同样的 Deployment YAML 执行多次，结果相同。SSH 部署脚本应该检查当前状态再决定是否执行（如检查进程是否已经运行了目标版本）。', note: '考察多层防御思维' },
          { q: '如果连部署操作本身都不幂等怎么办？', a: '那就只能寄希望于：1) 监控告警——及时发现重复发布的问题；2) 人工介入——手动检查并修复；3) 回滚——如果重复发布导致了问题，回滚到稳定版本。', note: '考察最坏情况处理' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「我们用了分布式锁，所以不会重复执行」</Text>——忽略了分布式锁的可靠性问题，没有兜底方案</li>
          <li><Text type="danger">「用数据库唯一约束就行了」</Text>——没有考虑应用层和基础设施层的多层防护</li>
          <li><Text type="danger">「重复执行也没关系，反正部署是幂等的」</Text>——过于乐观，没有考虑非幂等的部署操作</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「幂等性是分布式系统的基础问题。从我的理解来看，核心思路是多层防护——应用层用幂等键去重，中间件层用分布式锁，数据库层用唯一约束，基础设施层利用 K8s 声明式 API 的天然幂等性。每一层都是上一层的兜底。」
      </Paragraph>
    ),
  },
  {
    key: 't5',
    label: '回滚丢数据',
    q: '蓝绿部署切换后发现严重问题，回滚到旧环境，但数据库有新数据，旧版本 Schema 不兼容，怎么办？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察<Text strong>蓝绿部署中数据库兼容性</Text>这个核心难题。面试官想看你对「数据向前兼容」和「分阶段 Schema 变更」的理解深度，以及真实遇到数据问题时的处理能力。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这是蓝绿部署中最经典也最棘手的问题。核心矛盾是：<Text strong>新版本已经写入了新格式的数据，旧版本代码无法读取这些数据。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>预防优于补救：</Text>Schema 变更必须分阶段进行，每个阶段都兼容上一个版本</li>
          <li><Text strong>分阶段变更：</Text>先添加新字段（兼容旧代码），再部署新代码，最后清理旧字段</li>
          <li><Text strong>紧急处理：</Text>如果已经发生不兼容，需要评估影响范围和数据修复方案</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '分阶段变更',
        steps: [
          { q: '分阶段变更具体怎么做？', a: '三阶段：1) 兼容阶段——添加新字段（允许 NULL），旧代码忽略新字段；2) 部署阶段——部署新代码，使用新字段；3) 清理阶段——确认稳定后删除旧字段。每个阶段都可以安全回滚。', note: '考察分阶段变更的具体操作' },
          { q: '如果新字段不能为 NULL 怎么办？', a: '1) 使用默认值；2) 使用数据库触发器自动填充；3) 编写数据迁移脚本填充历史数据。关键是要让新字段在旧代码读取时不会报错。', note: '考察对数据库约束的处理' },
          { q: '分阶段变更需要多长时间？紧急发布等不了怎么办？', a: '分阶段变更确实需要更多时间。紧急情况下：1) 使用 Feature Flag 控制新旧代码路径；2) 使用 JSON 字段而不是 Schema 变更来存储新数据；3) 接受「回滚可能丢数据」的风险并做好预案。', note: '考察时间约束下的权衡' },
        ],
      },
      {
        chain: '无法向前兼容的情况',
        steps: [
          { q: '什么情况下无法向前兼容？', a: '1) 修改了字段类型（如 VARCHAR → INT）；2) 删除了必填字段；3) 修改了约束条件。这些变更需要更复杂的处理。', note: '考察对不兼容变更的识别' },
          { q: '如果真的无法向前兼容，怎么处理？', a: '1) 双写方案——同时写入新旧两种数据结构；2) 数据库视图——用视图隔离新旧 Schema；3) 中间层——用 API 层转换数据格式。这些方案增加了复杂度，但可以保证兼容性。', note: '考察高级兼容方案' },
        ],
      },
      {
        chain: '双写方案',
        steps: [
          { q: '双写方案怎么保证数据一致性？', a: '使用数据库事务保证双写的原子性。如果无法使用事务（跨表/跨库），需要接受最终一致性，并设计补偿机制。', note: '考察数据一致性处理' },
          { q: '双写会不会影响性能？', a: '会，双写增加了写入开销。但这是为兼容性付出的代价。可以通过异步写入、批量写入等方式降低影响。', note: '考察性能与兼容性的权衡' },
        ],
      },
      {
        chain: '数据不一致',
        steps: [
          { q: '如果已经发生了数据不一致，怎么处理？', a: '1) 评估影响范围——哪些数据被影响了；2) 编写数据修复脚本——将新格式数据转换回旧格式；3) 如果无法转换，可能需要暂时冻结受影响的用户数据。', note: '考察数据修复能力' },
          { q: '出过这样的事吗？', a: '（如实回答）如果遇到过，说明具体的场景、影响和修复过程。如果没遇到过，说明你们的分阶段变更策略有效预防了这个问题。', note: '考察诚实度和经验' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「回滚前先回滚数据库」</Text>——数据库回滚极其危险，可能导致数据丢失</li>
          <li><Text type="danger">「蓝绿部署不会遇到这个问题，因为切换很快」</Text>——忽略了切换后新版本写入新数据的时间窗口</li>
          <li><Text type="danger">「我们只做兼容性变更」</Text>——过于理想化，实际项目中总有不兼容的变更需求</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「这个问题涉及到蓝绿部署中最核心的数据库兼容性挑战。从我的理解来看，根本解决方案是分阶段 Schema 变更——将数据库变更和代码变更解耦。如果已经发生了不兼容，需要评估影响范围并制定数据修复方案。」
      </Paragraph>
    ),
  },
  {
    key: 't6',
    label: '1000台机器同时发布',
    q: '1000台机器同时发布，发布系统怎么支撑？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察的是<Text strong>发布系统的规模化能力</Text>。面试官想看你对大规模并发、系统瓶颈、分批策略的理解，以及失败场景下的处理能力。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          1000台机器同时发布是对发布系统架构设计的严峻考验。核心挑战在于：<Text strong>如何在保证发布速度的同时，不压垮发布系统本身和目标服务。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>分批发布：</Text>将1000台机器分成多个批次（如每批50-100台），批次间串行、批次内并发</li>
          <li><Text strong>异步执行：</Text>使用消息队列解耦发布请求，异步执行部署操作</li>
          <li><Text strong>Worker 扩展：</Text>部署多个 Worker 实例，水平扩展发布能力</li>
          <li><Text strong>熔断保护：</Text>设置失败率阈值，超过阈值自动暂停发布</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '并发控制',
        steps: [
          { q: '你怎么确定每批多少台机器？', a: '取决于几个因素：1) 发布系统 Worker 的处理能力；2) 目标服务的承载能力（不能因为发布导致服务过载）；3) 网络带宽限制。通常每批 50-100 台，可根据实际情况动态调整。', note: '考察对实际约束的理解' },
          { q: '如果发布过程中目标服务因为大量重启而不可用怎么办？', a: '这就是 PDB（PodDisruptionBudget）的作用——限制同时不可用的实例数。对于 K8s，设置 maxUnavailable 控制不可用比例；对于 EC2，分批发布确保始终有足够的实例在服务。', note: '考察对服务可用性的保护' },
        ],
      },
      {
        chain: '系统瓶颈',
        steps: [
          { q: '发布系统的瓶颈在哪里？', a: '1) 发布系统数据库（大量并发写入发布状态）；2) SSH 连接数（EC2 模式）；3) 制品下载带宽（所有机器同时拉取制品）；4) 内存和 CPU。需要针对每个瓶颈做优化。', note: '考察对系统瓶颈的识别' },
          { q: '制品下载的瓶颈怎么解决？', a: '1) 使用层次化制品仓库（如 Harbor 的 P2P 分发）；2) 使用 CDN 加速制品下载；3) 预分发——提前将制品推送到目标机器；4) 使用 BitTorrent 协议分发大文件。', note: '考察对制品分发的理解' },
          { q: '如果发布系统数据库成为瓶颈怎么办？', a: '1) 使用批量写入减少数据库操作次数；2) 使用异步写入，先执行部署再写入状态；3) 使用 Redis 缓存热点数据；4) 数据库读写分离。', note: '考察数据库优化思路' },
        ],
      },
      {
        chain: '失败重试',
        steps: [
          { q: '如果一批中有 30% 的机器失败了，怎么处理？', a: '1) 暂停该批次发布；2) 分析失败原因（网络？资源？配置？）；3) 如果是临时性故障，可以使用补偿发布模式重试失败机器；4) 如果是普遍性问题，可能需要回滚已发布的机器。', note: '考察失败处理策略' },
          { q: '如果 1000 台都失败了怎么办？', a: '这是灾难性场景。1) 保留所有失败日志和现场信息；2) 判断是发布系统问题还是目标服务问题；3) 如果是发布系统问题，修复后使用补偿发布重试；4) 如果是目标服务问题，可能需要回滚到之前版本并启动紧急修复流程。', note: '考察灾难恢复思维' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「1000台同时并发就行」</Text>——严重低估了大规模并发对发布系统和目标服务的压力</li>
          <li><Text type="danger">「用 K8s，让它自己处理」</Text>——虽然 K8s 可以处理滚动更新，但大规模集群的 K8s 控制平面也可能成为瓶颈</li>
          <li><Text type="danger">只讨论技术方案，不讨论失败处理</Text>——大规模发布中失败是常态，不讨论失败处理说明缺乏实战经验</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「大规模发布需要考虑多个维度的瓶颈——发布系统自身、目标服务、网络带宽。从我的理解来看，核心策略是分批发布 + 异步执行 + Worker 扩展。同时需要完善的失败处理和重试机制。」
      </Paragraph>
    ),
  },
  {
    key: 't7',
    label: 'Readiness Probe 写错了',
    q: 'K8s 滚动更新 Readiness Probe 写错了，新 Pod 永远不 Ready，会发生什么？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察对<Text strong>K8s 滚动更新机制</Text>的深入理解。面试官想看你知道 K8s 在异常情况下的行为，以及如何预防和处理这类问题。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这是 K8s 发布中常见的「静默故障」场景。由于 maxSurge 限制，新 Pod 创建后不 Ready，K8s 不会继续创建更多新 Pod，同时旧 Pod 也不会被删除（因为新 Pod 不 Ready 意味着不可用 Pod 数已经达到 maxUnavailable 限制）。
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>K8s 行为：</Text>滚动更新卡住——新 Pod 不 Ready，旧 Pod 不被删除，更新进度停滞</li>
          <li><Text strong>发现时机：</Text>通过 progressDeadlineSeconds 过期自动标记失败，或通过监控告警发现</li>
          <li><Text strong>修复方式：</Text>kubectl rollout undo 回滚到上一个版本，修复 Probe 后重新部署</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: 'K8s 行为',
        steps: [
          { q: 'K8s 具体会怎么表现？', a: '1) 创建新 Pod（受 maxSurge 限制）；2) 新 Pod 启动但 Readiness Probe 失败，Pod 状态为 Running 但 Not Ready；3) 因为新 Pod 不 Ready，K8s 不会继续创建更多新 Pod；4) 旧 Pod 继续运行，服务不受影响；5) 如果设置了 progressDeadlineSeconds，超时后 Deployment 标记为 Failed。', note: '考察对 K8s 滚动更新行为的精确理解' },
          { q: 'Readiness Probe 和 Liveness Probe 写错了有什么区别？', a: 'Readiness Probe 写错 = 新 Pod 不接收流量但继续运行，旧 Pod 继续服务，发布卡住。Liveness Probe 写错 = 新 Pod 被反复重启，可能触发 CrashLoopBackOff，影响更严重。', note: '考察对两种 Probe 区别的理解' },
        ],
      },
      {
        chain: '发现时机',
        steps: [
          { q: '你怎么第一时间发现这个问题？', a: '1) 发布系统监控 kubectl rollout status 的输出；2) 设置 progressDeadlineSeconds，超时后自动告警；3) 监控 Pod 的 Ready 状态变化；4) 发布系统在发布过程中实时检查新 Pod 的 Ready 状态。', note: '考察监控和告警设计' },
          { q: '如果 progressDeadlineSeconds 没设置怎么办？', a: '那发布会永远卡住，直到有人发现。这是一个常见的配置遗漏。建议：1) 所有 Deployment 都必须设置 progressDeadlineSeconds；2) 使用 Admission Webhook 强制校验；3) 在发布系统中做发布超时检测。', note: '考察防御性配置思维' },
        ],
      },
      {
        chain: '如何快速修复',
        steps: [
          { q: '发现后怎么快速修复？', a: '1) kubectl rollout undo deployment/my-app —— 立即回滚到上一个版本；2) 修复 Readiness Probe 配置；3) 重新部署。整个过程通常可以在 1-2 分钟内完成。', note: '考察应急处理能力' },
          { q: '如果 kubectl rollout undo 也失败了怎么办？', a: '直接编辑 Deployment YAML，将镜像版本改回旧版本，然后 kubectl apply。这是最底层的修复方式，但一定能生效。', note: '考察兜底方案' },
        ],
      },
      {
        chain: '如何预防',
        steps: [
          { q: '怎么预防这类问题？', a: '1) 预发环境验证——所有配置变更先在预发环境验证；2) 发布系统集成——发布前自动检查 manifest 的合法性；3) 蓝绿部署——先部署到绿色环境验证，再切换流量；4) 灰度发布——先部署少量 Pod 验证 Probe 是否正常。', note: '考察预防机制设计' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「新 Pod 不 Ready 会导致服务不可用」</Text>——错误！旧 Pod 还在运行，服务不受影响。这个回答暴露了对 K8s 滚动更新机制的不理解</li>
          <li><Text type="danger">「K8s 会自动回滚」</Text>——K8s 不会自动回滚，只会标记 Failed。需要手动回滚或配置自动化回滚</li>
          <li><Text type="danger">「我们不会写错 Probe」</Text>——过于自信，实际项目中 Probe 配置错误是常见问题</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「从我对 K8s 滚动更新机制的理解来看，新 Pod 不 Ready 会导致滚动更新卡住——新 Pod 不接收流量，旧 Pod 继续运行。K8s 不会自动回滚，需要通过 progressDeadlineSeconds 检测超时并告警。修复方式是 kubectl rollout undo 回滚到上一个版本。」
      </Paragraph>
    ),
  },
  {
    key: 't8',
    label: '紧急发布责任',
    q: '紧急发布跳过审批流程，出事后谁负责？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察的是<Text strong>责任划分</Text>和<Text strong>流程设计</Text>。面试官想看你对「技术决策」和「管理决策」边界的理解，以及你如何设计一个既能应对紧急情况、又能明确责任的流程。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这是一个<Text strong>技术和管理的交叉问题</Text>。紧急发布跳过审批是一种「风险接受」——在紧急情况下，修复问题的收益大于跳过审批的风险。
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>责任划分：</Text>紧急发布的操作人承担操作责任，但组织应承担「紧急通道」的流程责任</li>
          <li><Text strong>流程设计：</Text>紧急通道应该有明确的规则——谁可以发起、什么场景可以走紧急通道、事后必须补审批和复盘</li>
          <li><Text strong>组织文化：</Text>建立「不追责」的事后复盘文化，鼓励从错误中学习</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '追责机制',
        steps: [
          { q: '具体怎么追责？', a: '不建议追责个人，而是追责流程。紧急发布出问题，说明流程设计有缺陷——为什么紧急情况下没有更好的保护机制？应该改进流程，而不是惩罚个人。', note: '考察对组织文化的理解' },
          { q: '如果操作人明确违规操作怎么办？', a: '区分「紧急情况下的合理决策」和「恶意违规操作」。前者属于流程问题，后者属于纪律问题。需要具体分析操作人的动机和决策背景。', note: '考察对责任边界的判断' },
        ],
      },
      {
        chain: '流程设计',
        steps: [
          { q: '紧急通道的流程怎么设计？', a: '1) 明确触发条件——什么情况下可以走紧急通道（如 P0 故障、安全漏洞）；2) 限制操作范围——只能修复问题，不能上线新功能；3) 自动通知——紧急发布时自动通知所有相关人员；4) 事后补审批——24小时内补审批流程；5) 事后复盘——48小时内进行复盘。', note: '考察流程设计能力' },
          { q: '怎么防止紧急通道被滥用？', a: '1) 紧急发布次数纳入团队考核指标，过多紧急发布说明质量有问题；2) 每次紧急发布必须复盘，分析根因；3) 紧急发布的操作记录被标记，定期审计。', note: '考察滥用防范机制' },
        ],
      },
      {
        chain: '权限控制',
        steps: [
          { q: '谁可以走紧急通道？', a: '建议限制为：1) 值班运维人员；2) 技术负责人；3) 应用负责人。不应该所有人都能走紧急通道。同时需要记录紧急通道的使用者，定期审计。', note: '考察权限设计' },
          { q: '你怎么说服老板接受紧急通道的设计？', a: '用数据说话：1) 展示紧急通道的必要性——说明紧急情况下的时间成本；2) 展示安全控制措施——紧急通道不是无限制的，有明确的规则和审计；3) 参考行业最佳实践——Google、Netflix 等公司都有类似的紧急通道设计。', note: '考察向上沟通能力' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「操作人负全责」</Text>——过于简单化，忽略了组织流程的责任</li>
          <li><Text type="danger">「紧急情况不应该追责」</Text>——过于宽松，没有考虑流程的约束力</li>
          <li><Text type="danger">「我们从来不走紧急通道」</Text>——过于理想化，实际项目中紧急情况是无法避免的</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「这是一个技术管理交叉的问题。从我的理解来看，核心是设计一个既能应对紧急情况、又能明确责任的流程。紧急通道需要有明确的规则、审计和事后复盘。责任应该由流程设计来承载，而不是完全归咎于个人。」
      </Paragraph>
    ),
  },
  {
    key: 't9',
    label: '配置没改代码',
    q: '发布时改了配置没改代码，这个配置变更算不算一次发布？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察对<Text strong>「发布」定义</Text>的理解。面试官想看你对「部署」和「发布」区别的理解，以及你对配置变更管理的思考。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          <Text strong>算一次发布。</Text>虽然代码没变，但配置变更会影响服务行为，应该被记录和追溯。配置变更和代码变更的区别在于<Text strong>构建阶段可以跳过</Text>（使用快速发布模式），但发布流程（记录、通知、审批）不应该跳过。
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>配置变更 = 发布：</Text>任何影响服务行为的变更都应该走发布流程</li>
          <li><Text strong>简化流程：</Text>配置变更可以使用快速发布模式，跳过构建阶段</li>
          <li><Text strong>版本管理：</Text>配置变更也应该有版本号，和代码版本关联</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '版本管理',
        steps: [
          { q: '配置的版本怎么管理？', a: '1) 配置存储在 Git 中，每次变更提交一个 Commit；2) 配置变更的 Commit ID 和代码版本关联；3) 发布系统中记录配置版本和代码版本的组合。', note: '考察配置版本化思维' },
          { q: '如果配置变更和代码变更同时发生，怎么记录？', a: '发布系统记录两个维度的版本：代码版本（镜像 Tag）+ 配置版本（ConfigMap 版本）。发布单中同时记录这两个版本信息，确保完整可追溯。', note: '考察多维度版本管理' },
        ],
      },
      {
        chain: '回滚策略',
        steps: [
          { q: '配置变更怎么回滚？', a: '1) 如果使用 ConfigMap，回滚到上一个版本的 ConfigMap；2) 如果使用配置中心，回滚到上一个配置版本；3) 如果配置和代码一起部署，使用快速发布模式回滚旧版本制品。', note: '考察配置回滚机制' },
          { q: '代码回滚了，配置要不要回滚？', a: '取决于配置变更是否与代码版本耦合。如果配置变更是为新代码准备的，代码回滚后配置也应该回滚。如果配置变更是独立的（如调整日志级别），代码回滚后配置可以保留。', note: '考察配置与代码的耦合判断' },
        ],
      },
      {
        chain: '实际做法',
        steps: [
          { q: '你们实际是怎么做的？', a: '（结合实际经验）配置变更走快速发布模式——跳过构建阶段，直接更新 ConfigMap 或配置中心，然后重启服务。发布单中记录配置变更的内容和版本。', note: '考察实际操作经验' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「不算发布，只是改了配置」</Text>——低估了配置变更的风险，忽略了审计追溯的重要性</li>
          <li><Text type="danger">「配置变更和代码发布一样走完整流程」</Text>——过于僵化，没有利用快速发布模式简化流程</li>
          <li><Text type="danger">「配置变更不需要记录，因为代码没变」</Text>——缺乏版本管理思维，出现问题时无法追溯</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「从我的理解来看，配置变更虽然不涉及代码变更，但仍然会影响服务行为，应该被记录和追溯。可以通过快速发布模式简化流程。关键是要确保配置变更和代码变更一样具有可追溯性和可回滚性。」
      </Paragraph>
    ),
  },
  {
    key: 't10',
    label: '5分钟内发现问题',
    q: '你怎么确保发布后 5 分钟内一定能发现问题？如果问题在 5 分钟后才暴露呢？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题考察<Text strong>发布监控</Text>和<Text strong>长尾问题处理</Text>。面试官想看你对「即时问题」和「长尾问题」的区分，以及你的监控策略是否能覆盖不同时间维度的问题。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          5分钟是一个理想目标，但不是所有问题都能在5分钟内暴露。核心思路是：<Text strong>分层监控 + 分阶段观察 + 兜底机制。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>即时问题（秒级-分钟级）：</Text>错误率飙升、服务宕机、健康检查失败——通过实时监控告警</li>
          <li><Text strong>短期问题（分钟级-小时级）：</Text>内存泄漏、连接池耗尽、慢查询增加——通过趋势监控</li>
          <li><Text strong>长尾问题（小时级-天级）：</Text>磁盘空间耗尽、数据积累导致的性能退化——通过长期监控和基线对比</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '监控指标',
        steps: [
          { q: '5分钟内能发现的问题有哪些？', a: '1) 错误率/成功率——实时告警；2) 服务健康检查——Readiness/Liveness 失败；3) 部署状态——Pod 启动失败、CrashLoopBackOff；4) 关键业务指标——下单量突然下降。这些指标在 1-5 分钟内就能发现。', note: '考察对即时指标的识别' },
          { q: '如果问题在 30 分钟后才暴露呢？', a: '这就是为什么需要「分阶段观察」。灰度发布中，每个阶段观察 10-30 分钟。同时，发布后 1-2 小时内持续关注趋势监控（如内存使用率趋势、GC 频率变化），这些指标的变化需要更长时间才能体现。', note: '考察对长尾问题的认识' },
        ],
      },
      {
        chain: '告警策略',
        steps: [
          { q: '告警阈值怎么设？', a: '使用基线对比而非绝对阈值。发布前采集当前版本的指标基线，发布后对比新版本的指标变化。例如：错误率上升超过基线 50% 告警、P99 延迟上升超过基线 30% 告警。', note: '考察基线对比策略' },
          { q: '告警太多怎么办？怎么避免告警疲劳？', a: '1) 分级告警——P0（立即处理）、P1（1小时内）、P2（24小时内）；2) 告警聚合——同类告警合并，避免重复；3) 发布窗口告警降噪——发布期间的预期波动不告警；4) 自动修复——达到阈值自动回滚，不需要人工介入。', note: '考察告警管理策略' },
        ],
      },
      {
        chain: '长尾问题',
        steps: [
          { q: '有没有漏掉过问题？', a: '（如实回答）如果漏掉过，说明：1) 当时的问题是什么；2) 为什么没发现；3) 后来怎么改进的。如果没漏掉过，说明你们的监控策略有效，但也要承认「没有完美的监控，总有监控盲区」。', note: '考察诚实度和反思能力' },
          { q: '怎么覆盖监控盲区？', a: '1) 定期回顾监控盲区——每次线上故障后复盘监控是否有遗漏；2) 用户反馈通道——用户报告的问题是最直接的监控盲区信号；3) 混沌工程——主动注入故障，测试监控是否能发现。', note: '考察对监控盲区的认识' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「我们一定能 5 分钟内发现所有问题」</Text>——过于自信，忽略了监控盲区和长尾问题</li>
          <li><Text type="danger">「监控告警设得足够敏感就行」</Text>——太敏感会导致告警疲劳，反而降低监控效果</li>
          <li><Text type="danger">没有讨论基线对比和趋势监控</Text>——说明缺乏系统化的监控设计思维</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「5分钟是一个理想目标。从我的理解来看，核心是建立分层监控——即时问题通过实时告警，长尾问题通过趋势监控和基线对比。不是所有问题都能在5分钟内暴露，所以需要分阶段观察和持续监控兜底。」
      </Paragraph>
    ),
  },
  {
    key: 't11',
    label: '真实翻车经历',
    q: '你说你做过这套系统，但听起来都是理想情况。能不能说一次真实的翻车经历？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题是<Text strong>压力测试</Text>，面试官想验证你的经验是否真实。能说出具体细节（时间线、影响范围、修复过程）的候选人通常有真实经验；只能泛泛而谈的候选人可能是在「纸上谈兵」。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          这道题需要<Text strong>如实回答</Text>。如果你有真实的翻车经历，详细描述——这是加分的。如果你没有，诚实说明「我目前经历的项目中发布系统运行比较稳定，没有遇到严重的翻车事故」，但可以补充「我了解行业中的常见翻车案例」并举例。
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>具体细节：</Text>时间、环境、影响范围、根因</li>
          <li><Text strong>应对过程：</Text>怎么发现的、怎么修复的、花了多长时间</li>
          <li><Text strong>事后复盘：</Text>改进了什么、如何预防类似问题</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '具体细节',
        steps: [
          { q: '什么时候发生的？影响有多大？', a: '（给出具体时间、影响用户数、影响时长）越具体越可信。不要只说「有一次遇到问题」，要说「2023年Q3，生产环境发布导致支付成功率下降了5%，持续了约15分钟」。', note: '考察细节的真实性' },
          { q: '怎么发现的？', a: '（说明发现渠道）是监控告警？用户投诉？还是同事发现的？这反映了团队的监控能力。', note: '考察发现机制' },
        ],
      },
      {
        chain: '修复过程',
        steps: [
          { q: '怎么修复的？花了多长时间？', a: '（描述修复步骤和时间线）1) 发现问题（T+0）；2) 决定回滚（T+2）；3) 回滚执行（T+5）；4) 服务恢复（T+15）。具体的时间线体现真实经验。', note: '考察应急响应能力' },
          { q: '回滚过程中有没有遇到新的问题？', a: '（如实回答）回滚本身也可能出问题，如数据兼容性、配置漂移等。如果遇到过，说明具体问题；如果没遇到，说明回滚方案准备充分。', note: '考察回滚的复杂性认识' },
        ],
      },
      {
        chain: '事后复盘',
        steps: [
          { q: '事后做了什么改进？', a: '（具体改进措施）1) 流程改进——增加了什么检查环节；2) 技术改进——增加了什么自动化测试；3) 监控改进——增加了什么告警指标。改进措施越具体越好。', note: '考察反思和改进能力' },
          { q: '如果再来一次，你会怎么做？', a: '展示反思能力：1) 提前预防——在发布前就能发现问题的措施；2) 更快响应——缩短发现和恢复时间；3) 更好沟通——更及时地通知相关人员。', note: '考察系统性反思能力' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「我们从来没有翻过车」</Text>——要么经验不足，要么对「翻车」的定义太窄</li>
          <li><Text type="danger">描述过于笼统，缺乏具体细节</Text>——如「有一次发布出了点问题，我们很快就修复了」——缺乏可信度</li>
          <li><Text type="danger">只描述问题，不描述改进</Text>——说明缺乏从错误中学习的能力</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了（没有真实翻车经历）：</Text>「坦白说，我目前经历的项目中发布系统运行比较稳定，没有遇到严重的翻车事故。但我了解行业中的常见翻车案例，比如 Knight Capital 在 2012 年 45 分钟内损失 4.4 亿美元，就是因为发布系统缺少自动化检查。从这个案例中我学到……」——用行业案例展示你的学习能力。
      </Paragraph>
    ),
  },
  {
    key: 't12',
    label: '所有自动回滚都失败',
    q: '如果所有自动回滚手段都失败了，你怎么办？',
    intent: (
      <div>
        <Paragraph>
          <Text strong>面试官意图：</Text>这道题是<Text strong>终极压力测试</Text>，考察你在最极端情况下的应急处理能力、心理素质和组织协调能力。面试官想看你的「兜底方案」思维和「危机管理」能力。
        </Paragraph>
      </div>
    ),
    answer: (
      <div>
        <Paragraph>
          当所有自动化手段都失效时，需要<Text strong>手动介入 + 组织协调 + 心理稳定</Text>。核心原则：<Text strong>先止血，再分析，后复盘。</Text>
        </Paragraph>
        <Paragraph><Text strong>核心思路：</Text></Paragraph>
        <ol>
          <li><Text strong>手动回滚：</Text>直接操作 K8s API、服务器、负载均衡器，手动恢复服务</li>
          <li><Text strong>通信协调：</Text>立即通知受影响团队，建立沟通渠道</li>
          <li><Text strong>心理压力管理：</Text>保持冷静，按步骤执行，不要慌乱中做出错误决策</li>
        </ol>
      </div>
    ),
    followUpChains: [
      {
        chain: '手动回滚',
        steps: [
          { q: '手动回滚具体怎么做？', a: '1) K8s 场景：kubectl rollout undo deployment/my-app --to-revision=N；2) EC2 场景：手动 SSH 到主机，执行旧版本部署脚本；3) 负载均衡：手动调整流量分配。需要有预置的手动操作文档，紧急情况下不需要临时思考。', note: '考察手动操作能力' },
          { q: '手动回滚需要多长时间？', a: '取决于事先准备。如果有预置脚本和文档，K8s 回滚 1-2 分钟，EC2 回滚 5-15 分钟（取决于主机数量）。如果没有准备，可能需要 30 分钟以上。这就是为什么需要提前准备手动回滚方案。', note: '考察对时间预算的认识' },
        ],
      },
      {
        chain: '通信协调',
        steps: [
          { q: '事故期间怎么通知团队？', a: '1) 建立事故沟通群（如 Slack/钉钉专属频道）；2) 指定事故指挥官（Incident Commander）统一协调；3) 定期更新进展（如每15分钟汇报一次）；4) 通知相关方（客服、产品、管理层）。', note: '考察事故沟通能力' },
          { q: '怎么跟老板汇报？', a: '1) 第一时间汇报——不要隐瞒；2) 说明影响范围、当前状态、预计恢复时间；3) 定期更新进展；4) 事后提交详细的事故报告。诚实和透明比完美更重要。', note: '考察向上沟通能力' },
        ],
      },
      {
        chain: '心理压力',
        steps: [
          { q: '你经历过事故现场的高压环境吗？', a: '（如实回答）如果有，描述当时的感受和应对方式。如果没有，说明你了解高压环境下的应对原则：保持冷静、按步骤操作、不要一个人扛、寻求帮助。', note: '考察心理素质' },
          { q: '怎么避免慌乱中做出错误决策？', a: '1) 有预置的应急手册，按步骤操作；2) 每个操作都 double-check；3) 两人操作制——一人操作、一人检查；4) 不确定的操作先在小范围验证。', note: '考察决策质量保障' },
        ],
      },
      {
        chain: '最低保障',
        steps: [
          { q: '有没有最后的保障方案？', a: '1) 基础设施快照——定期备份基础设施状态，紧急情况下可以恢复；2) 灾备环境——预置灾备环境，紧急情况下切换；3) 降级方案——关闭非核心功能，确保核心功能可用。', note: '考察兜底方案设计' },
          { q: '如果连最低保障都失效了呢？', a: '那就到了最极端的情况——服务完全不可用。此时需要：1) 向用户公开故障信息（如 Status Page）；2) 动员所有资源修复；3) 接受损失并做好事后补偿。这种极端情况虽然罕见，但预案必须覆盖。', note: '考察最坏情况接受度' },
        ],
      },
    ],
    commonMistakes: (
      <div>
        <Paragraph><Text strong>常见破绽分析：</Text></Paragraph>
        <ul>
          <li><Text type="danger">「自动回滚不可能全部失败」</Text>——过于乐观，忽略了极端情况的可能性</li>
          <li><Text type="danger">「我会立刻手动修复」</Text>——没有具体操作步骤，缺乏实操经验</li>
          <li><Text type="danger">忽略通信和协调</Text>——只关注技术操作，忽略了事故管理中的组织协调</li>
        </ul>
      </div>
    ),
    ifStuck: (
      <Paragraph>
        <Text strong>如果被问住了：</Text>「这是最极端的情况。从我的理解来看，当自动化手段都失效时，需要回到最基本的手动操作——直接操作 K8s API、服务器、负载均衡器。同时需要做好事故沟通和团队协调。关键是要提前准备手动操作文档和应急方案，避免紧急情况下临时思考。」
      </Paragraph>
    ),
  },
];

/* =============================================================================
 * 四、场景面试题（~10道，含 STAR 框架）
 * ============================================================================= */

export const scenarioQuestions = [
  {
    key: 's1',
    label: '双11支付系统发布',
    title: '双11支付系统发布方案',
    scenario: (
      <div>
        <Paragraph>
          你负责一个日活千万的支付系统，双11前需要上线新支付流程。这是一个高风险变更，任何故障都可能导致数千万的交易损失。你需要设计一个完整的发布方案，确保新支付流程安全上线。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>高风险发布策略选择（灰度/蓝绿/滚动）</li>
          <li>发布前的充分验证（预发环境、压测、安全测试）</li>
          <li>发布中和发布后的监控告警</li>
          <li>回滚方案和应急预案</li>
          <li>与业务团队的协调沟通</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>日活千万支付系统，双11前需要上线新支付流程，高风险变更，任何故障损失巨大。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>设计一个安全可靠的发布方案，确保新支付流程平稳上线，最小化风险。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>发布前准备：</Text>
            <ul>
              <li>在预发环境进行充分的压力测试（模拟双11峰值流量）</li>
              <li>进行安全审计和代码审查</li>
              <li>制定详细的回滚方案和应急预案</li>
              <li>与业务团队确认发布窗口（选择低峰时段）</li>
            </ul>
          </li>
          <li><Text strong>发布策略：</Text>灰度发布 + 分阶段放量
            <ul>
              <li>阶段一：1% 内部员工灰度，观察 30 分钟</li>
              <li>阶段二：5% 普通用户灰度，观察 1 小时</li>
              <li>阶段三：20% 用户灰度，观察 2 小时</li>
              <li>阶段四：50% 用户灰度，观察 4 小时</li>
              <li>阶段五：100% 全量</li>
            </ul>
          </li>
          <li><Text strong>监控保障：</Text>
            <ul>
              <li>实时监控错误率、延迟、成功率、交易量</li>
              <li>设置自动回滚阈值（错误率 {'>'} 1%、P99 延迟 {'>'} 500ms）</li>
              <li>安排专人值班，实时关注监控大盘</li>
            </ul>
          </li>
          <li><Text strong>应急预案：</Text>
            <ul>
              <li>一键回滚按钮，任何阶段出现问题立即回滚</li>
              <li>备用支付通道，回滚期间使用备用通道</li>
              <li>事故沟通预案，问题发生时第一时间通知相关方</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>新支付流程分 5 个阶段逐步上线，每个阶段都经过充分观察。整个发布过程持续约 8 小时，期间未出现任何故障，成功完成双11前的支付系统升级。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>选择了灰度发布策略（不是滚动更新或蓝绿部署）</li>
          <li>分阶段放量，每个阶段有明确的观察时间和放量比例</li>
          <li>有完整的监控和自动回滚机制</li>
          <li>考虑了应急预案和备用方案</li>
          <li>有具体的数字和指标，不是泛泛而谈</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「直接全量发布，双11前做了充分测试」——忽略了灰度发布的重要性</li>
          <li>「用蓝绿部署，出问题切回来」——忽略了蓝绿部署中数据库兼容性的挑战</li>
          <li>没有具体的监控指标和回滚阈值</li>
          <li>没有考虑应急预案和备用方案</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果灰度到 5% 时发现错误率上升了 0.5%，要不要回滚？', a: '需要分析：0.5% 的错误率上升是否在可接受范围内？是新功能导致的还是正常波动？如果确认是新功能导致的，即使只有 0.5% 也应该回滚——支付系统的错误容忍度极低。' },
      { q: '如果双11当天发现新支付流程有问题，但回滚可能会中断交易，怎么办？', a: '这是最艰难的选择。原则：安全优先于速度。如果问题严重（如钱款错误），必须回滚。如果问题轻微（如性能稍慢），可以暂时保持运行，双11后再修复。需要根据问题严重程度和业务影响来决策。' },
      { q: '你的灰度比例是怎么确定的？', a: '基于统计需求：1% 可验证基本功能，5% 可暴露性能问题，20% 可验证规模化下的稳定性。每个阶段的比例和观察时间都是基于风险递减的原则——越早阶段风险越小，越晚阶段验证越充分。' },
    ],
  },
  {
    key: 's2',
    label: '单体到微服务迁移',
    title: '单体到微服务架构迁移的发布系统改造',
    scenario: (
      <div>
        <Paragraph>
          公司决定从单体架构迁移到微服务架构。原来只有一个服务的发布系统，现在需要支持 30+ 个微服务的独立发布。发布系统需要做哪些改造？
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>微服务发布的核心挑战识别</li>
          <li>发布系统的架构改造方案</li>
          <li>服务依赖管理和发布编排</li>
          <li>分阶段迁移策略</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>公司从单体架构迁移到微服务，发布系统需要支持 30+ 微服务的独立发布。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>改造发布系统以支持微服务架构的独立发布、依赖管理、并行发布。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>独立发布能力：</Text>每个微服务有独立的发布配置、发布流水线、发布历史，互不影响</li>
          <li><Text strong>依赖管理：</Text>建立服务依赖拓扑图，在发布前检查依赖服务的版本兼容性</li>
          <li><Text strong>发布编排：</Text>支持定义多服务的发布顺序和依赖条件，被依赖的服务先发布</li>
          <li><Text strong>API 版本化：</Text>每个服务支持 API 版本化，确保新旧版本可以共存</li>
          <li><Text strong>契约测试：</Text>在发布前运行契约测试，验证服务间的接口兼容性</li>
          <li><Text strong>分阶段迁移：</Text>不是一次性迁移所有服务，而是逐步将服务从单体中拆分出来</li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>发布系统成功支持 30+ 微服务的独立发布，服务间依赖关系清晰，发布编排自动化，迁移过程平滑无重大故障。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>识别了微服务发布的核心挑战（依赖管理、发布编排、API 兼容性）</li>
          <li>提出了分阶段迁移策略，不是一次性切换</li>
          <li>提到了契约测试和 API 版本化</li>
          <li>有具体的改造方案，不是泛泛而谈</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「每个服务独立发布就行了」——忽略了服务间依赖关系</li>
          <li>「一次性全部迁移完」——忽略了迁移风险</li>
          <li>没有提到契约测试和 API 兼容性</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '迁移过程中，单体服务和微服务如何共存？', a: '使用 API 网关做路由——将不同的 API 路径路由到单体或微服务。同时使用数据库迁移策略（如分阶段 Schema 变更），确保单体和新微服务都能访问数据库。' },
      { q: '如果迁移过程中发现某个微服务有严重 Bug，怎么处理？', a: '1) 回滚该微服务到旧版本；2) 如果旧版本是单体中的功能，将流量切回单体；3) 评估影响范围，通知依赖该微服务的其他服务。' },
    ],
  },
  {
    key: 's3',
    label: '线上CPU飙升排查',
    title: '线上 CPU 飙升，疑似发布引入的问题',
    scenario: (
      <div>
        <Paragraph>
          线上突然 CPU 飙升到 90%+，初步判断是最近一次发布引入的。你需要快速排查问题并决定是回滚还是修复。请描述你的排查和处理步骤。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>应急响应流程（先止血还是先分析）</li>
          <li>排查思路和工具使用</li>
          <li>回滚决策的判断依据</li>
          <li>与团队的沟通协作</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>线上 CPU 飙升到 90%+，疑似最近发布引入的问题。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>快速排查问题，决定回滚还是修复，尽快恢复服务。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>立即评估（0-1 分钟）：</Text>
            <ul>
              <li>查看错误率、延迟、用户影响面</li>
              <li>判断是否需要立即回滚</li>
            </ul>
          </li>
          <li><Text strong>决策（1-2 分钟）：</Text>
            <ul>
              <li>如果错误率飙升或服务不可用 → 立即回滚</li>
              <li>如果只是 CPU 高但服务正常 → 保留现场，先排查</li>
            </ul>
          </li>
          <li><Text strong>排查（如果保留现场）：</Text>
            <ul>
              <li>查看 CPU 分布——哪个进程/线程消耗 CPU</li>
              <li>使用 profiler（如 pprof、async-profiler）分析 CPU 热点</li>
              <li>查看最近发布的代码变更</li>
              <li>对比新旧版本的 CPU 使用差异</li>
            </ul>
          </li>
          <li><Text strong>修复（如果确认是代码问题）：</Text>
            <ul>
              <li>立即回滚到上一个版本</li>
              <li>修复代码后重新发布</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过快速排查，确认是新增的缓存逻辑导致 CPU 飙升，立即回滚恢复服务。事后修复代码并重新发布。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>先评估影响，再决定排查还是回滚——「先止血，再分析」</li>
          <li>使用了具体的排查工具和方法（profiler、CPU 热点分析）</li>
          <li>有明确的回滚决策标准</li>
          <li>有时间线意识，每个步骤都有时间预估</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「先排查问题，找到根因再决定」——忽略了时间窗口，可能让问题持续影响用户</li>
          <li>「直接回滚」——没有评估影响，每次都回滚可能过于保守</li>
          <li>没有具体的排查工具和方法</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果 CPU 飙升但没有影响用户，要不要回滚？', a: '不需要立即回滚，但需要排查。CPU 高可能预示潜在问题（如慢查询、死循环），如果不处理可能随着流量增加而恶化。设置观察时间窗口，如果 CPU 持续升高，再考虑回滚。' },
      { q: '如果排查后发现不是发布引入的问题，怎么办？', a: '这是常见情况——发布和问题只是时间上的巧合，而非因果关系。需要扩大排查范围：是否有流量突增？是否有依赖服务异常？是否有基础设施问题？同时通知团队，这个问题不是发布导致的。' },
    ],
  },
  {
    key: 's4',
    label: '100个Pod零停机Schema变更',
    title: '100 个 Pod 零停机 Schema 变更',
    scenario: (
      <div>
        <Paragraph>
          核心服务有 100 个 Pod 分布在 5 个可用区，需要做数据库 Schema 变更（新增必填字段）。要求零停机，且任意时刻服务都可用。请设计发布方案。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>数据库 Schema 变更的分阶段方案</li>
          <li>滚动更新中数据库兼容性处理</li>
          <li>大规模集群的发布策略</li>
          <li>零停机要求下的风险控制</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>核心服务 100 个 Pod，5 个可用区，需要数据库 Schema 变更（新增必填字段），要求零停机。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>设计一个零停机的数据库 Schema 变更发布方案。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>阶段一：兼容性变更（提前执行，不影响现有服务）</Text>
            <ul>
              <li>添加新字段，设置为允许 NULL 或提供默认值</li>
              <li>旧代码忽略新字段，正常读写</li>
            </ul>
          </li>
          <li><Text strong>阶段二：滚动更新部署新代码</Text>
            <ul>
              <li>使用滚动更新策略，每次更新少量 Pod</li>
              <li>新代码写入新字段，同时兼容旧代码的读取</li>
              <li>由于字段允许 NULL/有默认值，新旧代码都能正常工作</li>
            </ul>
          </li>
          <li><Text strong>阶段三：数据回填</Text>
            <ul>
              <li>对历史数据执行回填脚本，为新增字段填充默认值</li>
            </ul>
          </li>
          <li><Text strong>阶段四：设置约束</Text>
            <ul>
              <li>确认所有 Pod 已更新为新版本后，将新字段设置为 NOT NULL</li>
              <li>此阶段需要确保旧代码已完全下线</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过四阶段变更，实现了零停机的数据库 Schema 变更。每个阶段都可以安全回滚，服务在变更过程中始终可用。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>采用了分阶段变更方案，不是一次性变更</li>
          <li>每个阶段都兼容上一个版本，确保可回滚</li>
          <li>考虑了数据回填和约束设置</li>
          <li>有明确的零停机保障措施</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「停机维护窗口做变更」——违反了零停机要求</li>
          <li>「一次性添加字段 + 部署新代码」——忽略了新旧代码共存的兼容性问题</li>
          <li>没有考虑数据回填和回滚方案</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果历史数据量很大，回填脚本需要跑几个小时怎么办？', a: '1) 分批回填，避免影响线上服务；2) 在低峰时段执行；3) 使用异步任务队列；4) 如果数据量太大，可以考虑使用「懒回填」——新代码在读取旧数据时动态填充默认值。' },
      { q: '如果阶段四设置 NOT NULL 时发现还有 NULL 值怎么办？', a: '说明阶段三的回填脚本有遗漏或执行不完整。需要：1) 暂停设置约束；2) 排查遗漏原因；3) 补充回填遗漏数据；4) 重新执行约束设置。这也是为什么分阶段变更很重要——每个阶段都是安全的。' },
    ],
  },
  {
    key: 's5',
    label: '新同事误回滚',
    title: '新同事误回滚到一个月前版本',
    scenario: (
      <div>
        <Paragraph>
          新同事误操作，把生产环境回滚到了一个月前的版本。一个月前的版本缺少很多功能，而且数据库 Schema 已经不兼容了。你需要立即处理这个事故。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>事故应急响应能力</li>
          <li>数据库兼容性处理</li>
          <li>权限控制和安全防护反思</li>
          <li>团队管理和新人培训</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>新同事误操作将生产环境回滚到一个月前版本，数据库 Schema 不兼容。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>立即恢复服务到最新版本，最小化影响，事后改进防止再发生。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>立即恢复（0-5 分钟）：</Text>
            <ul>
              <li>找到最近一次正确的发布单，获取正确的版本号</li>
              <li>重新发布最新版本到生产环境</li>
              <li>如果数据库出现不兼容错误，先以只读模式运行，防止数据损坏</li>
            </ul>
          </li>
          <li><Text strong>评估影响（5-15 分钟）：</Text>
            <ul>
              <li>检查数据库是否有新数据写入（旧版本可能写入了不兼容的数据）</li>
              <li>检查用户是否受到影响——功能缺失、数据异常</li>
            </ul>
          </li>
          <li><Text strong>事后改进：</Text>
            <ul>
              <li>权限控制——新同事为什么有生产环境回滚权限？</li>
              <li>回滚确认——回滚操作应该有二次确认和风险提示</li>
              <li>新人培训——加强新人培训，生产环境操作必须有人监督</li>
              <li>操作审计——所有生产环境操作都应该有审计记录</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>5 分钟内恢复服务，数据库未受到不可逆损害。事后改进了权限控制和新人培训流程，防止类似事故再次发生。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>优先恢复服务，再分析影响</li>
          <li>考虑数据库兼容性问题</li>
          <li>有事后改进措施（权限、培训、流程）</li>
          <li>对新人没有过度追责，而是改进流程</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「追究新同事责任」——问题根源是流程和权限控制，不是个人</li>
          <li>「重新发布最新版本就行了」——忽略了数据库兼容性问题</li>
          <li>没有事后改进措施</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '你怎么避免以后再发生类似事故？', a: '1) 权限控制——生产环境回滚操作需要审批；2) 二次确认——回滚操作前弹出确认框，明确显示回滚的版本和时间；3) 操作指南——制定标准操作流程文档；4) 回滚限制——限制回滚的时间范围（如只能回滚到最近 7 天内的版本）。' },
      { q: '如果数据库已经损坏了怎么办？', a: '1) 从备份恢复数据库；2) 评估备份时间点之后的数据丢失量；3) 通过日志回放补充丢失的数据；4) 如果无法恢复，需要通知用户并做好补偿方案。这是最坏情况，应该通过分阶段 Schema 变更来避免。' },
    ],
  },
  {
    key: 's6',
    label: '跨区域发布',
    title: '跨区域发布策略设计',
    scenario: (
      <div>
        <Paragraph>
          应用部署在东京、新加坡、法兰克福三个区域，每个区域有独立的数据库和 K8s 集群。需要设计一个安全的跨区域发布策略，确保发布过程中全球用户都能正常使用服务。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>跨区域发布的顺序和策略</li>
          <li>区域间数据一致性</li>
          <li>流量管理和故障隔离</li>
          <li>回滚策略</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>应用部署在东京、新加坡、法兰克福三个区域，每个区域独立。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>设计安全的跨区域发布策略，确保全球服务可用。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>发布顺序：</Text>按风险递增顺序发布——先发布时区较晚、流量较小的区域
            <ul>
              <li>第一站：新加坡（流量较小，作为试点）</li>
              <li>第二站：法兰克福</li>
              <li>第三站：东京（流量最大，最后发布）</li>
            </ul>
          </li>
          <li><Text strong>区域间隔离：</Text>
            <ul>
              <li>每个区域发布完成并观察稳定后（至少 30 分钟），再发布下一个区域</li>
              <li>如果某个区域发布出现问题，只影响该区域用户，其他区域正常</li>
            </ul>
          </li>
          <li><Text strong>全球流量管理：</Text>
            <ul>
              <li>使用 Global Load Balancer（如 AWS Route 53、Cloudflare）管理全球流量</li>
              <li>发布某个区域时，可以将该区域流量临时切换到其他区域</li>
            </ul>
          </li>
          <li><Text strong>数据一致性：</Text>
            <ul>
              <li>由于每个区域有独立数据库，不需要担心跨区域 Schema 兼容性</li>
              <li>但需要确保所有区域的 Schema 变更同步执行</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过逐区域发布，每次发布风险可控。即使某个区域发布失败，也只影响该区域用户，其他区域正常运行。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>有明确的区域发布顺序和理由</li>
          <li>考虑了区域间故障隔离</li>
          <li>有全球流量管理方案</li>
          <li>每个区域发布后有观察期</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「三个区域同时发布」——故障可能同时影响所有用户</li>
          <li>没有考虑区域发布顺序的合理性</li>
          <li>没有考虑全球流量管理</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果新加坡发布失败，法兰克福和东京要不要发布？', a: '不发布。暂停发布计划，分析新加坡失败的原因。如果问题与区域无关（如代码 Bug），其他区域也会遇到同样的问题。如果问题与区域相关（如配置差异），可以评估后继续发布其他区域。' },
      { q: '跨区域发布需要多长时间？如果业务等不了怎么办？', a: '三个区域逐次发布，每个区域观察 30 分钟，总计约 2-3 小时。如果业务等不了，可以缩短观察期（如 15 分钟），但需要更密集的监控。同时可以并行发布低风险区域，缩短总时间。' },
    ],
  },
  {
    key: 's7',
    label: '大促前紧急修复',
    title: '双11前一天紧急修复',
    scenario: (
      <div>
        <Paragraph>
          双11前一天发现支付核心 Bug，必须在 2 小时内上线修复。但正常的发布流程（含审批）需要 4 小时。你需要在不影响双11稳定性的前提下，尽快上线修复。请给出你的方案。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>紧急发布流程设计</li>
          <li>紧急修复与稳定性的平衡</li>
          <li>风险控制和验证策略</li>
          <li>沟通协调能力</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>双11前一天发现支付核心 Bug，必须在 2 小时内上线，但正常流程需要 4 小时。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>在 2 小时内安全上线修复，不影响双11稳定性。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>走紧急发布通道：</Text>
            <ul>
              <li>触发紧急发布流程，绕过常规审批</li>
              <li>同时通知技术负责人和相关方（不要等审批）</li>
            </ul>
          </li>
          <li><Text strong>加速构建和测试：</Text>
            <ul>
              <li>使用快速发布模式，跳过不必要的构建步骤</li>
              <li>运行核心测试用例（冒烟测试），跳过非核心测试</li>
              <li>在预发环境快速验证（缩短验证时间，但保留关键验证）</li>
            </ul>
          </li>
          <li><Text strong>分阶段发布：</Text>
            <ul>
              <li>先灰度发布 5% 流量，观察 15 分钟</li>
              <li>指标正常后扩大到 50%，再观察 10 分钟</li>
              <li>最终全量发布</li>
            </ul>
          </li>
          <li><Text strong>风险控制：</Text>
            <ul>
              <li>准备回滚脚本，确保 1 分钟内可以回滚</li>
              <li>安排专人监控，随时准备手动回滚</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>在 1.5 小时内完成紧急修复上线，双11当天支付系统稳定运行。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>使用了紧急发布通道，而不是等待审批</li>
          <li>加速但不放弃验证——保留核心测试和灰度发布</li>
          <li>有回滚预案和监控保障</li>
          <li>有时间线意识，每个步骤有时间预估</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「等审批通过再发布」——2 小时内无法完成 4 小时的流程</li>
          <li>「直接全量发布，因为修复很简单」——忽略了修复带来的新风险</li>
          <li>「跳过所有测试，直接上线」——风险太高，可能引入新问题</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果紧急修复本身引入了新 Bug 怎么办？', a: '这就是为什么即使紧急发布也要保留灰度验证。如果灰度阶段发现新问题，立即回滚。如果全量后才发现，立即回滚并评估——是修复 Bug 更重要，还是保留旧 Bug 等双11后再修复？' },
      { q: '你怎么说服技术负责人同意跳过审批？', a: '用数据说话：1) 说明 Bug 的影响范围和严重程度；2) 说明修复方案和风险控制措施；3) 说明不修复的后果（双11可能出现支付故障）；4) 承诺事后补审批和复盘。' },
    ],
  },
  {
    key: 's8',
    label: '发布系统从零搭建',
    title: '从零搭建发布系统',
    scenario: (
      <div>
        <Paragraph>
          你加入一家创业公司，目前部署方式是开发者手动 SSH 到服务器上传代码。需要从零搭建发布系统。请给出你的技术选型、分阶段建设计划和优先级排序。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>技术选型能力和架构设计</li>
          <li>分阶段建设思维（MVP → 完善 → 优化）</li>
          <li>优先级排序（什么最重要？什么可以后做？）</li>
          <li>创业公司场景下的资源约束考虑</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>创业公司，目前手动 SSH 部署，需要从零搭建发布系统。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>在资源有限的情况下，分阶段搭建发布系统。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>第一阶段（1-2 周）：最基本的 CI/CD</Text>
            <ul>
              <li>使用 GitHub Actions / GitLab CI 实现自动化构建</li>
              <li>自动化部署到开发/测试环境</li>
              <li>目标：消除手动构建和部署</li>
            </ul>
          </li>
          <li><Text strong>第二阶段（1 个月）：发布管理</Text>
            <ul>
              <li>引入发布系统（如自研或开源的 Spug/Jenkins）</li>
              <li>支持多环境部署（开发/测试/生产）</li>
              <li>基本的发布历史和回滚能力</li>
              <li>目标：发布流程标准化</li>
            </ul>
          </li>
          <li><Text strong>第三阶段（2-3 个月）：高级能力</Text>
            <ul>
              <li>容器化部署（Docker + K8s）</li>
              <li>灰度发布、蓝绿部署</li>
              <li>审批流程</li>
              <li>监控告警集成</li>
              <li>目标：降低发布风险，提升发布效率</li>
            </ul>
          </li>
          <li><Text strong>第四阶段（持续迭代）：平台化</Text>
            <ul>
              <li>自服务发布平台</li>
              <li>多租户支持</li>
              <li>DORA 指标监控</li>
              <li>目标：发布系统成为团队的效率平台</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过分阶段建设，逐步提升发布能力。每个阶段都有明确的交付价值和风险控制。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>有明确的分阶段计划，每个阶段有目标和时间</li>
          <li>优先级合理——先解决最痛的问题（手动部署）</li>
          <li>考虑创业公司的资源约束（不追求完美，追求实用）</li>
          <li>技术选型有理由，不是盲目选择</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「直接用 K8s + Istio + Spinnaker」——创业公司没有资源维护这么复杂的系统</li>
          <li>「一步到位，搭建完美的发布系统」——忽略了分阶段建设的必要性</li>
          <li>没有考虑团队规模和资源约束</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '为什么第一阶段选择 GitHub Actions 而不是 Jenkins？', a: '创业公司资源有限，GitHub Actions 是 SaaS 服务，不需要自己维护服务器。Jenkins 需要自己部署和维护，初期成本高。等团队规模扩大后，可以考虑迁移到更灵活的 Jenkins 或其他方案。' },
      { q: '如果团队只有 3 个开发，还需要发布系统吗？', a: '需要，但可以更简单。3 个人的团队可能不需要复杂的审批流程和灰度发布，但自动化构建和部署仍然有价值——减少手动操作、避免「在我机器上能跑」的问题。关键是选择适合团队规模的方案，而不是过度设计。' },
    ],
  },
  {
    key: 's9',
    label: '合规审计',
    title: 'ISO 27001 合规审计',
    scenario: (
      <div>
        <Paragraph>
          公司要过 ISO 27001 审计，发布系统需要满足哪些合规要求？现有发布系统可能缺少哪些能力？如何进行改造？
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>对 ISO 27001 合规要求的理解</li>
          <li>发布系统的合规改造方案</li>
          <li>安全与效率的平衡</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>公司需要过 ISO 27001 审计，发布系统需要满足合规要求。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>识别发布系统需要的合规改造，制定改造计划。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>权限控制：</Text>
            <ul>
              <li>最小权限原则——每个人只能访问必要的资源</li>
              <li>权限分离——开发、审批、执行由不同角色完成</li>
              <li>定期权限审计——检查是否有不必要的权限</li>
            </ul>
          </li>
          <li><Text strong>操作审计：</Text>
            <ul>
              <li>所有发布操作都要记录审计日志</li>
              <li>审计日志不可篡改，保留至少 1 年</li>
              <li>支持审计报告导出</li>
            </ul>
          </li>
          <li><Text strong>变更管理：</Text>
            <ul>
              <li>所有变更都有变更记录（变更内容、变更人、变更时间）</li>
              <li>关键变更需要审批</li>
              <li>变更窗口管理</li>
            </ul>
          </li>
          <li><Text strong>密钥管理：</Text>
            <ul>
              <li>密钥不硬编码、不提交到 Git</li>
              <li>使用密钥管理系统</li>
              <li>密钥定期轮换</li>
            </ul>
          </li>
          <li><Text strong>制品安全：</Text>
            <ul>
              <li>制品签名验证</li>
              <li>镜像漏洞扫描</li>
              <li>供应链安全（SBOM）</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过系统化的合规改造，发布系统满足 ISO 27001 审计要求，同时不影响日常发布效率。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>覆盖了权限、审计、变更管理、密钥管理、制品安全等多个维度</li>
          <li>有具体的改造措施，不是泛泛而谈</li>
          <li>考虑了合规与效率的平衡</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「我们系统已经很安全了，不需要改造」——缺乏合规意识</li>
          <li>只提了一个方面（如审计日志），忽略了其他维度</li>
          <li>没有考虑合规对效率的影响</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '合规要求会不会拖慢发布速度？', a: '会，但可以平衡。核心操作（如代码提交、构建）不受影响，合规主要影响的是流程环节（如审批、审计）。可以通过自动化减少合规的人力成本——如自动审计日志收集、自动权限检查。' },
      { q: '如果审计发现发布系统不合规，但改造需要 3 个月，审计 deadline 只剩 1 个月怎么办？', a: '1) 优先改造最关键的不合规项（如权限控制、审计日志）；2) 对暂时无法改造的部分，制定补偿控制措施（如人工检查）；3) 与审计师沟通，说明改造计划和临时措施。' },
    ],
  },
  {
    key: 's10',
    label: '发布导致数据损坏',
    title: '发布导致用户数据损坏',
    scenario: (
      <div>
        <Paragraph>
          一次发布导致用户数据损坏，且数据无法通过回滚恢复。这是最严重的事故之一。你需要立即处理，并给出长期预防方案。
        </Paragraph>
      </div>
    ),
    testPoints: (
      <div>
        <Paragraph><Text strong>考察点：</Text></Paragraph>
        <ul>
          <li>数据损坏事故的应急响应</li>
          <li>数据恢复方案</li>
          <li>用户沟通和补偿</li>
          <li>长期预防措施</li>
        </ul>
      </div>
    ),
    starFramework: (
      <div>
        <Paragraph><Text strong>Situation（情境）：</Text>发布导致用户数据损坏，回滚无法恢复数据。</Paragraph>
        <Paragraph><Text strong>Task（任务）：</Text>立即止损，恢复数据，沟通用户，建立长期预防机制。</Paragraph>
        <Paragraph><Text strong>Action（行动）：</Text></Paragraph>
        <ol>
          <li><Text strong>立即止损（0-5 分钟）：</Text>
            <ul>
              <li>立即回滚代码，停止数据损坏的持续发生</li>
              <li>如果有必要，暂时关闭写入功能</li>
            </ul>
          </li>
          <li><Text strong>评估影响（5-30 分钟）：</Text>
            <ul>
              <li>评估数据损坏的范围和严重程度</li>
              <li>确定受影响用户数量和数据类型</li>
            </ul>
          </li>
          <li><Text strong>数据恢复（30 分钟-数小时）：</Text>
            <ul>
              <li>从数据库备份恢复数据（Point-in-Time Recovery）</li>
              <li>如果备份不能完全恢复，通过日志回放补充</li>
              <li>如果无法恢复，从其他数据源重建（如缓存、消息队列）</li>
            </ul>
          </li>
          <li><Text strong>用户沟通：</Text>
            <ul>
              <li>通过 Status Page 公开事故信息</li>
              <li>通知受影响用户</li>
              <li>制定用户补偿方案</li>
            </ul>
          </li>
          <li><Text strong>长期预防：</Text>
            <ul>
              <li>发布前数据备份——每次发布前自动备份数据库</li>
              <li>数据库变更分阶段执行——不允许一次性不兼容变更</li>
              <li>数据写入保护——关键数据操作需要二次确认</li>
              <li>发布前数据影响评估——评估发布对数据的潜在影响</li>
            </ul>
          </li>
        </ol>
        <Paragraph><Text strong>Result（结果）：</Text>通过数据库备份恢复和数据修复，最大程度恢复了受损数据。事后建立了完善的发布前数据备份和变更审核机制。</Paragraph>
      </div>
    ),
    scoringCriteria: (
      <div>
        <Paragraph><Text strong>好回答的特征：</Text></Paragraph>
        <ul>
          <li>先止损，再评估，后恢复——有清晰的应急流程</li>
          <li>有数据恢复的具体方案（备份、日志回放、数据重建）</li>
          <li>考虑了用户沟通和补偿</li>
          <li>有长期预防措施</li>
        </ul>
        <Paragraph style={{ marginTop: 8 }}><Text strong>差回答的特征：</Text></Paragraph>
        <ul>
          <li>「数据损坏了没办法恢复」——缺乏数据恢复意识</li>
          <li>「回滚代码就行了」——忽略了数据已经损坏的事实</li>
          <li>没有考虑用户沟通和补偿</li>
        </ul>
      </div>
    ),
    followUpPredictions: [
      { q: '如果数据库备份也有问题，无法恢复怎么办？', a: '这是最坏情况。需要从其他数据源重建：1) 应用日志中的操作记录；2) 缓存中的数据；3) 消息队列中的未处理消息；4) 第三方服务的数据（如支付记录）。如果都无法恢复，需要诚实告知用户并制定补偿方案。', note: '考察最坏情况处理' },
      { q: '你怎么确保以后不再发生类似问题？', a: '1) 发布前数据备份自动化——每次发布前自动执行数据库备份；2) 数据库变更审核——所有数据库变更必须经过审核；3) 分阶段变更——数据库变更分阶段执行，每个阶段可回滚；4) 数据写入保护——关键数据操作增加防误操作机制。', note: '考察长期预防机制' },
    ],
  },
];

/* =============================================================================
 * 五、面试技巧总结
 * ============================================================================= */

export const interviewTips = (
  <div>
    <Title level={4}>发布系统面试技巧总结</Title>

    <Card title="1. 回答结构：金字塔原理" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        <Text strong>直接答案 → 详细解释 → 扩展思考</Text>
      </Paragraph>
      <ul>
        <li><Text strong>第一层（直接答案）：</Text>用一句话直接回答问题。如「滚动更新和蓝绿部署的核心区别在于：滚动是逐步替换实例，蓝绿是环境切换。」</li>
        <li><Text strong>第二层（详细解释）：</Text>展开说明原理、过程、关键参数。如「滚动更新通过 maxSurge 和 maxUnavailable 控制替换速度...」</li>
        <li><Text strong>第三层（扩展思考）：</Text>补充相关知识点、对比、最佳实践。如「在实际项目中，80% 的场景使用滚动更新就够了...」</li>
      </ul>
    </Card>

    <Card title="2. 用数据说话" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        面试中引用具体数据和指标，会显著提升专业度。
      </Paragraph>
      <ul>
        <li><Text strong>DORA 指标：</Text>「精英团队的部署频率是每天多次，变更前置时间小于 1 小时」</li>
        <li><Text strong>具体数字：</Text>「灰度发布从 1% 开始，每个阶段观察 10-30 分钟」</li>
        <li><Text strong>行业案例：</Text>「Netflix 每天部署数千次，使用红黑部署策略」</li>
        <li><Text strong>个人经验：</Text>「我们的发布系统支持同时发布 200+ 台主机，通过分批并发控制」</li>
      </ul>
    </Card>

    <Card title="3. 对比类问题用表格" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        遇到对比类问题（如「滚动更新 vs 蓝绿部署」），用表格或结构化框架回答会更清晰。
      </Paragraph>
      <ul>
        <li>先列出对比维度（资源需求、回滚速度、风险等级、适用场景）</li>
        <li>再逐维度对比两个方案</li>
        <li>最后给出选择建议</li>
      </ul>
      <Paragraph>
        <Text type="secondary">示例：从「资源需求」「回滚速度」「风险等级」「适用场景」四个维度对比滚动更新和蓝绿部署。</Text>
      </Paragraph>
    </Card>

    <Card title="4. 展示实际经验" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        用 STAR 框架（情境-任务-行动-结果）描述你的实际项目经验。
      </Paragraph>
      <ul>
        <li><Text strong>不要只说「我们用了灰度发布」</Text></li>
        <li><Text strong>要说「在我们的项目中，我们遇到过高风险变更场景，我们采用了灰度发布策略，从 5% 开始逐步放量，每个阶段观察 15 分钟，最终安全完成全量发布」</Text></li>
      </ul>
    </Card>

    <Card title="5. 主动提缺点和局限" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        只说优点会显得不够全面。主动提及缺点和局限，体现全面思考。
      </Paragraph>
      <ul>
        <li>「蓝绿部署的优点是可以秒级回滚，但缺点是需要两倍资源」</li>
        <li>「滚动更新的优点是资源效率高，但缺点是回滚速度慢」</li>
        <li>「Feature Flag 的优点是灵活，但缺点是会产生 Flag 债务」</li>
      </ul>
    </Card>

    <Card title="6. 被问住时的应对策略" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        被问住不可怕，关键是如何应对。
      </Paragraph>
      <ul>
        <li><Text strong>诚实承认：</Text>「这个问题我之前没有深入思考过，但根据我的理解...」</li>
        <li><Text strong>关联已知：</Text>「虽然我不太了解 X，但我知道类似的 Y 是...」</li>
        <li><Text strong>思考过程：</Text>「如果让我来设计，我会从以下几个角度考虑...」</li>
        <li><Text strong>引导话题：</Text>「这个问题我可能回答得不够全面，但我对相关的 Z 问题比较了解，要不要聊聊那个？」</li>
        <li><Text strong>不要硬撑：</Text>不懂装懂比诚实承认更糟糕，面试官一眼就能看出来</li>
      </ul>
    </Card>

    <Card title="7. 面试节奏控制" size="small" style={{ marginBottom: 16 }}>
      <Paragraph>
        控制面试节奏，展示你的主动性。
      </Paragraph>
      <ul>
        <li><Text strong>适时提问：</Text>「这个问题您是想了解技术实现，还是想了解我的项目经验？」</li>
        <li><Text strong>引导深入：</Text>「关于这个问题，我还想补充一个实际案例...」</li>
        <li><Text strong>控制时间：</Text>每个问题的回答控制在 2-3 分钟，不要一个人讲太久</li>
        <li><Text strong>反向提问：</Text>面试结束前提问环节，准备几个有深度的问题——如「贵司的发布系统目前最大的挑战是什么？」</li>
      </ul>
    </Card>

    <Divider />

    <Alert
      type="info"
      showIcon
      message="面试准备建议"
      description={
        <div>
          <Paragraph>
            建议按照「概念 → 原理 → 对比 → 设计 → 场景」的顺序逐步深入准备：
          </Paragraph>
          <ol>
            <li><Text strong>概念层：</Text>掌握 CI/CD、部署策略、发布模式等基础概念</li>
            <li><Text strong>原理层：</Text>理解 K8s 滚动更新、蓝绿切换、灰度放量的底层原理</li>
            <li><Text strong>对比层：</Text>能清晰对比不同策略和模式的优劣</li>
            <li><Text strong>设计层：</Text>能设计一个完整的发布系统架构</li>
            <li><Text strong>场景层：</Text>能应对各种实际场景的挑战</li>
          </ol>
        </div>
      }
    />
  </div>
);