"""
可配置优化规则引擎 —— 平台能力层。

规则由运维在页面配置（scope 检测范围 + conditions 检测条件 + saving_config 节省估算），
引擎负责解析配置、匹配 CMDB 资源、生成优化建议与分析报告。

设计要点（面试亮点）：
- 匹配器注册表（MatcherRegistry）：新增规则类型 = 注册一个匹配器，无需改引擎
- 数据源为 CMDB 规范化 Resource（天然多云），引擎与云无关
- 利用率类指标（avg_cpu_7d 等）由采集平台写入 Resource.metadata，引擎只消费
- 每次执行写 RuleExecutionLog + 生成 OptimizationReport（快照留痕，可追溯）
"""
import logging
import time
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

logger = logging.getLogger(__name__)

# 云显示名 → Resource.provider_type
CLOUD_PROVIDER_MAP = {
    'AWS': 'aws',
    '阿里云': 'aliyun',
    '腾讯云': 'tencent',
    '全部': '',
}

# 资源类型 → 展示名（报告树 / 导出用）
RESOURCE_TYPE_LABELS = {
    'instance': '云主机', 'database': '数据库', 'cache': '缓存', 'disk': '云硬盘',
    'load_balancer': '负载均衡', 'object_storage': '对象存储', 'vpc': 'VPC',
    'subnet': '子网', 'security_group': '安全组', 'gateway': '网关',
    'cluster': '集群', 'middleware': '中间件', 'message_queue': '消息队列',
}

# 维度级检测类型（作用于部门/账号，非单资源）
DIMENSION_RULE_TYPES = ('budget', 'trend')


class MatcherRegistry:
    """匹配器注册表 —— 新增规则类型只需注册一个匹配器函数"""
    _matchers = {}

    @classmethod
    def register(cls, rule_type):
        def deco(fn):
            cls._matchers[rule_type] = fn
            return fn
        return deco

    @classmethod
    def get(cls, rule_type):
        return cls._matchers.get(rule_type)


# ---------- 通用工具 ----------

def _base_qs(scope):
    """根据 scope（云/账号/区域/资源类型）构建基础查询集"""
    from cmdb.models import Resource
    qs = Resource.objects.filter(is_deleted=False)
    cloud = scope.get('cloud')
    if cloud:
        provider = CLOUD_PROVIDER_MAP.get(cloud)
        if provider:
            qs = qs.filter(provider_type=provider)
    account = scope.get('account')
    if account:
        qs = qs.filter(account__account_name=account)
    region = scope.get('region')
    if region:
        qs = qs.filter(region=region)
    rtype = scope.get('resource_type')
    if rtype:
        qs = qs.filter(resource_type=rtype)
    return qs


def _eval_compare(val, rule):
    """比较值是否满足规则，如 {'lt':5} / {'gte':80}"""
    for op, target in rule.items():
        try:
            if op == 'lt' and not (val < target):
                return False
            if op == 'lte' and not (val <= target):
                return False
            if op == 'gt' and not (val > target):
                return False
            if op == 'gte' and not (val >= target):
                return False
            if op == 'eq' and not (val == target):
                return False
            if op == 'ne' and not (val != target):
                return False
        except TypeError:
            return False
    return True


def _days_since(dt):
    """距今天数（用于停止时长等近似判断）"""
    if not dt:
        return 0
    try:
        return (date.today() - dt.date()).days
    except Exception:
        return 0


# ---------- 资源级匹配器 ----------

@MatcherRegistry.register('idle')
def match_idle(resource, conditions):
    """闲置资源：状态为 stopped（可配 min_days 停止时长）"""
    status = conditions.get('status', 'stopped')
    if resource.status != status:
        return False
    min_days = conditions.get('min_days') or conditions.get('min_stopped_days')
    if min_days and _days_since(resource.updated_at) < min_days:
        # 停止时长由采集系统记录，这里用 updated_at 近似
        return False
    return True


@MatcherRegistry.register('downsize')
def match_downsize(resource, conditions):
    """规格降配：读取 metadata 指标摘要（采集器写入），低于阈值则建议降配"""
    if resource.status != 'running':
        return False
    metrics = conditions.get('metrics', {})
    if not metrics:
        return False
    for key, rule in metrics.items():
        val = resource.metadata.get(key)
        if val is None:
            # 无指标数据 → 不匹配（等待采集器写入指标摘要）
            return False
        if not _eval_compare(val, rule):
            return False
    return True


