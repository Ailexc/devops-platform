"""
规则数据源字典（rule-meta 接口 / 前端配置器下拉）

数据源 = 表单字段（来自 form_schema）+ 业务上下文指标（来自 context.METRICS）
"""
from .context import METRICS

# form-create 组件类型 → 规则数据源类型
# number=数值 / money=金额 / enum=枚举 / text=文本 / array=数组
_FORM_TYPE_MAP = {
    'input': 'text',
    'textarea': 'text',
    'inputNumber': 'number',
    'select': 'enum',
    'radio': 'enum',
    'checkbox': 'array',
    'datePicker': 'text',
    'timePicker': 'text',
    'switch': 'enum',
}


def _extract_field(widget) -> dict:
    ftype = _FORM_TYPE_MAP.get(widget.get('type'), 'text')
    field = {
        'name': widget.get('field'),
        'label': widget.get('title') or widget.get('field'),
        'type': ftype,
    }
    options = widget.get('options')
    if options:
        # form-create options 可能为 [{label, value}] 或 [str]
        if isinstance(options, list) and options and isinstance(options[0], dict):
            field['options'] = [o.get('label', o.get('value')) for o in options if o]
        else:
            field['options'] = list(options)
    props = widget.get('props') or {}
    if props.get('min') is not None:
        field['min'] = props.get('min')
    if props.get('max') is not None:
        field['max'] = props.get('max')
    return field


def form_field_sources(form_schema) -> list:
    """从 form-create rules 数组提取表单字段数据源"""
    if not isinstance(form_schema, dict):
        return []
    rules = form_schema.get('rules') or form_schema.get('formItems') or []
    if isinstance(form_schema, list):
        rules = form_schema
    sources = []
    for widget in rules:
        if isinstance(widget, dict) and widget.get('field'):
            sources.append(_extract_field(widget))
    return sources


def available_sources(form_schema) -> set:
    """返回可被规则引用的全部数据源名（表单字段 + 上下文指标）"""
    names = {f['name'] for f in form_field_sources(form_schema)}
    names.update(m['name'] for m in METRICS)
    return names


def rule_meta(form_schema) -> dict:
    """组装 rule-meta 响应：分组数据源 + 操作符字典"""
    return {
        'form': form_field_sources(form_schema),
        'context': METRICS,
        'operators': {
            'number': ['>', '>=', '<', '<=', '==', '!='],
            'money': ['>', '>=', '<', '<=', '==', '!='],
            'enum': ['==', '!='],
            'text': ['==', '!=', 'contains', 'not_contains', 'matches'],
            'array': ['in', 'not_in'],
        },
    }
