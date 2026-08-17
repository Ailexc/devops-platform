"""
业务规则解释器（方案 B · 结构化 AST）

规则数据形态（前端配置器产出，存储于 ProcessDefinition.rules_json）：
{
  "id": "RULE-001", "name": "...", "level": "error|warning",
  "message": "命中提示", "suggestion": "建议",
  "groups": [                      # 多组 = OR
    [                              # 组内 = AND
      { "source": "cpu",           # 数据源（表单字段 或 上下文指标）
        "op": ">",                 # 操作符
        "refType": "fixed|field",  # 参考值类型
        "fixed": 8,                # refType=fixed 时
        "refField": "dept.cpu_quota.remaining",  # refType=field 时
        "offset": 0 }              # 参考值偏移（rhs = ref - offset，用于容量预留）
    ]
  ]
}

求值：遍历 AST，不用 eval；数据源带 form. 兜底（表单字段名不带前缀）。
"""
import logging
import re

from .context import build_context

logger = logging.getLogger(__name__)

# 操作符集合（前端按数据源类型提供子集）
OPERATORS = ('>', '>=', '<', '<=', '==', '!=', 'in', 'not_in', 'contains', 'not_contains', 'matches')

LEVEL_ERROR = 'error'
LEVEL_WARNING = 'warning'


# ---------------------------------------------------------------------------
# 数值 / 类型兼容
# ---------------------------------------------------------------------------
def _to_num(v):
    try:
        if isinstance(v, bool):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _normalize(v):
    """比较前的类型归一：数字字符串转 float"""
    if isinstance(v, str):
        n = _to_num(v)
        if n is not None:
            return n
    return v


# ---------------------------------------------------------------------------
# 数据源取值（带 form. 兜底）
# ---------------------------------------------------------------------------
def resolve_source(name, data):
    """从数据字典中取数据源值。

    兼容三种形态：
    1. 扁平 key（上下文指标）：'dept.cpu_quota.remaining' 直接命中
    2. 点路径（嵌套结构）：'form.cpu' 按层取
    3. 表单字段兜底：'cpu'（无前缀）自动落到 data['form']['cpu']
    """
    if not name:
        return None
    def _get(obj, path):
        cur = obj
        for k in str(path).split('.'):
            if cur is None or not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

    if name in data:
        return data[name]
    v = _get(data, name)
    if v is None and not str(name).startswith('form.'):
        v = _get(data.get('form') or {}, name)
    return v


def _resolve_ref(cond, data):
    """解析参考值（返回待比较的 rhs）"""
    if cond.get('refType') == 'field':
        ref = resolve_source(cond.get('refField'), data)
        offset = cond.get('offset') or 0
        if offset:
            rn, on = _to_num(ref), _to_num(offset)
            if rn is not None and on is not None:
                return rn - on
        return ref
    return cond.get('fixed')


# ---------------------------------------------------------------------------
# 单条件求值
# ---------------------------------------------------------------------------
def eval_condition(cond: dict, data: dict) -> bool:
    lhs = resolve_source(cond.get('source'), data)
    op = cond.get('op')
    rhs = _resolve_ref(cond, data)

    # in / not_in：数组成员判断
    if op in ('in', 'not_in'):
        coll = rhs if isinstance(rhs, (list, tuple)) else lhs
        item = lhs if isinstance(rhs, (list, tuple)) else rhs
        if isinstance(coll, str):  # 子串
            inside = str(item) in coll
        else:
            inside = item in coll if coll is not None else False
        return not inside if op == 'not_in' else inside

    # contains / not_contains：文本子串
    if op in ('contains', 'not_contains'):
        hit = str(lhs or '') in str(rhs or '') or str(rhs or '') in str(lhs or '')
        return not hit if op == 'not_contains' else hit

    # matches：正则
    if op == 'matches':
        try:
            return re.search(str(rhs or ''), str(lhs or '')) is not None
        except re.error:
            return False

    # 数值比较
    ln, rn = _to_num(lhs), _to_num(rhs)
    if ln is not None and rn is not None:
        a, b = ln, rn
    else:
        a, b = _normalize(lhs), _normalize(rhs)

    try:
        if op == '>':
            return a > b
        if op == '>=':
            return a >= b
        if op == '<':
            return a < b
        if op == '<=':
            return a <= b
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
    except TypeError:
        return False
    return False


def condition_matched_text(cond: dict, data: dict) -> str:
    """生成命中条件的人话描述（用于详情展示）"""
    src = cond.get('source') or ''
    op = cond.get('op') or ''
    if cond.get('refType') == 'field':
        ref = cond.get('refField') or ''
        offset = cond.get('offset') or 0
        rhs_text = ref + (f' − {offset}' if offset > 0 else f' + {abs(offset)}' if offset < 0 else '')
    else:
        rhs_text = str(cond.get('fixed'))
    return f'{src} {op} {rhs_text}'