@MatcherRegistry.register('unused')
def match_unused(resource, conditions):
    """未使用资源：磁盘 available 等"""
    status = conditions.get('status', 'available')
    if resource.status != status:
        return False
    min_days = conditions.get('min_days')
    if min_days and _days_since(resource.updated_at) < min_days:
        return False
    return True


@MatcherRegistry.register('reserved')
def match_reserved(resource, conditions):
    """付费模式优化：按量计费资源推荐转包年/预留"""
    if resource.resource_type != 'instance':
        return False
    target_mode = conditions.get('billing_mode', 'pay_as_you_go')
    billing_mode = resource.metadata.get('billing_mode', 'pay_as_you_go')
    if billing_mode != target_mode:
        return False
    # 仅对较大规格建议转包年（小规格收益低，避免建议淹没）
    if _spec_base_price(resource.spec) < 300:
        return False
    return True


@MatcherRegistry.register('storage')
def match_storage(resource, conditions):
    """存储优化：对象存储/大容量磁盘，建议生命周期分层或归档"""
    if resource.resource_type not in ('object_storage', 'disk'):
        return False
    min_size = conditions.get('min_size_gb')
    if min_size:
        size = resource.metadata.get('size_gb', 0)
        if not size or size < min_size:
            return False
    return True


# ---------- 维度级检测 ----------

def _dimension_detections(rule, conditions):
    """返回维度级建议项列表（dict 形式，不绑定具体资源）"""
    items = []
    rule_type = rule.rule_type
    if rule_type == 'budget':
        # 预算超支：部门月度预算使用超过阈值
        from .models import Budget
        threshold = conditions.get('budget_usage_percent', {}).get('gte', 80)
        month = date.today().strftime('%Y-%m')
        for budget in Budget.objects.filter(month=month).select_related('department'):
            if budget.usage_percent >= threshold:
                items.append({
                    'kind': 'department',
                    'name': budget.department.name,
                    'cloud_resource_id': f'DEPT-{budget.department_id}',
                    'department_id': budget.department_id,
                    'region': '-', 'provider_type': '', 'resource_type': 'budget',
                    'extra': {
                        'usage_percent': budget.usage_percent,
                        'budget_amount': float(budget.budget_amount),
                        'used_amount': float(budget.used_amount),
                    },
                })
    elif rule_type == 'trend':
        # 费用趋势异常：月度费用环比增长超过阈值
        from .models import CostBill
        threshold = conditions.get('threshold_percent', 20)
        direction = conditions.get('direction', 'increase')
        bills = list(CostBill.objects.select_related('account').order_by('bill_month'))
        by_account = {}
        for b in bills:
            by_account.setdefault(b.account_id, []).append(b)
        for account_id, account_bills in by_account.items():
            account_bills.sort(key=lambda x: x.bill_month)
            for i in range(1, len(account_bills)):
                prev, cur = account_bills[i - 1], account_bills[i]
                if prev.total_cost and cur.total_cost > prev.total_cost:
                    change = float((cur.total_cost - prev.total_cost) / prev.total_cost * 100)
                    if change >= threshold:
                        items.append({
                            'kind': 'account',
                            'name': prev.account.account_name,
                            'cloud_resource_id': f'ACC-{prev.account_id}',
                            'region': '-', 'provider_type': prev.account.provider_type,
                            'resource_type': 'account',
                            'extra': {
                                'change_percent': round(change, 1),
                                'prev_month': prev.bill_month,
                                'cur_month': cur.bill_month,
                                'prev_cost': float(prev.total_cost),
                                'cur_cost': float(cur.total_cost),
                            },
                        })
                        break
    return items


# ---------- 节省估算 ----------

def _estimate_saving(resource, rule, extra=None):
    """根据 saving_config 估算月节省金额"""
    config = rule.saving_config or {}
    stype = config.get('type', 'none')
    if stype == 'fixed':
        return Decimal(str(config.get('amount', 0)))
    if stype == 'spec_ratio':
        # 按规格基础价 × 比例估算
        base = _spec_base_price(resource.spec)
        percent = config.get('percent', 100)
        return Decimal(str(round(base * percent / 100, 2)))
    if stype == 'none':
        return Decimal('0')
    return Decimal('0')


