from django.db import models


class CloudAccount(models.Model):
    """云账号"""
    PROVIDER_CHOICES = [
        ('aws', 'AWS'),
        ('aliyun', '阿里云'),
        ('mock', 'Mock'),
    ]
    STATUS_CHOICES = [
        (0, '未纳管'),
        (1, '正常'),
        (2, '异常'),
    ]
    SYNC_STATUS_CHOICES = [
        (0, '未同步'),
        (1, '同步中'),
        (2, '同步完成'),
        (3, '同步失败'),
    ]

    account_name = models.CharField('账号名称', max_length=64)
    provider_type = models.CharField('云类型', max_length=16, choices=PROVIDER_CHOICES)
    access_key = models.CharField('AccessKey', max_length=128, blank=True, default='')
    secret_key = models.CharField('SecretKey', max_length=256, blank=True, default='')
    regions = models.CharField('纳管地域', max_length=255, blank=True, default='',
                               help_text='逗号分隔')
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=0)
    sync_status = models.SmallIntegerField('同步状态', choices=SYNC_STATUS_CHOICES, default=0)
    last_sync_time = models.DateTimeField('最近同步时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cmdb_cloud_account'
        verbose_name = '云账号'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.account_name} ({self.get_provider_type_display()})'


class Resource(models.Model):
    """统一资源表（多态资源建模核心）"""
    RESOURCE_TYPE_CHOICES = [
        ('instance', '云主机'),
        ('vpc', 'VPC'),
        ('subnet', '子网'),
        ('security_group', '安全组'),
        ('disk', '云硬盘'),
        ('load_balancer', '负载均衡'),
        ('gateway', '网关/入口'),
        ('database', '数据库'),
        ('cache', '缓存'),
        ('cluster', '集群'),
        ('middleware', '中间件'),
        ('object_storage', '对象存储'),
        ('message_queue', '消息队列'),
    ]
    SOURCE_CHOICES = [
        (0, '同步'),
        (1, '工单创建'),
        (2, '手工录入'),
    ]

    account = models.ForeignKey(CloudAccount, on_delete=models.CASCADE,
                                related_name='resources', verbose_name='所属云账号')
    provider_type = models.CharField('云类型', max_length=16)
    resource_type = models.CharField('资源类型', max_length=32, choices=RESOURCE_TYPE_CHOICES)
    resource_name = models.CharField('资源名称', max_length=128)
    cloud_resource_id = models.CharField('云上资源ID', max_length=128, db_index=True)
    region = models.CharField('地域', max_length=32)
    zone = models.CharField('可用区', max_length=32, blank=True, default='')
    status = models.CharField('运行状态', max_length=32, default='unknown')
    spec = models.CharField('规格', max_length=64, blank=True, default='')
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='所属部门')
    application = models.ForeignKey('cmdb.Application', on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='所属应用')
    environment = models.ForeignKey('cmdb.Environment', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='env_resources',
                                    verbose_name='所属环境',
                                    help_text='环境是资源归属的切片维度（dev/test/prod + 云账号/地域）')
    metadata = models.JSONField('差异化字段', default=dict, blank=True)
    source = models.SmallIntegerField('数据来源', choices=SOURCE_CHOICES, default=0)
    MANAGED_CHOICES = [
        ('cloud', '云资源'),
        ('self', '自建'),
        ('hybrid', '混合'),
    ]
    managed_by = models.CharField('资源归属', max_length=16, choices=MANAGED_CHOICES,
                                  default='cloud', blank=True,
                                  help_text='cloud=云托管资源 / self=自建资源 / hybrid=混合')
    source_system = models.CharField('来源系统', max_length=32, default='cmdb', blank=True,
                                     help_text='cmdb / collection / manual，标识数据来自哪个系统')
    sync_mode = models.CharField('同步方式', max_length=16, default='manual', blank=True,
                                 help_text='schedule / event / manual')
    external_id = models.CharField('CMDB配置项ID', max_length=128, blank=True, default='',
                                   help_text='与采集系统/CMDB对齐的外部配置项ID')
    is_deleted = models.BooleanField('逻辑删除', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cmdb_resource'
        verbose_name = '资源'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.resource_name} ({self.cloud_resource_id})'


