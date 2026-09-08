"""
提单预检服务（preview-check）

聚合三部分：
1. base    —— 表单基础校验（必填 / 范围 / 枚举，配置层已兜底，弱化展示）
2. rules   —— 业务规则引擎求值（方案 B 核心）
3. dryrun  —— 办理节点自动化任务 Dry Run（能力 input_schema 校验 + Mock 执行日志）
"""
import logging
from datetime import datetime

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

from apps.capabilities.models import Capability

from .context import build_context, METRICS
from .definition_convert import normalized_definition
from .rule_meta import form_field_sources
from .rules import evaluate_rules

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. 表单基础校验
# ---------------------------------------------------------------------------
def _is_empty(v):
    return v is None or v == '' or (isinstance(v, (list, dict)) and len(v) == 0)


def _fmt_val(v):
    if v is None or v == '':
        return ''
    if isinstance(v, (list, tuple)):
        return '、'.join(str(x) for x in v)
    if isinstance(v, bool):
        return '是' if v else '否'
    return str(v)


def build_base_checks(form_schema: dict, form_data: dict) -> dict:
    """基于 form-create schema 的基础校验（前端已拦截，后端兜底）"""
    categories = [
        {'name': '必填校验', 'checks': []},
        {'name': '范围校验', 'checks': []},
        {'name': '枚举校验', 'checks': []},
    ]
    cat_map = {c['name']: c['checks'] for c in categories}
    any_error = False

    for f in form_field_sources(form_schema):
        widget = _find_widget(form_schema, f['name'])
        if not widget:
            continue
        label = widget.get('title') or f['name']
        value = form_data.get(f['name'])
        val_text = _fmt_val(value)
        validate = widget.get('validate') or []
        props = widget.get('props') or {}
        options = widget.get('options') or []

        # 必填
        if any(v.get('required') for v in validate):
            if _is_empty(value):
                cat_map['必填校验'].append({'name': label, 'value': val_text, 'status': 'error', 'message': f'{label} 未填写'})
                any_error = True
            else:
                cat_map['必填校验'].append({'name': label, 'value': val_text, 'status': 'passed', 'message': '已填写'})

        # 范围（number）
        if props.get('min') is not None or props.get('max') is not None:
            try:
                num = float(value)
            except (TypeError, ValueError):
                num = None
            if num is not None:
                lo, hi = props.get('min'), props.get('max')
                if lo is not None and num < lo:
                    cat_map['范围校验'].append({'name': label, 'value': val_text, 'status': 'error', 'message': f'{value} 低于最小值 {lo}'})
                    any_error = True
                elif hi is not None and num > hi:
                    cat_map['范围校验'].append({'name': label, 'value': val_text, 'status': 'error', 'message': f'{value} 超出最大值 {hi}'})
                    any_error = True
                else:
                    cat_map['范围校验'].append({'name': label, 'value': val_text, 'status': 'passed', 'message': f'{value} 在允许范围内'})

        # 枚举
        if options:
            vals = [o.get('value', o.get('label')) if isinstance(o, dict) else o for o in options]
            if not _is_empty(value) and value not in vals:
                cat_map['枚举校验'].append({'name': label, 'value': val_text, 'status': 'error', 'message': f'{value} 不是合法选项'})
                any_error = True
            elif not _is_empty(value):
                cat_map['枚举校验'].append({'name': label, 'value': val_text, 'status': 'passed', 'message': '是合法选项'})

    return {'passed': not any_error, 'categories': categories}


def _find_widget(form_schema: dict, field: str) -> dict:
    rules = form_schema.get('rules') if isinstance(form_schema, dict) else form_schema
    for w in rules or []:
        if isinstance(w, dict) and w.get('field') == field:
            return w
    return None


# ---------------------------------------------------------------------------
# 2. 办理节点 Dry Run
# ---------------------------------------------------------------------------
_MOCK_OUTPUTS = {
    'cmdb.create_host': lambda inp: {'host_id': 'host_' + (str(inp.get('hostname') or 'x')[-4:] or '0001'), 'ip': '10.20.1.10', 'status': 'success'},
    'mail.send': lambda inp: {'mail_id': 'mail_demo', 'status': 'success'},
    'permission.center.grant': lambda inp: {'grant_id': 'grant_demo', 'status': 'success'},
    'cmdb.restart_host': lambda inp: {'task_id': 'job_demo', 'status': 'success'},
    'dns.add_record': lambda inp: {'record_id': 'rec_demo', 'status': 'success'},
    'external.approve': lambda inp: {'approval_id': 'app_demo', 'status': 'success'},
}


def _resolve_action_input(action: dict, form_data: dict) -> dict:
    inp = {}
    for bind in action.get('fieldBindings') or []:
        field = bind.get('capabilityField')
        if not field:
            continue
        source = bind.get('source', 'form')
        if source == 'form':
            inp[field] = form_data.get(bind.get('formField'))
        elif source == 'constant':
            inp[field] = bind.get('constantValue', bind.get('constant'))
        else:
            inp[field] = None  # previous 输出：dryrun 阶段不可得，置空
    return inp


