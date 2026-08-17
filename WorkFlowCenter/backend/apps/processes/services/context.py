"""
业务上下文指标（ContextProvider 注册表）

规则引擎的数据源分为两类：
1. 表单字段：从 ProcessDefinition.form_schema 动态提取（rule_meta 生成）
2. 业务上下文指标：由各 Provider 暴露（配额 / 容量 / 网络 / 预算 / 历史）

Provider 统一接口：provide(form_data, user) -> {metric_name: value}

设计说明（方案 B）：
- 指标 = 规则可引用的「表单之外」的数据（部门配额、资源池监控、网络拓扑、预算、历史工单）
- 本文件内置 Mock Provider（demo/开发环境用），接口与真实系统对齐：
  接真实系统时仅替换 provider 内部实现（如从 CMDB / 预算系统 API 拉取），规则与前端无需改动
"""
from typing import Optional

from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------------------------------------------------------------------
# 指标字典（供 rule-meta 接口 / 前端配置器下拉）
# type: number=数值 / money=金额 / array=数组（多选、列表）
# ---------------------------------------------------------------------------
METRICS = [
    {'name': 'dept.cpu_quota.remaining', 'label': '部门剩余CPU配额', 'type': 'number', 'unit': '核', 'provider': '配额系统', 'source': 'quota'},
    {'name': 'dept.mem_quota.remaining', 'label': '部门剩余内存配额', 'type': 'number', 'unit': 'GB', 'provider': '配额系统', 'source': 'quota'},
    {'name': 'dept.budget_remaining', 'label': '部门剩余预算', 'type': 'money', 'unit': '元', 'provider': '预算系统', 'source': 'budget'},
    {'name': 'estimate.cost_month', 'label': '估算月成本', 'type': 'money', 'unit': '元/月', 'provider': '定价模型', 'source': 'estimate'},
    {'name': 'pool.cpu_available', 'label': '资源池可用CPU', 'type': 'number', 'unit': '核', 'provider': '监控系统', 'source': 'capacity'},
    {'name': 'pool.mem_available', 'label': '资源池可用内存', 'type': 'number', 'unit': 'GB', 'provider': '监控系统', 'source': 'capacity'},
    {'name': 'network.reachable_segments', 'label': '可达网段列表', 'type': 'array', 'unit': '', 'provider': '网络拓扑', 'source': 'network'},
    {'name': 'network.is_reachable', 'label': '所选网络是否可达', 'type': 'number', 'unit': '0=不可达/1=可达', 'provider': '网络拓扑', 'source': 'network'},
    {'name': 'history.same_spec_count', 'label': '近7天同规格申请数', 'type': 'number', 'unit': '台', 'provider': '历史工单', 'source': 'history'},
]


# ---------------------------------------------------------------------------
# Mock Provider（Demo / 开发环境）
# ---------------------------------------------------------------------------
def _to_num(v, default=0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def provide_quota(form_data, user):
    """部门配额（Mock：固定剩余值）"""
    return {
        'dept.cpu_quota.remaining': 8,
        'dept.mem_quota.remaining': 152,
    }


def provide_budget(form_data, user):
    """部门预算（Mock）"""
    return {'dept.budget_remaining': 120000}


def provide_estimate(form_data, user):
    """估算月成本：基础费 + CPU*单价 + 内存*单价（Mock 定价模型）"""
    cpu = _to_num(form_data.get('cpu'))
    mem = _to_num(form_data.get('memory'))
    return {'estimate.cost_month': round(500 + cpu * 800 + mem * 120, 2)}


def provide_capacity(form_data, user):
    """资源池可用容量（Mock）"""
    return {
        'pool.cpu_available': 24,
        'pool.mem_available': 96,
    }


def provide_network(form_data, user):
    """网络可达性：用 CIDR 归属判断所选网段是否在可达前缀内"""
    import ipaddress

    reachable_prefixes = ['10.0.0.0/8', '192.168.0.0/16', '172.16.0.0/12']
    seg = (form_data or {}).get('network_segment')
    is_reachable = 1
    if seg:
        try:
            addr = ipaddress.ip_network(seg, strict=False)
            is_reachable = 1 if any(addr.subnet_of(ipaddress.ip_network(p)) for p in reachable_prefixes) else 0
        except ValueError:
            is_reachable = 0
    return {
        'network.reachable_segments': reachable_prefixes,
        'network.is_reachable': is_reachable,
    }


def provide_history(form_data, user):
    """近 7 天同规格申请数（Mock）"""
    return {'history.same_spec_count': 0}


# provider 注册表：metric 前缀 → provider 函数
_PROVIDERS = {
    'dept': provide_quota,
    'estimate': provide_estimate,
    'pool': provide_capacity,
    'network': provide_network,
    'history': provide_history,
}


def build_context(form_data: dict, user=None) -> dict:
    """
    聚合所有 provider 的输出，返回指标字典（规则求值的输入变量）。
    """
    ctx = {}
    for provider in dict.fromkeys(_PROVIDERS.values()):
        try:
            ctx.update(provider(form_data or {}, user) or {})
        except Exception:
            continue
    return ctx


def metric_meta() -> list:
    """返回指标字典（供 rule-meta 接口 / 前端配置器下拉）"""
    return list(METRICS)


def available_metric_names() -> set:
    return {m['name'] for m in METRICS}
