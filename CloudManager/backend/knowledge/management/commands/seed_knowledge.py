"""初始化系统知识库：分类 + HTML 文档。

用法: python manage.py seed_knowledge
文档 HTML 正文落盘到 knowledge/docs/{slug}.html（文件为运行时源，不存数据库），
由前端「系统文档」详情页加载渲染（.doc-body 容器样式）。
"""
from pathlib import Path

from django.core.management.base import BaseCommand

from knowledge.models import DocCategory, DocEntry

DOCS = [
    {
        'cat': ('overview', '项目概览', '📘', 1),
        'docs': [
            {
                'slug': 'project-bg',
                'title': '项目需求与背景',
                'summary': '多云资源管理平台（Cloud Manager）的项目背景、业务目标与原系统能力短板。',
                'tags': '需求,背景,目标',
                'html': '''
<h2>一、项目整体背景与目标</h2>
<p>企业上云后普遍面临 <b>多云资源分散、口径不一、成本失控、操作不可审计</b> 四大问题。
Cloud Manager 定位为统一的多云资源管理平台（CMDB 为核心），目标是：</p>
<ul>
  <li><b>统一纳管</b>：AWS / 阿里云 / 腾讯云等异构云资源统一建模、统一视图。</li>
  <li><b>操作可控</b>：所有变更操作走工单审批，全程留痕可审计。</li>
  <li><b>成本可见</b>：账单按部门 / 应用分摊，配合规则引擎持续优化。</li>
  <li><b>数据一致</b>：CMDB 为唯一数据源，云、工单、成本均以 CMDB 为准。</li>
</ul>

<h2>二、原有系统能力与短板</h2>
<h3>业务范围</h3>
<p>覆盖资源纳管、工单审批、操作审计、成本管理、服务目录等核心能力。</p>
<h3>原有系统短板</h3>
<ul>
  <li>多云控制台割裂，无统一视图与统一建模。</li>
  <li>操作无统一审批流，无法追溯责任。</li>
  <li>成本无分摊，无法回答"谁在用、用了多少"。</li>
  <li>数据源多头，云上状态与内部 CMDB 常不一致。</li>
</ul>

<h2>三、Demo 系统建设诉求</h2>
<ul>
  <li><b>架构还原</b>：还原真实项目的四层架构与核心设计决策。</li>
  <li><b>业务闭环</b>：申请 → 工单 → 审批 → 执行 → 回写 CMDB 端到端打通。</li>
  <li><b>亮点突出</b>：依赖图谱、成本规则引擎、场景模板、数据权限等。</li>
  <li><b>演示友好</b>：全量 Mock 数据 + 可配置规则 + 系统演示模块。</li>
</ul>

<h2>四、核心诉求总结</h2>
<blockquote>一句话：<b>用 CMDB 唯一数据源，把多云资源、工单审批、成本分摊打通成一个可解释、可演示、可复盘的闭环系统。</b></blockquote>
''',
            },
        ],
    },
    {
        'cat': ('architecture', '系统架构', '🏗️', 2),
        'docs': [
            {
                'slug': 'architecture',
                'title': '系统架构设计',
                'summary': '四层架构（前端→后端→工单→CMDB）与三大核心设计决策、云适配层与数据流。',
                'tags': '架构,四层,CMDB,决策',
                'html': '''
<h2>一、总体架构：还原真实项目四层骨架</h2>
<table>
  <thead><tr><th>层级</th><th>职责</th><th>技术选型（Demo）</th></tr></thead>
  <tbody>
    <tr><td>接入层</td><td>Web / 用户交互</td><td>Vue 3 + Ant Design Vue</td></tr>
    <tr><td>业务层</td><td>资源 / 工单 / 成本 / 权限</td><td>Django REST Framework</td></tr>
    <tr><td>流程层</td><td>审批流 / 自动化任务</td><td>工单系统 + Mock Provider</td></tr>
    <tr><td>数据层</td><td>唯一数据源</td><td>CMDB（MySQL 8）</td></tr>
  </tbody>
</table>
<p>关键：<b>所有数据以 CMDB 为唯一数据源</b>，前端不直接操作云厂商，统一走后端 API。</p>

<h2>二、核心设计决策（面试重点）</h2>
<h3>决策 1：操作为什么必须走工单系统？</h3>
<ul>
  <li>变更可控：所有写操作统一入口，未审批不执行。</li>
  <li>责任可溯：操作人、审批人、执行结果全程留痕。</li>
  <li>便于接入审计 / 合规要求。</li>
</ul>
<h3>决策 2：CMDB 为什么是唯一数据源？</h3>
<ul>
  <li>云上资源与内部数据一致，避免多头维护。</li>
  <li>支持跨云统一建模（多态资源表）。</li>
  <li>成本 / 拓扑 / 权限均基于 CMDB 数据派生。</li>
</ul>
<h3>决策 3：云操作是异步长任务，如何保证最终一致？</h3>
<ol>
  <li>工单通过后提交到 <b>Mock Provider 执行队列</b>（真实系统为消息队列）。</li>
  <li>执行结果异步回写 CMDB（采集 / 回写任务）。</li>
  <li>失败可重试 / 回滚，保证最终一致。</li>
</ol>

<h2>三、云适配层设计（核心扩展点）</h2>
<p>通过 <b>Provider 适配层</b> 屏蔽云厂商差异：</p>
<ul>
  <li>统一操作接口（create / start / stop / resize / delete）。</li>
  <li>统一资源模型（Resource 多态 + 类型映射）。</li>
  <li>新增云厂商 = 新增一个 Provider 适配器，业务层无感。</li>
</ul>

<h2>四、数据流</h2>
<h3>查询链路（读）</h3>
<pre>前端 → /api/... → CMDB → 统一响应</pre>
<h3>操作链路（写）</h3>
<pre>前端 → 工单提交 → 审批通过 → Provider 执行 → 回写 CMDB → 前端刷新</pre>
''',
            },
            {
                'slug': 'permission',
                'title': '数据权限与权限中心',
                'summary': '去中心化权限中心（注册制 + 能力包）与后端强制数据范围过滤的实现。',
                'tags': '权限,数据范围,能力包',
                'html': '''
<h2>一、权限设计思路：去中心化 IAM</h2>
<p>本项目不自建权限系统，而是接入 <b>统一权限中心（Permission Center）</b>：</p>
<ul>
  <li><b>注册制</b>：应用注册后发布"能力包"（菜单 / 操作 / 数据范围）。</li>
  <li><b>申请授权</b>：用户按需申请能力包，审批通过后获得对应权限。</li>
</ul>
<table>
  <thead><tr><th>能力包</th><th>数据范围</th><th>可执行操作</th></tr></thead>
  <tbody>
    <tr><td>全量管理员</td><td>全部</td><td>读 + 写 + 审批</td></tr>
    <tr><td>部门负责人</td><td>本部门</td><td>读 + 申请</td></tr>
    <tr><td>只读用户</td><td>本部门</td><td>只读</td></tr>
  </tbody>
</table>

<h2>二、数据权限：后端强制过滤</h2>
<p>Demo 做了简化：由后端按当前用户强制过滤数据范围，而非仅前端隐藏。</p>
<ul>
  <li><b>超级管理员（admin）</b> → 数据范围：全部。</li>
  <li><b>普通员工（readonly）</b> → 数据范围：本部门（user.department）。</li>
</ul>
<pre>def _scoped_items(request):
    if request.user.is_superuser:
        return CostItem.objects.all()
    return CostItem.objects.filter(department=request.user.department)</pre>
<p>应用在成本账单、优化建议、分摊、报告等所有接口，越权维度值自动清空。</p>

<h2>三、为什么后端强制？</h2>
<ul>
  <li>前端控制可被绕过（改请求参数即可越权）。</li>
  <li>后端过滤是唯一可信边界，符合安全最佳实践。</li>
  <li>为对接真实权限中心预留：审批通过的能力包 → 数据范围映射。</li>
</ul>
''',
            },
        ],
    },
    {
        'cat': ('tech', '技术选型', '🧰', 3),
        'docs': [
            {
                'slug': 'tech-stack',
                'title': '技术选型与理由',
                'summary': '前端 Vue3、后端 Django/DRF、MySQL、规则引擎与 Mock 策略的选型依据。',
                'tags': '选型,Vue3,Django,MySQL,Mock',
                'html': '''
<h2>一、选型前提（硬约束）</h2>
<ul>
  <li>面向企业内网部署，单机 / 小型集群即可。</li>
  <li>需快速演示完整业务闭环，降低基建成本。</li>
  <li>架构上需与真实项目（Java Spring Boot）保持同构。</li>
</ul>

<h2>二、选型建议</h2>
<table>
  <thead><tr><th>领域</th><th>技术</th><th>理由</th></tr></thead>
  <tbody>
    <tr><td>前端</td><td>Vue 3 + TypeScript + Vite + Ant Design Vue</td><td>组件丰富、生态成熟、类型安全</td></tr>
    <tr><td>后端</td><td>Django 4.2 + DRF + SimpleJWT</td><td>快速建模、自带 Admin、认证完善</td></tr>
    <tr><td>数据库</td><td>MySQL 8（生产）/ SQLite（本地）</td><td>稳定通用，支持 JSON / 多表</td></tr>
    <tr><td>消息队列</td><td>RabbitMQ（真实）→ 本 Demo 用 Mock Provider 异步</td><td>异步长任务解耦</td></tr>
    <tr><td>部署</td><td>Docker Compose + Nginx</td><td>一键起多服务，便于演示</td></tr>
  </tbody>
</table>

<h2>三、关键选型理由</h2>
<h3>前端：Vue 3 + Ant Design Vue</h3>
<p>企业级组件全（表格 / 表单 / 图表联动），配合 ECharts 实现成本大屏与依赖图谱。</p>
<h3>后端：Django REST Framework</h3>
<p>ORM 建模高效、DRF 序列化 + 视图集快速出 API、自带 JWT 认证与权限体系，适合快速交付 Demo。</p>

<h2>四、Mock 策略（Demo 关键设计）</h2>
<ul>
  <li><b>数据全 Mock</b>：账号、资源、账单、建议均由 seed 脚本生成，贴近真实分布。</li>
  <li><b>Provider Mock</b>：云操作由 Mock Provider 模拟执行 + 回写 CMDB，闭环完整。</li>
  <li><b>成本模拟采集</b>：seed_metrics 写 CPU / 内存指标，供规则引擎检测。</li>
</ul>

<h2>五、暂缓 / 排除项</h2>
<ul>
  <li>真实云 SDK 对接（Demo 阶段 Mock Provider 足够）。</li>
  <li>消息队列 / 缓存中间件（异步用任务表模拟）。</li>
  <li>复杂工作流引擎（工单状态机简化实现）。</li>
</ul>
''',
            },
        ],
    },
    {
        'cat': ('database', '数据库设计', '🗄️', 4),
        'docs': [
            {
                'slug': 'database',
                'title': '数据库设计与核心表',
                'summary': 'CMDB 多态资源建模、工单系统、成本模块、服务目录的核心表结构与关系。',
                'tags': '数据库,建模,CMDB,表结构',
                'html': '''
<h2>一、总体 ER 概览</h2>
<p>四大模块：<b>CMDB（资源）</b> / <b>工单系统（流程）</b> / <b>权限审计</b> / <b>成本（账单）</b>。</p>

<h2>二、CMDB 模块</h2>
<h3>cmdb_cloud_account 云账号表</h3>
<p>云厂商、账号名、AK/SK 引用、区域列表、状态。</p>
<h3>cmdb_resource 统一资源表（多态建模核心）</h3>
<table>
  <thead><tr><th>字段</th><th>说明</th></tr></thead>
  <tbody>
    <tr><td>resource_type</td><td>instance / database / cache / load_balancer ...</td></tr>
    <tr><td>metadata</td><td>JSON 扩展字段（规格 / IP / 配置）</td></tr>
    <tr><td>provider_type / region / account</td><td>云厂商、区域、归属账号</td></tr>
    <tr><td>application / department</td><td>归属标签（业务视角）</td></tr>
    <tr><td>status</td><td>运行中 / 已停止 / 异常</td></tr>
  </tbody>
</table>
<h3>cmdb_resource_relation 资源关系表</h3>
<p>source_id → target_id + relation_type，支撑依赖图谱。</p>
<h3>cmdb_resource_change 变更历史表</h3>
<p>每次操作留痕：操作人、类型、前后 diff、工单号。</p>
<h3>cmdb_application 应用表</h3>
<p>应用归属组织、环境（dev / prod）、预算（budget_amount）。</p>

<h2>三、工单系统模块</h2>
<ul>
  <li><b>ticket_order</b>：单号 WO+日期+序列、类型（create/start/stop/change/delete/relation_change/apply_quota）、状态 8 种流转、请求参数、关联资源。</li>
  <li><b>ticket_approval</b>：审批人、意见、时间，支持多人 / 驳回重提。</li>
  <li><b>ticket_task</b>：自动化任务（执行 Provider / 回写 CMDB）。</li>
</ul>

<h2>四、成本模块</h2>
<ul>
  <li><b>fin_cost_bill</b>：账单（云厂商 / 账号 / 月份 / 总额）。</li>
  <li><b>fin_cost_item</b>：成本明细，含 department / application 分摊标签（Cost Allocation Tag）。</li>
  <li><b>fin_budget</b>：部门 / 应用预算。</li>
</ul>

<h2>五、索引与性能要点</h2>
<ul>
  <li>资源表按 (provider_type, status) 建索引。</li>
  <li>成本明细按 (bill_id, department, application) 建组合索引，支撑分摊聚合。</li>
  <li>变更历史按 resource_id + created_at 索引，分页查询。</li>
</ul>
''',
            },
        ],
    },
    {
        'cat': ('mechanism', '核心机制', '⚙️', 5),
        'docs': [
            {
                'slug': 'cost-triangle',
                'title': '业务 / 资源 / 成本三角关系',
                'summary': '通过"标签主线"打通业务、资源、成本三大块：供给侧打标、消费侧采集、成本侧归集。',
                'tags': '三角关系,标签,成本归属',
                'html': '''
<h2>一、核心结论</h2>
<blockquote>业务、资源、成本三者通过 <b>统一标签（application / department）</b> 打通：
资源归属业务、账单归属业务，两者都基于同一套标签，从而回答"业务用了多少资源、花了多少钱"。</blockquote>

<h2>二、三角关系总览</h2>
<table>
  <thead><tr><th>块</th><th>问题</th><th>打通机制</th></tr></thead>
  <tbody>
    <tr><td>业务</td><td>有哪些应用 / 环境？</td><td>cmdb_application + 环境</td></tr>
    <tr><td>资源</td><td>业务用了哪些资源？</td><td>资源表 application 标签</td></tr>
    <tr><td>成本</td><td>业务花了多少钱？</td><td>账单 CostItem 的 department / application 标签</td></tr>
  </tbody>
</table>

<h2>三、三大块打通（架构层三步）</h2>
<h3>5.1 供给侧：业务 → 资源（自动打标）</h3>
<p>申请资源时绑定应用，Resource 自动带上 application 标签。</p>
<h3>5.2 消费侧：资源 → CMDB（采集映射）</h3>
<p>云上资源通过采集任务映射进 CMDB，保持一致。</p>
<h3>5.3 成本侧：账单 → 分摊（标签归集）</h3>
<p>云账单的 Cost Allocation Tag 落到 CostItem，按 department / application 聚合分摊；未打标签归入「未归属」。</p>

<h2>四、映射到本项目建模（关键）</h2>
<ul>
  <li>Resource.application / department：资源归属业务标签。</li>
  <li>CostItem.department / application：账单分摊标签（与资源标签分离，模拟真实账单标签）。</li>
  <li>应用中心成本 = 按应用过滤的账单聚合，避免"环境成本 = 账号全部费用"失真。</li>
</ul>

<h2>五、面试话术要点</h2>
<p>强调"标签主线"设计：<b>不靠人工对账，靠统一标签自动归集</b>，三层（业务 / 资源 / 成本）任何一层有标签即可回答成本归属问题。</p>
''',
            },
            {
                'slug': 'rule-engine',
                'title': '可配置规则引擎',
                'summary': '7 种成本优化规则、MatcherRegistry 注册表、一键检测与报告单号体系。',
                'tags': '规则引擎,优化建议,报告',
                'html': '''
<h2>一、设计目标</h2>
<p>优化建议不是写死的，而是由 <b>可配置规则引擎</b> 驱动：运维按需定义"检测什么、什么条件、省多少"。</p>

<h2>二、7 种规则类型</h2>
<table>
  <thead><tr><th>类型</th><th>检测逻辑</th></tr></thead>
  <tbody>
    <tr><td>闲置资源</td><td>近 30 天 CPU &lt; 5%</td></tr>
    <tr><td>规格降配</td><td>CPU 峰值 &lt; 40% 且内存 &lt; 50%</td></tr>
    <tr><td>未使用资源</td><td>7 天无访问流量</td></tr>
    <tr><td>预算告警</td><td>本月花费 &gt; 预算 80%</td></tr>
    <tr><td>趋势上涨</td><td>连续 3 月涨幅 &gt; 15%</td></tr>
    <tr><td>预留实例</td><td>持续运行 &gt; 6 个月</td></tr>
    <tr><td>存储优化</td><td>快照保留 &gt; 90 天</td></tr>
  </tbody>
</table>

<h2>三、MatcherRegistry 注册表</h2>
<pre>class MatcherRegistry:
    _registry = {}
    @classmethod
    def register(cls, rule_type): ...
    @classmethod
    def get(cls, rule_type): ...</pre>
<p>新增规则类型 = 实现一个匹配器并注册，即插即用（类 ActionRegistry 模式）。</p>

<h2>四、执行与报告</h2>
<ul>
  <li><b>执行</b>：execute_rule 按检测范围（云 / 账号 / 区域 / 类型）过滤资源，跑匹配器生成建议。</li>
  <li><b>报告单号</b>：RPT-YYYYMMDD-NNN，当天序号递增，便于追踪。</li>
  <li><b>报告下钻</b>：云 → 账号 → 区域 → 资源类型 左树右表联动，支持 CSV 导出。</li>
</ul>

<h2>五、设计价值</h2>
<p>平台提供"规则引擎能力"，规则内容由运维配置，避免面试时被追问"规则怎么定的"深坑，同时体现可扩展架构。</p>
''',
            },
            {
                'slug': 'ticket-loop',
                'title': '工单闭环机制',
                'summary': '操作→工单→审批→执行→回写 CMDB 的端到端闭环与状态机、审计留痕。',
                'tags': '工单,审批,闭环,审计',
                'html': '''
<h2>一、闭环链路</h2>
<pre>用户操作 → 生成工单(待审批) → 审批通过 → Provider 执行 → 回写 CMDB → 前端实时刷新</pre>

<h2>二、工单状态机</h2>
<p>8 种状态：<b>待审批 → 审批中 → 执行中 → 成功 / 失败</b>，支持驳回、重提、关闭。</p>

<h2>三、工单类型</h2>
<ul>
  <li>创建 / 启动 / 停止 / 变更 / 下线 / 关系变更（资源运维）。</li>
  <li>预算申请（apply_quota）：成本类工单，审批通过即更新预算。</li>
</ul>

<h2>四、关键机制</h2>
<ul>
  <li><b>统一入口</b>：所有写操作（含场景模板、预算变更）都生成工单。</li>
  <li><b>审计留痕</b>：操作记录 + 工单号 + 前后 diff 写入 audit / change 表。</li>
  <li><b>最终一致</b>：执行结果异步回写，失败可重试 / 回滚。</li>
</ul>

<h2>五、为什么重要</h2>
<p>工单闭环让"每一个变更都可解释、可追溯"，是运维平台区别于云控制台的核心价值，也是本项目面试演示的主线。</p>
''',
            },
        ],
    },
    {
        'cat': ('deploy', '部署运维', '🚀', 6),
        'docs': [
            {
                'slug': 'deployment',
                'title': '部署指南',
                'summary': 'Docker Compose 一键部署、Nginx 反代、MySQL 参数与常见问题。',
                'tags': '部署,Docker,Nginx,MySQL',
                'html': '''
<h2>一、部署架构</h2>
<pre>浏览器 → Nginx(前端静态 + 反代) → Django Backend(DRF) → MySQL 8</pre>
<p>docker-compose.prod.yml 编排：frontend（Nginx）、backend（Django + uvicorn/gunicorn）、db（MySQL 8）。</p>

<h2>二、快速开始</h2>
<ol>
  <li>构建后端镜像（含 seed 命令）：<code>docker compose -f docker-compose.prod.yml build backend</code></li>
  <li>构建前端：<code>cd frontend && npm run build</code>（dist 挂载进 Nginx）</li>
  <li>启动：<code>./deploy.sh</code> 或 <code>docker compose up -d</code></li>
  <li>访问：前端 http://cloud-manager-nginx.orb.local · 后端 http://cloud-manager-backend.orb.local/api/</li>
</ol>

<h2>三、关键配置</h2>
<ul>
  <li>MySQL 启动参数需加 <code>--sort-buffer-size=16M</code>，避免大批量排序触发 1038 错误。</li>
  <li>entrypoint.sh 按序执行 migrate + seed 数据（账号 / 资源 / 成本 / 规则 / 知识库）。</li>
  <li>前端 dist 由 Nginx 挂载，重构建后自动生效。</li>
</ul>

<h2>四、常见问题</h2>
<ul>
  <li>接口返回非 JSON：后端容器未就绪，等待后重试（grep "Listening at" 确认）。</li>
  <li>后端改动不生效：需 <code>build backend</code> 重建镜像（代码 COPY 进镜像）。</li>
  <li>数据库错误：检查 MySQL 容器与卷。</li>
</ul>
''',
            },
        ],
    },
]