def _spec_base_price(spec):
    """规格 → 基础月价（演示用，生产对接定价系统）"""
    table = {
        't3.medium': 200, 't3.large': 400, 't3.xlarge': 800,
        'ecs.g6.large': 300, 'ecs.g6.xlarge': 600, 'ecs.g6.2xlarge': 1200,
        'ecs.c7.large': 250, 'ecs.c7.xlarge': 500,
    }
    return table.get(spec, 300)


def _render_template(template, resource=None, extra=None):
    """渲染标题/描述模板，支持 {resource_name} 等占位符"""
    mapping = {
        '{resource_name}': resource.resource_name if resource else '',
        '{account_name}': resource.account.account_name if resource and resource.account else '',
        '{department_name}': (extra or {}).get('name', ''),
        '{usage_percent}': str((extra or {}).get('usage_percent', '')),
        '{change_percent}': str((extra or {}).get('change_percent', '')),
    }
    out = template or ''
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out


# ---------- 执行器 ----------

def execute_rule(rule, trigger='manual', operator='system'):
    """执行单条规则：匹配 + 生成建议 + 写执行日志。

    返回: {"matched": n, "created": n, "items": [suggestion_id,...]}
    """
    from cmdb.models import Resource
    from .models import OptimizationSuggestion, RuleExecutionLog

    start = time.time()
    scope = rule.scope or {}
    conditions = rule.conditions or {}
    matched_resources = []
    dimension_items = []

    if rule.rule_type in DIMENSION_RULE_TYPES:
        dimension_items = _dimension_detections(rule, conditions)
    else:
        matcher = MatcherRegistry.get(rule.rule_type)
        if matcher:
            qs = _base_qs(scope)
            for res in qs:
                if matcher(res, conditions):
                    matched_resources.append(res)

    created = 0
    created_ids = []

    for res in matched_resources:
        # 同一资源 + 同一规则 + 未处理 → 去重
        if OptimizationSuggestion.objects.filter(
            rule=rule, resource=res, is_resolved=False
        ).exists():
            continue
        saving = _estimate_saving(res, rule)
        sug = OptimizationSuggestion.objects.create(
            rule=rule,
            resource=res,
            department=res.department,
            account=res.account,
            provider_type=res.provider_type,
            region=res.region,
            resource_type=res.resource_type,
            suggestion_type=rule.rule_type,
            severity=rule.severity,
            title=_render_template(rule.title_template, resource=res),
            description=rule.description or f'资源 {res.resource_name}({res.cloud_resource_id}) 触发 {rule.get_rule_type_display()} 规则',
            estimated_saving=saving,
        )
        created += 1
        created_ids.append(sug.id)

    for item in dimension_items:
        saving = Decimal('0')
        sug = OptimizationSuggestion.objects.create(
            rule=rule,
            resource=None,
            department_id=item.get('department_id'),
            provider_type=item.get('provider_type', ''),
            region=item.get('region', '-'),
            resource_type=item.get('resource_type', ''),
            suggestion_type=rule.rule_type,
            severity=rule.severity,
            title=_render_template(rule.title_template, extra=item),
            description=rule.description or f'{item.get("name")} 触发 {rule.get_rule_type_display()} 规则',
            estimated_saving=saving,
        )
        created += 1
        created_ids.append(sug.id)

    elapsed = int((time.time() - start) * 1000)
    RuleExecutionLog.objects.create(
        rule=rule,
        scope_snapshot=scope,
        matched_count=len(matched_resources) + len(dimension_items),
        created_count=created,
        execution_time_ms=elapsed,
    )
    return {'matched': len(matched_resources) + len(dimension_items),
            'created': created, 'ids': created_ids}