class ResourceRelation(models.Model):
    """资源关系"""
    RELATION_TYPE_CHOICES = [
        ('belongs_to', '属于'),
        ('deployed_on', '部署于'),
        ('depends_on', '依赖'),
        ('communicates_with', '通信'),
        ('hosted_on', '托管于'),
        ('contains', '包含'),
        ('belongs_to_vpc', '属于VPC'),
        ('belongs_to_subnet', '属于子网'),
        ('attach_sg', '绑定安全组'),
        ('bind_application', '绑定应用'),
    ]
    STRENGTH_CHOICES = [
        ('hard', '强制依赖'),
        ('soft', '软依赖'),
    ]

    source = models.ForeignKey(Resource, on_delete=models.CASCADE,
                               related_name='outgoing_relations', verbose_name='源资源')
    target = models.ForeignKey(Resource, on_delete=models.CASCADE,
                               related_name='incoming_relations', verbose_name='目标资源')
    relation_type = models.CharField('关系类型', max_length=32, choices=RELATION_TYPE_CHOICES)
    strength = models.CharField('依赖强度', max_length=8, choices=STRENGTH_CHOICES,
                                default='hard', help_text='hard=强制依赖 / soft=可降级软依赖')
    relation_source = models.CharField('关系来源', max_length=16, default='manual',
                                       help_text='sync=采集系统同步 / manual=云管人工维护')
    metadata = models.JSONField('关系属性', default=dict, blank=True,
                                help_text='如端口、协议、描述等')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cmdb_resource_relation'
        verbose_name = '资源关系'
        verbose_name_plural = verbose_name
        unique_together = ('source', 'target', 'relation_type')