# 操作符中文名（判定明细展示）
OP_LABELS_ZH = {
    '>': '大于', '>=': '大于等于', '<': '小于', '<=': '小于等于',
    '==': '等于', '!=': '不等于',
    'in': '属于', 'not_in': '不属于',
    'contains': '包含', 'not_contains': '不包含', 'matches': '匹配',
}


def _label_of(labels, name):
    if labels and name in labels:
        return (labels[name] or {}).get('label') or name
    return name


def _fmt_value(v):
    if v is None:
        return '—'
    if isinstance(v, bool):
        return '是' if v else '否'
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else str(round(v, 2))
    if isinstance(v, (list, tuple)):
        return '、'.join(str(x) for x in v)
    return str(v)


def _condition_detail(cond: dict, data: dict, labels=None) -> dict:
    """生成单条件的判定明细（实际取值对比，供前端"为什么命中"展示）"""
    src = cond.get('source') or ''
    op = cond.get('op') or ''
    lhs = resolve_source(src, data)
    rhs = _resolve_ref(cond, data)
    is_field = cond.get('refType') == 'field'
    ref_label = _label_of(labels, cond.get('refField')) if is_field else ''
    return {
        'source': src,
        'source_label': _label_of(labels, src),
        'lhs_value': _fmt_value(lhs),
        'op': op,
        'op_label': OP_LABELS_ZH.get(op, op),
        'ref_type': 'field' if is_field else 'fixed',
        'ref_label': ref_label,
        'rhs_value': _fmt_value(rhs),
        'offset': cond.get('offset') or 0,
        'matched': bool(eval_condition(cond, data)),
    }


# ---------------------------------------------------------------------------
# 规则求值
# ---------------------------------------------------------------------------
def evaluate_rule(rule: dict, data: dict, labels=None) -> dict:
    """求值单条规则，返回 RuleResult（detail.conditions 为命中组的判定明细）"""
    groups = rule.get('groups') or []
    hit_conditions = []
    # 多组 OR；空组视为不匹配
    for group in groups:
        conds = group or []
        if not conds:
            continue
        if all(eval_condition(c, data) for c in conds):
            hit_conditions = list(conds)
            break
    passed = not hit_conditions
    return {
        'rule_id': rule.get('id') or '',
        'name': rule.get('name') or '',
        'level': rule.get('level') or LEVEL_ERROR,
        'passed': passed,
        'message': rule.get('message') or '',
        'suggestion': rule.get('suggestion') or '',
        'detail': {
            'matched': [condition_matched_text(c, data) for c in hit_conditions],
            'conditions': [_condition_detail(c, data, labels) for c in hit_conditions],
        },
    }


def evaluate_rules(rules: list, form_data: dict, user=None, labels=None) -> dict:
    """
    对一批规则求值（预检 / 提交权威校验共用）。

    labels: {source_name: {'label': 展示名}}，用于判定明细的中文展示（由调用方传入）

    返回：
        {'rules': [RuleResult...],
         'summary': {'total','passed','warnings','errors','blocked'}}
    """
    data = {'form': form_data or {}}
    data.update(build_context(form_data or {}, user))

    results = []
    for rule in rules or []:
        results.append(evaluate_rule(rule, data, labels=labels))

    errors = sum(1 for r in results if not r['passed'] and r['level'] == LEVEL_ERROR)
    warnings = sum(1 for r in results if not r['passed'] and r['level'] == LEVEL_WARNING)
    return {
        'rules': results,
        'summary': {
            'total': len(results),
            'passed': len(results) - errors - warnings,
            'warnings': warnings,
            'errors': errors,
            'blocked': errors > 0,
        },
    }


# ---------------------------------------------------------------------------
# 规则配置校验（flow_checker 复用）
# ---------------------------------------------------------------------------
def validate_rule(rule: dict, available_sources: set) -> list:
    """校验一条规则配置是否合法，返回错误信息列表（空 = 合法）"""
    errors = []
    if not (rule.get('name') or '').strip():
        errors.append('规则缺少名称')
    if rule.get('level') not in (LEVEL_ERROR, LEVEL_WARNING):
        errors.append('规则级别不合法（error/warning）')
    groups = rule.get('groups') or []
    if not groups:
        errors.append('规则缺少触发条件')
    for gi, group in enumerate(groups):
        if not group:
            errors.append(f'条件组 {gi + 1} 为空')
            continue
        for ci, c in enumerate(group):
            src = c.get('source')
            if not src:
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条缺少数据源')
                continue
            if available_sources and src not in available_sources:
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条数据源不存在：{src}')
            if c.get('op') not in OPERATORS:
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条操作符不合法：{c.get("op")}')
            if c.get('refType') == 'fixed' and c.get('fixed') in (None, ''):
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条缺少参考值')
            if c.get('refType') == 'field' and not c.get('refField'):
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条缺少引用字段/指标')
            elif c.get('refType') == 'field' and available_sources and c.get('refField') not in available_sources:
                errors.append(f'条件组 {gi + 1} 第 {ci + 1} 条引用字段不存在：{c.get("refField")}')
    return errors
