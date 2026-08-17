"""
流程定义格式转换：设计器树形格式 → 引擎平铺格式

设计器（前端）产出的 definition_json 为树形 nodeConfig（数字节点类型），
引擎需要平铺的 {nodes, edges}（字符串节点类型）。此模块负责转换；
已是平铺格式（如种子数据）则原样返回。

节点类型映射：
  0 开始 / 1 审批 / 2 抄送 / 3 条件 / 4 排他网关 / 5 办理 / 6 触发器 / 9 结束
"""

# 数字类型 → 引擎字符串类型
NODE_TYPE_MAP = {
    0: 'start',
    1: 'approve',
    2: 'cc',
    3: 'condition',
    4: 'gateway',
    5: 'handle',
    6: 'trigger',
    9: 'end',
}

# 条件运算符（与前端 FunNames / flow_checker OPERATORS 一致）
OP_MAP = {
    0: '==',
    1: '!=',
    2: '>',
    3: '>=',
    4: '<',
    5: '<=',
}


def _build_expression(branch):
    """将设计器条件分组转换为引擎表达式，如 amount > 10000"""
    parts = []
    for group in branch.get('conditionGroups') or []:
        for cond in group.get('conditions') or []:
            var = cond.get('varName')
            op = OP_MAP.get(cond.get('operator'))
            val = cond.get('val')
            if not var or op is None:
                continue
            if isinstance(val, str):
                val = f"'{val}'"
            parts.append(f'{var} {op} {val}')
    return ' and '.join(parts)


def normalized_definition(definition_json: dict) -> dict:
    """返回引擎可执行的 {nodes, edges}；已是平铺格式则原样返回"""
    if not isinstance(definition_json, dict):
        return {'nodes': [], 'edges': []}
    if 'nodes' in definition_json and 'edges' in definition_json:
        return definition_json

    node_config = definition_json.get('nodeConfig')
    if not node_config:
        return {'nodes': [], 'edges': []}

    nodes = []
    edges = []
    seen = set()
    added_edges = set()

    def emit(node):
        key = node.get('key')
        if not key or key in seen:
            return
        seen.add(key)
        n = dict(node)
        n['type'] = NODE_TYPE_MAP.get(node.get('type'), 'handle')
        nodes.append(n)

    def add_edge(frm, to, condition=None):
        """加边（去重）：网关多分支可能共享下游，重复边仅保留一条"""
        ekey = (frm, to)
        if ekey in added_edges:
            return
        added_edges.add(ekey)
        edges.append({
            'from': frm,
            'to': to,
            'condition': condition or None,
        })

    def walk(node, parent_key=None, edge_condition=''):
        if not node:
            return
        key = node.get('key')
        if not key:
            return
        if key in seen:
            # 节点已遍历（如网关多分支共享下游节点）：仅补入边，不再发射/递归
            if parent_key:
                add_edge(parent_key, key, edge_condition)
            return
        emit(node)
        if parent_key:
            add_edge(parent_key, key, edge_condition)

        ntype = node.get('type')
        if ntype == 4:
            # 排他网关：分支各自成边，最后一条为默认；各分支末端可汇入网关 childNode
            branches = node.get('conditionNodes') or []
            continuation = node.get('childNode')
            for i, branch in enumerate(branches):
                bkey = branch.get('key')
                if not bkey:
                    continue
                cond = '' if i == len(branches) - 1 else _build_expression(branch)
                emit(branch)
                add_edge(key, bkey, cond or None)
                # 分支内部链路（无论是否有汇合点都要遍历，分支可各自走向独立结束节点）
                bchild = branch.get('childNode')
                if bchild:
                    walk(bchild, parent_key=bkey)
                    if continuation:
                        # 分支链末端汇入网关 childNode
                        last = bchild
                        while last.get('childNode'):
                            last = last['childNode']
                        if last.get('key') and last.get('key') != continuation.get('key'):
                            add_edge(last['key'], continuation['key'])
                elif continuation:
                    add_edge(bkey, continuation['key'])
            # 主链路继续
            walk(continuation)
        else:
            walk(node.get('childNode'), parent_key=key)

    walk(node_config)
    return {'nodes': nodes, 'edges': edges}