def _coerce_input_to_schema(input_data: dict, schema: dict) -> dict:
    """按能力 input_schema 做输入归一：schema 声明为 array 的字段，若值为标量则包成数组"""
    if not schema:
        return input_data
    props = schema.get('properties') or {}
    coerced = dict(input_data)
    for field, val in input_data.items():
        if val is None or isinstance(val, (list, tuple)):
            continue
        if (props.get(field) or {}).get('type') == 'array':
            coerced[field] = [val]
    return coerced


def _validate_schema(schema: dict, input_data: dict) -> list:
    """用 JSON Schema 校验能力输入，返回错误消息列表（空 = 通过）"""
    if not schema:
        return []
    try:
        validator = Draft7Validator(schema)
        errors = sorted(validator.iter_errors(input_data), key=lambda e: list(e.path))
        return [e.message for e in errors]
    except Exception as e:
        return [f'schema 校验异常：{e}']


def build_dryrun(definition_json: dict, form_data: dict) -> list:
    """
    遍历办理节点（handle）的自动化任务，做 DRY 校验 + Mock 执行。

    返回：[{node_key, node_name, tasks: [{key, name, capability, status, statusText, input, output, logs}]}]
    """
    nd = normalized_definition(definition_json)
    nodes = nd.get('nodes', [])
    handle_nodes = [n for n in nodes if n.get('type') == 'handle']

    cap_cache = {c.code: c for c in Capability.objects.filter(is_active=True)}

    result = []
    for node in handle_nodes:
        task_config = node.get('taskConfig') or {}
        actions = task_config.get('actions') or []
        execution_mode = task_config.get('executionMode', 'sequential')
        tasks = []
        prev_failed = False

        for i, action in enumerate(actions):
            capability_code = action.get('capabilityCode') or ''
            capability = cap_cache.get(capability_code)
            logs = []
            t = datetime.now().strftime('%H:%M:%S')
            logs.append({'time': t, 'level': 'info', 'msg': '校验输入参数 ...'})

            input_data = _resolve_action_input(action, form_data)
            input_data = _coerce_input_to_schema(input_data, capability.input_schema if capability else {})
            schema_errors = _validate_schema(capability.input_schema if capability else {}, input_data) if capability else []

            # 串行且前序失败 → 跳过
            if execution_mode == 'sequential' and prev_failed:
                logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'level': 'warn', 'msg': '前序动作失败，本动作跳过执行'})
                tasks.append({
                    'key': action.get('key') or f'a{i}',
                    'name': action.get('name') or capability_code,
                    'capability': capability_code,
                    'status': 'warning',
                    'statusText': '待确认',
                    'input': input_data,
                    'output': {},
                    'logs': logs,
                })
                continue

            if schema_errors:
                for msg in schema_errors:
                    logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'level': 'error', 'msg': msg})
                logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'level': 'error', 'msg': '执行中止'})
                tasks.append({
                    'key': action.get('key') or f'a{i}',
                    'name': action.get('name') or capability_code,
                    'capability': capability_code,
                    'status': 'error',
                    'statusText': '预检失败',
                    'input': input_data,
                    'output': {},
                    'logs': logs,
                })
                if execution_mode == 'sequential':
                    prev_failed = True
                continue

            # 校验通过 → Mock 执行
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'level': 'info', 'msg': f'Mock 执行：{action.get("name") or capability_code}'})
            output = _MOCK_OUTPUTS.get(capability_code, lambda inp: {'status': 'success'})(input_data)
            logs.append({'time': datetime.now().strftime('%H:%M:%S'), 'level': 'success', 'msg': '执行成功（DRY 模式 · 无副作用）'})
            tasks.append({
                'key': action.get('key') or f'a{i}',
                'name': action.get('name') or capability_code,
                'capability': capability_code,
                'status': 'success',
                'statusText': '预检通过',
                'input': input_data,
                'output': output,
                'logs': logs,
            })

        result.append({
            'node_key': node.get('key'),
            'node_name': node.get('name'),
            'tasks': tasks,
        })
    return result


# ---------------------------------------------------------------------------
# 3. 聚合预检
# ---------------------------------------------------------------------------
def _build_labels(form_schema: dict) -> dict:
    """构造数据源中文名映射（表单字段 + 上下文指标），供判定明细展示"""
    labels = {}
    for f in form_field_sources(form_schema):
        labels[f['name']] = {'label': f['label']}
    for m in METRICS:
        labels[m['name']] = {'label': m['label'], 'provider': m.get('provider', '')}
    return labels


def preview_check(definition, form_data: dict, user=None) -> dict:
    """完整预检：base + rules + dryrun + summary"""
    form_data = form_data or {}
    base = build_base_checks(definition.form_schema, form_data)
    labels = _build_labels(definition.form_schema)
    rules_result = evaluate_rules(definition.rules_json or [], form_data, user, labels=labels)
    dryrun = build_dryrun(definition.definition_json, form_data)

    rules_summary = rules_result['summary']
    summary = {
        **rules_summary,
        'base_passed': base['passed'],
        # 拦截 = 业务规则错误 或 基础校验失败
        'blocked': rules_summary['blocked'] or not base['passed'],
    }
    return {
        'base': base,
        'rules': rules_result['rules'],
        'dryrun': dryrun,
        'summary': summary,
    }
