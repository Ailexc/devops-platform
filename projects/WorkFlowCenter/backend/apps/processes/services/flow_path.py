"""
审批路径预计算：提单前根据流程定义 + 表单数据，计算唯一审批路径（供发起预览/预检测）。

流程定义是 Beeflow 树形 nodeConfig；引擎运行时按 `definition_convert.normalized_definition`
生成的 nodes/edges 推进。这里用同样的节点/边与条件求值逻辑，但纯计算、不落库，
把「表单提交后实际会经过哪些节点」算出来。
"""
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .definition_convert import normalized_definition
from .engine import evaluate_condition

logger = logging.getLogger(__name__)

# 节点类型展示名
NODE_LABELS = {
    'start': '发起',
    'approve': '审批',
    'cc': '抄送',
    'handle': '办理',
    'service': '任务',
    'trigger': '触发器',
    'end': '结束',
}

# 需要展示在路径上的节点类型（网关/条件等路由节点不展示，只用于解析方向）
DISPLAY_TYPES = ('start', 'approve', 'cc', 'handle', 'end')

# 审批方式（设计器 multiInstanceApprovalType 数字 → 引擎 code + 中文）
MULTI_APPROVAL = {
    0: ('single', '单人审批'),
    1: ('countersign', '会签（需所有审批人同意）'),
    2: ('or_sign', '或签（一名审批人同意即可）'),
    3: ('sequential', '序签（按顺序审批）'),
}
# 办理节点执行模式
HANDLE_MODE = {
    'manual': '人工办理',
    'auto': '自动执行',
    'confirm': '自动执行 + 人工确认',
}
EXEC_MODE = {
    'sequential': '串行',
    'parallel': '并行',
}


def _user_names(ids):
    if not ids:
        return ''
    User = get_user_model()
    us = {u.id: (u.get_full_name() or u.username) for u in User.objects.filter(id__in=ids)}
    return '、'.join(us[i] for i in ids if i in us)


def _role_names(ids):
    if not ids:
        return ''
    groups = {g.id: g.name for g in Group.objects.filter(id__in=ids)}
    return '、'.join(groups[i] for i in ids if i in groups)


def _layer_text(item, leader=False):
    lv = item.get('layer') or 0
    unit = '部门负责人' if leader else '上级'
    if item.get('layerType') == 0:
        return f'直属{lv}级{unit}' if lv else f'直属{unit}'
    return f'最高{unit}减{lv}级'


def _resolve_handlers(items, type_key) -> str:
    """将办理人配置解析为可读文本（审批 assigneeType / 抄送 ccType / 办理 transactorType）"""
    parts = []
    for it in items or []:
        t = it.get(type_key)
        if t == 0:
            parts.append('发起人本人')
        elif t == 1:
            parts.append(_layer_text(it))
        elif t == 2:
            parts.append(_layer_text(it, leader=True))
        elif t == 3:
            parts.append(_role_names(it.get('roles') or []))
        elif t == 4:
            parts.append(_user_names(it.get('assignees') or []))
        elif t == 5:
            parts.append('连续多级上级')
        elif t == 6:
            parts.append('连续多级部门负责人')
        elif t == 7:
            parts.append('发起人自选')
    return '、'.join(p for p in parts if p) or '未设置'


def _handler_summary(node) -> str:
    """生成审批/抄送/办理节点的办理人摘要（预览展示用）"""
    ntype = node.get('type')
    if ntype == 'approve':
        return _resolve_handlers(node.get('assignees'), 'assigneeType')
    if ntype == 'cc':
        return _resolve_handlers(node.get('ccs'), 'ccType')
    if ntype == 'handle':
        task = node.get('taskConfig') or {}
        mode = task.get('mode', 'manual')
        transactor = _resolve_handlers(node.get('transactors'), 'transactorType')
        if mode != 'manual':
            order = '并行' if task.get('executionMode') == 'parallel' else '串行'
            mode_text = '自动+确认' if mode == 'confirm' else '自动执行'
            action_count = len(task.get('actions') or [])
            return f'{transactor}｜{mode_text}（{order}，{action_count} 个动作）'
        return transactor
    return ''


def _node_detail(node) -> dict:
    """生成节点结构化详情（供前端「审批预览 / 提单预检」右侧详情面板展示）"""
    ntype = node.get('type')
    detail = {}
    if ntype == 'approve':
        mi = node.get('multiInstanceApprovalType', 0)
        code, label = MULTI_APPROVAL.get(mi, (None, ''))
        detail['approval_type'] = {'code': code, 'label': label}
        detail['approvers'] = _resolve_handlers(node.get('assignees'), 'assigneeType')
    elif ntype == 'cc':
        detail['ccs'] = _resolve_handlers(node.get('ccs'), 'ccType')
    elif ntype == 'handle':
        task = node.get('taskConfig') or {}
        mode = task.get('mode', 'manual')
        exec_mode = task.get('executionMode', 'sequential')
        actions = task.get('actions') or []
        detail['mode'] = {'code': mode, 'label': HANDLE_MODE.get(mode, mode)}
        detail['execution_mode'] = {'code': exec_mode, 'label': EXEC_MODE.get(exec_mode, exec_mode)}
        detail['action_count'] = len(actions)
        detail['actions'] = [
            {'key': a.get('key'), 'name': a.get('name'), 'capability': a.get('capabilityCode')}
            for a in actions
        ]
        detail['handlers'] = _resolve_handlers(node.get('transactors'), 'transactorType')
    return detail


def compute_flow_path(definition_json: dict, form_data: dict) -> list:
    """
    根据流程定义与表单数据，计算提单前的唯一审批路径。

    返回有序的展示节点列表：
        [{'key', 'name', 'type', 'type_label', 'summary'}, ...]
    """
    nd = normalized_definition(definition_json)
    nodes = {n.get('key'): n for n in nd.get('nodes', []) if n.get('key')}
    edges = nd.get('edges', [])

    start_node = next((n for n in nodes.values() if n.get('type') == 'start'), None)
    if not start_node:
        return []

    path = []
    seen = set()
    current = start_node.get('key')

    while current and current not in seen:
        seen.add(current)
        node = nodes.get(current)
        if not node:
            break
        ntype = node.get('type')

        if ntype in DISPLAY_TYPES:
            path.append({
                'key': node.get('key'),
                'name': node.get('name') or NODE_LABELS.get(ntype, ntype),
                'type': ntype,
                'type_label': NODE_LABELS.get(ntype, ntype),
                'summary': _handler_summary(node),
                'detail': _node_detail(node),
            })
            if ntype == 'end':
                break

        # 解析下一条边
        outgoing = [e for e in edges if e.get('from') == current]
        if not outgoing:
            break
        if len(outgoing) == 1:
            current = outgoing[0].get('to')
        else:
            nxt = None
            for e in outgoing:
                cond = e.get('condition')
                if cond and evaluate_condition(cond, form_data):
                    nxt = e.get('to')
                    break
            if nxt is None:
                nxt = outgoing[-1].get('to')  # 默认分支
            current = nxt

    return path