class Command(BaseCommand):
    help = '初始化系统知识库：分类 + HTML 文档'

    DOCS_DIR = Path(__file__).resolve().parent.parent.parent / 'docs'

    def _ensure_utf8mb4(self):
        """MySQL 下表字符集转 utf8mb4（幂等），支持 emoji 图标；SQLite 忽略"""
        from django.db import connection
        if connection.vendor != 'mysql':
            return
        with connection.cursor() as cursor:
            for table in ('knowledge_doc_category', 'knowledge_doc_entry'):
                cursor.execute(
                    f'ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 '
                    'COLLATE utf8mb4_unicode_ci')

    def _write_html_file(self, slug: str, html: str) -> None:
        """HTML 正文落盘到 docs 目录（文件为运行时源，数据库不存正文）"""
        self.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        path = self.DOCS_DIR / f'{slug}.html'
        if not path.exists():
            path.write_text(html, encoding='utf-8')

    def handle(self, *args, **options):
        self._ensure_utf8mb4()
        for group in DOCS:
            code, name, icon, sort = group['cat']
            cat, _ = DocCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'icon': icon, 'sort': sort},
            )
            for doc in group['docs']:
                self._write_html_file(doc['slug'], doc['html'])
                DocEntry.objects.update_or_create(
                    slug=doc['slug'],
                    defaults={
                        'category': cat,
                        'title': doc['title'],
                        'summary': doc['summary'],
                        'tags': doc['tags'],
                        # 正文以文件为准，数据库不再冗余存储
                        'html_content': '',
                    },
                )
        written = len(list(self.DOCS_DIR.glob('*.html')))
        self.stdout.write(self.style.SUCCESS(
            f'知识库初始化完成：{DocCategory.objects.count()} 个分类，'
            f'{DocEntry.objects.count()} 篇文档，HTML 落盘 {written} 个文件 '
            f'（{self.DOCS_DIR}）'))