def run_all(rules=None, trigger='manual', operator='system'):
    """全量检测：执行指定（或全部启用）规则，生成分析报告。

    返回: OptimizationReport 实例
    """
    from .models import OptimizationRule, OptimizationReport, OptimizationSuggestion
    from django.utils import timezone

    target_rules = list(rules) if rules else list(
        OptimizationRule.objects.filter(is_enabled=True).order_by('-priority')
    )

    all_items = []
    logs = []
    for rule in target_rules:
        result = execute_rule(rule, trigger=trigger, operator=operator)
        logs.append({
            'rule_id': rule.id, 'rule_name': rule.name,
            'matched': result['matched'], 'created': result['created'],
        })
        # 收集本次报告快照用的明细（复用 rule 触发条件，独立生成快照 item）
        all_items.extend(_collect_items(rule))

    total_saving = float(OptimizationSuggestion.objects.filter(
        is_resolved=False, rule__in=target_rules
    ).aggregate(s=Sum('estimated_saving'))['s'] or 0)

    # 报告单号：按日期编排唯一编号，如 RPT-20260812-004
    today = timezone.localdate()
    seq = OptimizationReport.objects.filter(executed_at__date=today).count() + 1
    report_no = f'RPT-{today:%Y%m%d}-{seq:03d}'

    report = OptimizationReport.objects.create(
        report_no=report_no,
        title=f'成本优化分析报告 - {date.today().strftime("%Y-%m-%d")}',
        operator=operator,
        trigger=trigger,
        summary={
            'total_rules': len(target_rules),
            'total_matched': sum(l['matched'] for l in logs),
            'total_saving': round(total_saving, 2),
            'cloud_count': len({i['cloud'] for i in all_items if i.get('cloud')}),
        },
        tree_snapshot=build_tree(all_items),
        items_snapshot=all_items,
    )
    # 把本次报告关联到建议
    for sug in OptimizationSuggestion.objects.filter(rule__in=target_rules, report__isnull=True):
        sug.report = report
        sug.save(update_fields=['report'])
    return report


def _collect_items(rule):
    """为报告快照收集当前规则下的建议明细（含冗余维度字段，便于导出）"""
    from .models import OptimizationSuggestion
    items = []
    for s in OptimizationSuggestion.objects.filter(rule=rule).select_related('resource', 'account'):
        items.append({
            'cloud': s.provider_type, 'account': s.account.account_name if s.account else '-',
            'region': s.region, 'resource_type': s.resource_type,
            'resource_name': s.resource.resource_name if s.resource else s.title,
            'resource_id': s.resource.cloud_resource_id if s.resource else s.title,
            'spec': s.resource.spec if s.resource else '-',
            'suggestion_type': s.suggestion_type, 'severity': s.severity,
            'title': s.title, 'description': s.description,
            'estimated_saving': float(s.estimated_saving),
            'is_resolved': s.is_resolved, 'rule_name': rule.name,
        })
    return items


def build_tree(items):
    """构建 云→账号→区域→资源类型 层级聚合（V5 报告树）。"""
    tree = {}
    for it in items:
        cloud = it.get('cloud') or '全部'
        if cloud not in tree:
            tree[cloud] = {'cloud': cloud, 'matched': 0, 'saving': 0.0, 'accounts': {}}
        tree[cloud]['matched'] += 1
        tree[cloud]['saving'] += it.get('estimated_saving', 0)
        acc = it.get('account') or '-'
        if acc not in tree[cloud]['accounts']:
            tree[cloud]['accounts'][acc] = {'account': acc, 'matched': 0, 'saving': 0.0, 'regions': {}}
        tree[cloud]['accounts'][acc]['matched'] += 1
        tree[cloud]['accounts'][acc]['saving'] += it.get('estimated_saving', 0)
        region = it.get('region') or '-'
        if region not in tree[cloud]['accounts'][acc]['regions']:
            tree[cloud]['accounts'][acc]['regions'][region] = {
                'region': region, 'matched': 0, 'saving': 0.0, 'types': {}
            }
        tree[cloud]['accounts'][acc]['regions'][region]['matched'] += 1
        tree[cloud]['accounts'][acc]['regions'][region]['saving'] += it.get('estimated_saving', 0)
        rtype = RESOURCE_TYPE_LABELS.get(it.get('resource_type'), it.get('resource_type') or '-')
        reg = tree[cloud]['accounts'][acc]['regions'][region]
        if rtype not in reg['types']:
            reg['types'][rtype] = {'type_name': rtype, 'matched': 0, 'saving': 0.0, 'items': []}
        reg['types'][rtype]['matched'] += 1
        reg['types'][rtype]['saving'] += it.get('estimated_saving', 0)
        reg['types'][rtype]['items'].append(it)

    # 嵌套 dict → list
    for c in tree.values():
        for a in c['accounts'].values():
            for r in a['regions'].values():
                r['types'] = list(r['types'].values())
            a['regions'] = list(a['regions'].values())
        c['accounts'] = list(c['accounts'].values())
    return tree