class ResourceChange(models.Model):
    """资源变更历史"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE,
                                 related_name='changes', verbose_name='资源')
    action = models.CharField('操作', max_length=32)
    before_data = models.JSONField('变更前快照', default=dict, blank=True)
    after_data = models.JSONField('变更后快照', default=dict, blank=True)
    operator = models.CharField('操作人', max_length=64)
    source = models.CharField('来源', max_length=16, default='manual',
                              help_text='ticket / sync / manual')
    ticket_id = models.CharField('关联工单', max_length=64, blank=True, default='')
    created_at = models.DateTimeField('变更时间', auto_now_add=True)

    class Meta:
        db_table = 'cmdb_resource_change'
        verbose_name = '资源变更'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class Application(models.Model):
    """应用"""
    APP_CATEGORY_CHOICES = [
        ('core_business', '核心交易'),
        ('foundation', '基础支撑'),
        ('internal_tool', '内部工具'),
        ('big_data', '大数据'),
        ('middleware', '中间件'),
    ]
    APP_TYPE_CHOICES = [
        ('microservice', '微服务'),
        ('frontend', '前端应用'),
        ('bigdata_job', '大数据任务'),
        ('middleware', '中间件'),
        ('internal_tool', '内部工具'),
    ]
    DEPLOY_TYPE_CHOICES = [
        ('k8s', 'K8s 容器化'),
        ('vm', '云主机/虚机'),
        ('serverless', 'Serverless'),
        ('physical', '物理机'),
    ]
    IMPORTANCE_CHOICES = [
        ('P0', 'P0-核心'),
        ('P1', 'P1-重要'),
        ('P2', 'P2-一般'),
        ('P3', 'P3-低优'),
    ]
    CHANGE_POLICY_CHOICES = [
        ('none', '免审批'),
        ('single', '单人审批'),
        ('multi', '多人会签'),
    ]

    name = models.CharField('应用名称', max_length=64)
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='所属部门')
    owner = models.CharField('负责人', max_length=64, blank=True, default='')
    description = models.CharField('描述', max_length=255, blank=True, default='')

    # 标识与归属
    app_code = models.CharField('应用编码', max_length=64, blank=True, default='')
    app_name_en = models.CharField('应用英文名', max_length=128, blank=True, default='')
    cmdb_ci_id = models.CharField('CMDB配置项ID', max_length=128, blank=True, default='')
    business_line = models.CharField('所属业务线', max_length=64, blank=True, default='')
    app_category = models.CharField('应用分类', max_length=32, choices=APP_CATEGORY_CHOICES,
                                    blank=True, default='')

    # 负责人与协作
    dev_owner = models.CharField('开发负责人', max_length=64, blank=True, default='')
    ops_owner = models.CharField('运维负责人', max_length=64, blank=True, default='')
    alert_group = models.CharField('告警通知组', max_length=128, blank=True, default='')
    creator = models.CharField('创建人', max_length=64, blank=True, default='')

    # 技术元数据
    language = models.CharField('开发语言', max_length=32, blank=True, default='')
    framework = models.CharField('技术框架', max_length=64, blank=True, default='')
    app_type = models.CharField('应用类型', max_length=32, choices=APP_TYPE_CHOICES,
                                blank=True, default='')
    git_repo = models.CharField('Git仓库', max_length=255, blank=True, default='')
    default_branch = models.CharField('默认分支', max_length=64, blank=True, default='')
    artifact_repo = models.CharField('制品/镜像仓库', max_length=255, blank=True, default='')
    ci_pipeline = models.CharField('CI流水线', max_length=255, blank=True, default='')
    deploy_type = models.CharField('部署方式', max_length=16, choices=DEPLOY_TYPE_CHOICES,
                                   blank=True, default='')
    default_cluster = models.CharField('默认集群', max_length=64, blank=True, default='')

    # 治理与合规
    importance_level = models.CharField('重要级别', max_length=8, choices=IMPORTANCE_CHOICES,
                                        blank=True, default='')
    sla = models.CharField('SLA', max_length=32, blank=True, default='')
    dr_level = models.CharField('容灾级别', max_length=64, blank=True, default='')
    change_policy = models.CharField('变更审批策略', max_length=16, choices=CHANGE_POLICY_CHOICES,
                                     blank=True, default='')
    domain = models.CharField('访问域名', max_length=128, blank=True, default='')
    tags = models.JSONField('标签', default=list, blank=True)
    doc_url = models.CharField('文档地址', max_length=255, blank=True, default='')
    # 应用月度预算（成本管理用，申请加预算后累加）
    budget_amount = models.DecimalField('月度预算(元)', max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cmdb_application'
        verbose_name = '应用'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Environment(models.Model):
    """环境：应用下的部署切片，同一应用在不同环境依赖与位置不同"""
    ENV_TYPE_CHOICES = [
        ('dev', '开发'),
        ('test', '测试'),
        ('staging', '预发'),
        ('prod', '生产'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE,
                                    related_name='environments', verbose_name='所属应用')
    name = models.CharField('环境名称', max_length=64)
    env_type = models.CharField('环境类型', max_length=16, choices=ENV_TYPE_CHOICES)
    account = models.ForeignKey(CloudAccount, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='environments', verbose_name='云账号',
                                help_text='环境所处位置：云账号')
    region = models.CharField('地域', max_length=32, blank=True, default='')
    description = models.TextField('描述', blank=True, default='')
    enabled = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cmdb_environment'
        verbose_name = '环境'
        verbose_name_plural = verbose_name
        ordering = ['application', 'id']
        unique_together = ('application', 'name')

    def __str__(self):
        return f'{self.application.name}/{self.name}'


class ServiceInstance(models.Model):
    """服务实例：应用下的服务，部署在资源之上（业务层到资源层的桥梁）"""
    SERVICE_TYPE_CHOICES = [
        ('frontend', '前端'),
        ('backend', '后端'),
        ('database', '数据库'),
        ('cache', '缓存'),
        ('mq', '消息队列'),
        ('worker', '异步任务'),
        ('other', '其他'),
    ]
    DEPLOY_TYPE_CHOICES = [
        ('ec2', '云主机'),
        ('eks', 'K8s'),
        ('serverless', 'Serverless'),
        ('rds', '托管数据库'),
        ('other', '其他'),
    ]
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('degraded', '异常'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE,
                                    related_name='services', verbose_name='所属应用')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='services',
                                    verbose_name='所属环境')
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='services', verbose_name='主部署资源',
                                 help_text='服务部署的主要资源（EC2/集群等）')
    resources = models.ManyToManyField(Resource, blank=True, related_name='deployed_services',
                                       verbose_name='部署资源(多实例)',
                                       help_text='服务实际部署的多个实例/集群资源')
    name = models.CharField('服务名称', max_length=64)
    service_type = models.CharField('服务类型', max_length=16, choices=SERVICE_TYPE_CHOICES)
    deploy_type = models.CharField('部署方式', max_length=16, choices=DEPLOY_TYPE_CHOICES,
                                   default='ec2')
    region = models.CharField('地域', max_length=32, blank=True, default='')
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='running')
    owner = models.CharField('负责人', max_length=64, blank=True, default='')
    description = models.TextField('描述', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cmdb_service_instance'
        verbose_name = '服务实例'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return f'{self.application.name}/{self.name}'


class ServiceEndpoint(models.Model):
    """服务端点：域名/端口/协议/证书，服务对外暴露的配置视图"""
    service = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE,
                                related_name='endpoints', verbose_name='所属服务')
    protocol = models.CharField('协议', max_length=16, default='http')
    port = models.IntegerField('端口', default=80)
    domain = models.CharField('域名', max_length=128, blank=True, default='')
    certificate = models.CharField('证书', max_length=255, blank=True, default='')
    is_public = models.BooleanField('是否公网暴露', default=False)
    metadata = models.JSONField('扩展属性', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cmdb_service_endpoint'
        verbose_name = '服务端点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.service.name} ({self.protocol}://{self.domain or "-"}:{self.port})'


class SecurityRule(models.Model):
    """安全组规则：用于规则级网络连通性推导"""
    DIRECTION_CHOICES = [
        ('inbound', '入方向'),
        ('outbound', '出方向'),
    ]
    PROTOCOL_CHOICES = [
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
        ('icmp', 'ICMP'),
        ('all', '全部'),
    ]
    ACTION_CHOICES = [
        ('allow', '允许'),
        ('deny', '拒绝'),
    ]

    security_group = models.ForeignKey(Resource, on_delete=models.CASCADE,
                                       related_name='security_rules', verbose_name='所属安全组')
    direction = models.CharField('方向', max_length=8, choices=DIRECTION_CHOICES, default='inbound')
    protocol = models.CharField('协议', max_length=8, choices=PROTOCOL_CHOICES, default='tcp')
    port_range = models.CharField('端口范围', max_length=32, default='1-65535')
    source = models.CharField('源', max_length=128, blank=True, default='0.0.0.0/0',
                              help_text='源CIDR或源安全组')
    target = models.CharField('目的', max_length=128, blank=True, default='0.0.0.0/0',
                              help_text='目的CIDR或目的安全组')
    priority = models.IntegerField('优先级', default=100)
    action = models.CharField('动作', max_length=8, choices=ACTION_CHOICES, default='allow')
    enabled = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cmdb_security_rule'
        verbose_name = '安全组规则'
        verbose_name_plural = verbose_name
        ordering = ['priority', 'id']

    def __str__(self):
        return f'{self.security_group.resource_name} {self.direction} {self.protocol}:{self.port_range}'


class SyncJob(models.Model):
    """同步任务：模拟两个采集系统（定时同步 / 事件同步）向云管推送元数据"""
    JOB_TYPE_CHOICES = [
        ('schedule', '定时同步'),
        ('event', '事件同步'),
        ('manual', '手动同步'),
    ]
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    job_type = models.CharField('任务类型', max_length=16, choices=JOB_TYPE_CHOICES)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='pending')
    source_system = models.CharField('来源系统', max_length=32, default='cmdb',
                                     help_text='采集系统A(定时) / 采集系统B(事件)')
    total_count = models.IntegerField('处理条数', default=0)
    message = models.CharField('结果信息', max_length=255, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    finished_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'cmdb_sync_job'
        verbose_name = '同步任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_job_type_display()}] {self.status}'
