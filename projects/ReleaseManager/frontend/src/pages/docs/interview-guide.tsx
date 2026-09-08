import { Typography, Collapse } from 'antd';

const { Title } = Typography;

const qaItems = [
  {
    key: '1',
    label: '发布系统的核心功能模块有哪些？',
    children: (
      <div>
        <p>一个完整的发布系统通常包含以下核心模块：</p>
        <ul>
          <li><strong>应用管理：</strong>管理应用的基本信息、环境配置、部署配置等。</li>
          <li><strong>发布管理：</strong>创建发布单、定义发布流水线、执行发布任务。</li>
          <li><strong>审批中心：</strong>多层审批流程，支持自定义审批规则和审批人。</li>
          <li><strong>制品管理：</strong>管理构建产物（Docker 镜像、JAR 包等），支持制品晋级。</li>
          <li><strong>配置管理：</strong>模板 + 变量 + 环境差异化的配置管理方案。</li>
          <li><strong>权限管理：</strong>基于 RBAC 和组织树的细粒度权限控制。</li>
          <li><strong>环境与基础设施：</strong>管理集群、命名空间、部署配置等。</li>
          <li><strong>审计日志：</strong>记录所有操作历史，支持追溯和审计。</li>
        </ul>
        <p>Demo 实现了以上核心模块的简化版本，展示了发布系统的基本工作流程。</p>
      </div>
    ),
  },
  {
    key: '2',
    label: '权限模型如何设计？RBAC vs 组织树？',
    children: (
      <div>
        <p>权限模型设计是发布系统的关键环节，主要涉及以下两个维度：</p>
        <p><strong>RBAC（基于角色的访问控制）：</strong></p>
        <ul>
          <li>定义角色（如：管理员、开发者、运维、审批人等），每个角色关联一组权限。</li>
          <li>用户通过被赋予角色而获得相应权限，简化了权限管理。</li>
          <li>支持角色继承和角色组合，灵活应对复杂场景。</li>
        </ul>
        <p><strong>组织树：</strong></p>
        <ul>
          <li>以组织架构为基础（公司 → 部门 → 团队 → 成员），权限沿组织树继承。</li>
          <li>某部门下的应用，默认该部门成员拥有相应权限，减少重复配置。</li>
          <li>支持组织树与 RBAC 结合使用，实现更细粒度的权限控制。</li>
        </ul>
        <p><strong>Demo 实现：</strong>采用 RBAC + 组织树结合的方案，以组织树为基础权限结构，通过角色进行细粒度权限控制。支持按用户、按组、按角色三种维度配置权限。</p>
      </div>
    ),
  },
  {
    key: '3',
    label: '双镜像设计是什么？为什么要这样做？',
    children: (
      <div>
        <p><strong>双镜像设计</strong>是 CI 构建阶段的一种优化策略，将构建过程拆分为两个镜像：</p>
        <p><strong>1. 环境基础镜像（Builder Image）：</strong></p>
        <ul>
          <li>包含编译工具链（JDK、Node.js、Go、Maven、Gradle 等）。</li>
          <li>用于 CI 阶段的代码编译和构建。</li>
          <li>体积较大，但不需要频繁更新。</li>
        </ul>
        <p><strong>2. 应用基础镜像（Application Base Image）：</strong></p>
        <ul>
          <li>预装应用运行所需的环境（JRE、Python 运行时、系统依赖等）。</li>
          <li>不包含编译工具，体积小巧。</li>
          <li>作为最终运行镜像的基础层。</li>
        </ul>
        <p><strong>构建流程：</strong></p>
        <ol>
          <li>CI 阶段使用 Builder Image 编译代码，生成产物（JAR、二进制文件等）。</li>
          <li>将产物 COPY 到 Application Base Image 中，组装成最终可运行镜像。</li>
          <li>最终镜像只包含运行环境和产物，体积小、启动快、安全风险低。</li>
        </ol>
        <p><strong>优势：</strong></p>
        <ul>
          <li>最终镜像体积小，部署和拉取速度快。</li>
          <li>编译环境和运行环境解耦，运行环境稳定可靠。</li>
          <li>减少安全攻击面（运行镜像不包含编译工具）。</li>
          <li>构建缓存利用率高，加速 CI 流程。</li>
        </ul>
      </div>
    ),
  },
  {
    key: '4',
    label: 'EC2 部署 vs K8s 部署的区别？',
    children: (
      <div>
        <p><strong>EC2 部署（传统方式）：</strong></p>
        <ul>
          <li>将构建产物（JAR、WAR、zip 等）上传到 S3 或直接传输到目标服务器。</li>
          <li>目标机器拉取产物，部署到指定目录，重启应用进程。</li>
          <li>需要自行管理服务器集群、负载均衡、健康检查等。</li>
          <li>扩容和缩容需要手动操作或配合 Auto Scaling。</li>
        </ul>
        <p><strong>K8s 部署（容器化方式）：</strong></p>
        <ul>
          <li>将应用打包为 Docker 镜像，推送到镜像仓库。</li>
          <li>通过 kubectl 操作 K8s 集群，更新 Deployment 实现滚动更新。</li>
          <li>K8s 自动管理 Pod 调度、健康检查、负载均衡、自动扩缩容。</li>
          <li>支持灰度发布、蓝绿部署、滚动更新等多种发布策略。</li>
        </ul>
        <p><strong>Demo 实现：</strong>支持 EC2 和 K8s 双路径部署。EC2 路径将产物部署到目标服务器，K8s 路径通过 kubectl 更新镜像版本实现滚动更新。</p>
      </div>
    ),
  },
  {
    key: '5',
    label: '灰度发布/蓝绿部署/滚动更新的区别？',
    children: (
      <div>
        <p><strong>灰度发布（Canary Release）：</strong></p>
        <ul>
          <li>将新版本先部署到少量实例（如 10% 的流量），验证稳定后再逐步扩大范围。</li>
          <li>适合需要验证新版本兼容性和稳定性的场景。</li>
          <li>可以快速回滚，影响范围小。</li>
        </ul>
        <p><strong>蓝绿部署（Blue-Green Deployment）：</strong></p>
        <ul>
          <li>维护两套完整的环境（蓝环境 = 当前生产环境，绿环境 = 新版本环境）。</li>
          <li>绿环境验证完成后，通过切换负载均衡将流量从蓝环境切换到绿环境。</li>
          <li>切换速度快，回滚也快（切回蓝环境即可）。</li>
          <li>资源消耗大（需要同时维护两套环境）。</li>
        </ul>
        <p><strong>滚动更新（Rolling Update）：</strong></p>
        <ul>
          <li>逐个或分批替换旧版本 Pod 为新版本 Pod。</li>
          <li>K8s 默认的更新策略，过程中服务不中断。</li>
          <li>支持设置 maxSurge（最大超出实例数）和 maxUnavailable（最大不可用实例数）。</li>
          <li>资源消耗适中，但回滚速度相对较慢。</li>
        </ul>
        <p><strong>Demo 实现：</strong>流水线中的灰度发布阶段模拟了灰度发布流程，支持设置灰度比例，验证通过后进入全量发布阶段。</p>
      </div>
    ),
  },
  {
    key: '6',
    label: '制品晋级是什么？',
    children: (
      <div>
        <p><strong>制品晋级（Artifact Promotion）</strong>是指将构建产物从一个环境晋级到下一个环境的过程。</p>
        <p><strong>典型晋级流程：</strong></p>
        <ul>
          <li>开发环境（dev）→ 测试环境（test）→ 预发环境（staging）→ 生产环境（prod）</li>
          <li>每个环境晋级前需要经过验证和审批。</li>
          <li>同一份制品在不同环境中保持一致性，确保测试和生产使用相同的构建产物。</li>
        </ul>
        <p><strong>为什么要晋级而不是重新构建？</strong></p>
        <ul>
          <li>确保各环境使用完全相同的制品，避免"测试通过，生产出问题"的情况。</li>
          <li>构建过程可能因时间、依赖版本变化而产生不同的结果。</li>
          <li>晋级记录可以完整追溯制品在各环境的流转历史。</li>
        </ul>
        <p><strong>Demo 实现：</strong>制品管理模块支持查看制品信息、晋级记录，以及手动触发制品晋级操作。</p>
      </div>
    ),
  },
  {
    key: '7',
    label: '配置管理如何做？模板 + 变量 + 环境差异化？',
    children: (
      <div>
        <p>配置管理是发布系统的重要组成部分，Demo 采用"模板 + 变量 + 环境差异化"的方案：</p>
        <p><strong>配置模板：</strong></p>
        <ul>
          <li>使用 Jinja2-like 语法（如 <code>{'{{ var_name }}'}</code>）定义模板。</li>
          <li>模板中包含配置文件的骨架结构和变量占位符。</li>
          <li>支持多种模板类型：YAML、Properties、ENV、JSON、Nginx 等。</li>
        </ul>
        <p><strong>变量定义：</strong></p>
        <ul>
          <li>定义模板中使用的变量及其默认值。</li>
          <li>变量支持不同的数据类型（字符串、数字、布尔值、列表等）。</li>
        </ul>
        <p><strong>环境差异化：</strong></p>
        <ul>
          <li>每个环境（dev/test/staging/prod）可以设置不同的变量值。</li>
          <li>渲染时根据目标环境选择对应的变量值，生成最终配置文件。</li>
        </ul>
        <p><strong>配置发布：</strong></p>
        <ul>
          <li>配置变更通过发布流程进行，支持版本管理和回滚。</li>
          <li>记录配置发布的完整历史，支持版本对比。</li>
        </ul>
        <p><strong>生产环境补充：</strong>还需要考虑配置加密（敏感信息如数据库密码）、配置变更审批、配置与代码的版本一致性等。</p>
      </div>
    ),
  },
  {
    key: '8',
    label: '审批流设计',
    children: (
      <div>
        <p>审批流是发布系统的安全网关，确保变更经过必要的审核才能上线。</p>
        <p><strong>Demo 实现：</strong></p>
        <ul>
          <li>发布单提交后自动创建审批记录。</li>
          <li>审批人可以在审批中心查看待审批事项，进行通过/驳回操作。</li>
          <li>当前简化了审批人分配逻辑，统一使用应用负责人作为审批人。</li>
        </ul>
        <p><strong>真实项目设计：</strong></p>
        <ul>
          <li><strong>多层审批：</strong>根据环境级别配置不同的审批策略。例如：测试环境发布无需审批，生产环境发布需要应用负责人 + 技术经理审批。</li>
          <li><strong>审批通知：</strong>审批通知通过 IM（飞书/钉钉/企业微信）和邮件推送，支持审批人快速响应。</li>
          <li><strong>超时处理：</strong>审批超时自动审批或升级审批（转给上级）。</li>
          <li><strong>审批策略：</strong>支持一人通过即可、全员通过、按比例通过等多种审批策略。</li>
          <li><strong>审批与流水线联动：</strong>审批通过后自动触发下一阶段流水线执行。</li>
        </ul>
      </div>
    ),
  },
];

export default function DocsInterview() {
  return (
    <div style={{ maxWidth: 800 }}>
      <Title level={3}>常见面试题与回答思路</Title>
      <Collapse
        items={qaItems}
        defaultActiveKey={['1']}
        style={{ background: '#fff' }}
      />
    </div>
  );
}