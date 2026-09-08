"""
流程检查器（FlowChecker）

对流程配置（基本信息 + 表单设计 + 流程建模）执行完整检查，
返回结构化检查结果，用于前端第 4 步「检查」页面展示与跳转修复。

定义数据（Beeflow）节点类型：
    0 开始 / 1 审批 / 2 抄送 / 3 条件 / 4 排他网关 / 5 办理 / 6 触发器 / 9 结束

definition_json 结构:
{
    "nodeConfig": {...},
    "flowWidgets": [...],
    "workFlowDef": {...},
    "flowPermission": {...}
}

form_schema 结构:
{
    "rules": [...],   // form-create 规则
    "options": {}
}
"""
import re

from apps.processes.models import InitiatorApp

# ---------------------------------------------------------------------------
# 节点类型常量（与前端 FlowConstant.js 保持一致）
# ---------------------------------------------------------------------------
NODE_START = 0
NODE_APPROVE = 1
NODE_COPY = 2
NODE_CONDITION = 3
NODE_GATEWAY = 4
NODE_TRANSACT = 5
NODE_TRIGGER = 6
NODE_END = 9

# 需要配置处理人的节点类型
HANDLER_NODE_TYPES = (NODE_APPROVE, NODE_COPY, NODE_TRANSACT)

# 条件运算符号（近似校验用）
OPERATORS = {
    0: '==', 1: '!=', 2: '>', 3: '>=', 4: '<', 5: '<=',
    6: '包含', 7: '不包含', 8: '为空', 9: '不为空',
}

# 数值类组件类型（用于字段类型匹配校验）
NUMERIC_WIDGETS = {3, 4, 9, 23}  # 数字 / 金额 / 明细 / 公式


class CheckResult:
    """检查结果构建器"""

    def __init__(self):
        self.categories = []
        self.passed = True
        self.summary = {'total': 0, 'passed': 0, 'warnings': 0, 'errors': 0}

    def add_check(self, category, name, status, message, fix_action=None):
        """向指定分类追加一条检查记录"""
        check = {
            'name': name,
            'status': status,
            'message': message,
            'fixAction': fix_action,
        }
        for cat in self.categories:
            if cat['name'] == category:
                cat['checks'].append(check)
                if status == 'error':
                    cat['passed'] = False
                return

        # 分类不存在则新建
        self.categories.append({
            'name': category,
            'icon': self._category_icon(category),
            'passed': status != 'error',
            'checks': [check],
        })

    @staticmethod
    def _category_icon(name):
        icons = {
            '基本信息': 'document',
            '表单设计': 'form',
            '流程建模': 'share',
            '字段引用': 'link',
            '任务绑定': 'connection',
            '流程逻辑': 'set-up',
        }
        return icons.get(name, 'document')

    def finalize(self):
        """汇总统计并返回最终结果"""
        for cat in self.categories:
            for check in cat['checks']:
                self.summary['total'] += 1
                status = check['status']
                if status == 'error':
                    self.summary['errors'] += 1
                elif status == 'warning':
                    self.summary['warnings'] += 1
                else:
                    self.summary['passed'] += 1
            if not cat['passed']:
                self.passed = False
        return {
            'passed': self.passed,
            'summary': self.summary,
            'categories': self.categories,
        }


class FlowChecker:
    """流程检查器"""

    def __init__(self, definition_data: dict, form_schema: dict = None,
                 basic_info: dict = None, rules=None):
        self.definition_data = definition_data or {}
        self.form_schema = form_schema or {}
        self.basic_info = basic_info or {}
        self.rules = rules or []
        # 提取表单字段: name -> { label, type, options, required }
        self.fields = self._extract_fields(self.form_schema)
        # 提取流程表单组件（flowWidgets）
        self.flow_widgets = self._extract_widgets(self.definition_data.get('flowWidgets') or [])
        # 合并字段表（flowWidgets 优先级更高，name 相同以 flowWidgets 为准）
        self.fields.update(self.flow_widgets)
        self.nodes = []
        self.node_keys = set()

    # ====================================================================
    # 数据提取
    # ====================================================================
    @staticmethod
    def _extract_fields(form_schema):
        """从 form-create rules 中提取字段"""
        fields = {}
        rules = (form_schema or {}).get('rules') or []
        for rule in rules:
            name = rule.get('field') or rule.get('name')
            if not name:
                continue
            fields[name] = {
                'label': rule.get('title') or rule.get('label') or name,
                'type': rule.get('type'),
                'options': rule.get('options') or [],
                'required': bool(rule.get('required')),
            }
        return fields

    @staticmethod
    def _extract_widgets(flow_widgets):
        """从 flowWidgets 中提取字段"""
        fields = {}
        for w in flow_widgets or []:
            name = w.get('name')
            if not name:
                continue
            fields[name] = {
                'label': w.get('label') or name,
                'type': w.get('type'),
                'options': w.get('options') or [],
                'required': False,
            }
        return fields

    def _collect_nodes(self):
        """遍历节点树，收集所有节点（含网关分支内节点）"""
        self.nodes = []
        self.node_keys = set()

        # 平铺格式（引擎格式）：nodes 列表
        flat_nodes = self.definition_data.get('nodes')
        if isinstance(flat_nodes, list):
            self.nodes = list(flat_nodes)
            self.node_keys = {
                n.get('key') or n.get('name')
                for n in flat_nodes
                if n.get('key') or n.get('name')
            }
            return

        def walk(node):
            if not node:
                return
            self.nodes.append(node)
            key = node.get('key') or node.get('name')
            if key:
                self.node_keys.add(key)
            # 网关条件分支（walk 内部会递归其 childNode）
            for branch in node.get('conditionNodes') or []:
                walk(branch)
            # 普通子节点
            walk(node.get('childNode'))

        walk(self.definition_data.get('nodeConfig'))

    # ====================================================================
    # 检查入口
    # ====================================================================
    def check(self) -> dict:
        """执行完整检查，返回结构化结果"""
        self._collect_nodes()
        result = CheckResult()

        self._check_basic_info(result)
        self._check_form_design(result)
        self._check_flow_modeling(result)
        self._check_field_references(result)
        self._check_task_binding(result)
        self._check_flow_logic(result)
        self._check_rules(result)

        return result.finalize()

    # ====================================================================
    # 8. 业务规则配置检查
    # ====================================================================
    def _check_rules(self, result: CheckResult):
        from .context import available_metric_names
        from .rules import validate_rule

        rules = self.rules or []
        if not rules:
            result.add_check('业务规则', '业务规则配置', 'passed', '未配置业务规则（可选）')
            return
        sources = set(self.fields.keys()) | available_metric_names()
        all_errors = []
        for r in rules:
            for e in validate_rule(r, sources):
                all_errors.append(f'{r.get("id") or r.get("name") or "?"}：{e}')
        if all_errors:
            result.add_check(
                '业务规则', '业务规则配置', 'error',
                '；'.join(all_errors[:5]),
                '规则配置存在错误，请检查数据源、操作符与参考值',
            )
        else:
            result.add_check('业务规则', '业务规则配置', 'passed', f'{len(rules)} 条规则配置合法')

    # ====================================================================
    # 1. 基本信息检查
    # ====================================================================
    def _check_basic_info(self, result: CheckResult):
        info = self.basic_info or {}
        name = info.get('name')
        key = info.get('key')
        submit_scope = info.get('submit_scope')
        admin_ids = info.get('admin_ids') or []

        # 流程名称
        if name:
            result.add_check('基本信息', '流程名称', 'passed', '已填写')
        else:
            result.add_check('基本信息', '流程名称', 'error', '未填写流程名称',
                             {'type': 'jump', 'target': 'step_0', 'field': 'name'})

        # 唯一标识
        if not key:
            result.add_check('基本信息', '唯一标识', 'error', '未填写唯一标识',
                             {'type': 'jump', 'target': 'step_0', 'field': 'key'})
        elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', key):
            result.add_check('基本信息', '唯一标识', 'error',
                             '标识只能包含字母、数字和下划线，且以字母开头',
                             {'type': 'jump', 'target': 'step_0', 'field': 'key'})
        else:
            result.add_check('基本信息', '唯一标识', 'passed', '格式正确')

        # 提交范围
        if submit_scope:
            if submit_scope in ('specific_dept', 'specific_role'):
                ids = info.get('submit_scope_ids') or []
                if ids:
                    result.add_check('基本信息', '提交范围', 'passed', '已设置指定提交范围')
                else:
                    result.add_check('基本信息', '提交范围', 'error',
                                     '选择了指定部门/角色，但未选择具体部门或角色',
                                     {'type': 'jump', 'target': 'step_0', 'field': 'submit_scope_ids'})
            elif submit_scope == 'none':
                allow_program = info.get('allow_program_initiate', False)
                if allow_program:
                    result.add_check('基本信息', '提交范围', 'passed', '不允许人员提交（仅程序发起）')
                else:
                    result.add_check('基本信息', '提交范围', 'warning',
                                     '提交范围设为不允许提交，但未开启程序发起，流程将无法被发起',
                                     {'type': 'jump', 'target': 'step_0', 'field': 'allow_program_initiate'})
            else:
                result.add_check('基本信息', '提交范围', 'passed', '全员可提交')
        else:
            result.add_check('基本信息', '提交范围', 'error', '未设置提交范围',
                             {'type': 'jump', 'target': 'step_0', 'field': 'submit_scope'})

        # 流程管理员
        if admin_ids:
            result.add_check('基本信息', '流程管理员', 'passed', f'已设置 {len(admin_ids)} 名管理员')
        else:
            result.add_check('基本信息', '流程管理员', 'warning', '未设置流程管理员，建议设置以保证流程可维护',
                             {'type': 'jump', 'target': 'step_0', 'field': 'admin_ids'})

        # 程序发起
        allow_program = info.get('allow_program_initiate', False)
        app_ids = info.get('initiator_app_ids') or []
        if allow_program:
            if app_ids:
                active_count = InitiatorApp.objects.filter(id__in=app_ids, is_active=True).count()
                if active_count:
                    result.add_check('基本信息', '程序发起', 'passed', f'已绑定 {active_count} 个启用中的发起程序')
                else:
                    result.add_check('基本信息', '程序发起', 'error',
                                     '绑定的发起程序不存在或已停用',
                                     {'type': 'jump', 'target': 'step_0', 'field': 'initiator_app_ids'})
            else:
                result.add_check('基本信息', '程序发起', 'error',
                                 '已开启程序发起，但未绑定任何发起程序',
                                 {'type': 'jump', 'target': 'step_0', 'field': 'initiator_app_ids'})
        else:
            result.add_check('基本信息', '程序发起', 'passed', '未开启（仅人员发起）')

        # 上线状态
        launch_labels = {'offline': '未上线', 'debug': '调试上线', 'production': '正式上线'}
        launch_status = info.get('launch_status')
        if launch_status in launch_labels:
            result.add_check('基本信息', '上线状态', 'passed', launch_labels[launch_status])
        else:
            result.add_check('基本信息', '上线状态', 'warning', '未设置上线状态',
                             {'type': 'jump', 'target': 'step_0', 'field': 'launch_status'})

        # 允许发起人自己审批
        allow_self_approve = info.get('allow_self_approve', True)
        result.add_check('基本信息', '发起人自审', 'passed',
                         '允许发起人自己审批' if allow_self_approve else '不允许发起人自己审批')

    # ====================================================================
    # 2. 表单设计检查
    # ====================================================================
    def _check_form_design(self, result: CheckResult):
        rules = (self.form_schema or {}).get('rules') or []
        widgets = self.definition_data.get('flowWidgets') or []
        fields = self.fields

        # 表单是否有字段
        if rules or widgets:
            result.add_check('表单设计', '表单字段', 'passed', f'共 {len(fields)} 个字段')
        else:
            result.add_check('表单设计', '表单字段', 'error', '表单中没有任何字段',
                             {'type': 'jump', 'target': 'step_1'})

        # 字段名称是否重复
        seen = {}
        dup = []
        for w in widgets:
            name = w.get('name')
            if not name:
                continue
            if name in seen:
                dup.append(name)
            else:
                seen[name] = True
        if dup:
            result.add_check('表单设计', '字段重名', 'error',
                             f'存在重复字段名: {", ".join(set(dup))}',
                             {'type': 'jump', 'target': 'step_1'})
        else:
            result.add_check('表单设计', '字段重名', 'passed', '字段名称唯一')

        # 选项字段是否有选项值
        empty_option_fields = []
        for name, field in fields.items():
            ftype = field.get('type')
            if ftype in ('select', 'radio', 'checkbox', 'multi_select',
                         5, 6):  # 单选/多选
                options = field.get('options') or []
                if not options:
                    empty_option_fields.append(field.get('label') or name)
        if empty_option_fields:
            result.add_check('表单设计', '选项字段', 'warning',
                             f'以下选项字段缺少选项值: {", ".join(empty_option_fields[:3])}',
                             {'type': 'jump', 'target': 'step_1'})
        else:
            result.add_check('表单设计', '选项字段', 'passed', '选项字段配置完整')

        # 必填字段是否有默认值（仅对单行文本/数字/金额等给出警告）
        no_default_required = []
        for name, field in fields.items():
            if field.get('required') and not self._has_default(field):
                no_default_required.append(field.get('label') or name)
        if no_default_required:
            result.add_check('表单设计', '必填字段', 'warning',
                             f'必填字段未设置默认值: {", ".join(no_default_required[:3])}',
                             {'type': 'jump', 'target': 'step_1'})
        else:
            result.add_check('表单设计', '必填字段', 'passed', '必填字段配置合理')

    @staticmethod
    def _has_default(field):
        value = field.get('value')
        return value is not None and value != ''

    # ====================================================================
    # 3. 流程建模检查
    # ====================================================================
    def _check_flow_modeling(self, result: CheckResult):
        nodes = self.nodes
        node_config = self.definition_data.get('nodeConfig')

        # 是否有开始节点
        start_nodes = [n for n in nodes if n.get('type') == NODE_START]
        if start_nodes:
            result.add_check('流程建模', '开始节点', 'passed', '流程包含开始节点')
        else:
            result.add_check('流程建模', '开始节点', 'error', '缺少开始节点',
                             {'type': 'jump', 'target': 'step_2'})

        # 是否有结束节点
        end_nodes = [n for n in nodes if n.get('type') == NODE_END]
        if end_nodes:
            result.add_check('流程建模', '结束节点', 'passed', '流程包含结束节点')
        else:
            result.add_check('流程建模', '结束节点', 'error', '缺少结束节点，流程将无法正常结束',
                             {'type': 'jump', 'target': 'step_2'})

        # 是否只有一个开始节点
        if len(start_nodes) > 1:
            result.add_check('流程建模', '开始节点唯一', 'error', '流程存在多个开始节点',
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('流程建模', '开始节点唯一', 'passed', '开始节点唯一')

        # 节点处理人配置
        for node in nodes:
            ntype = node.get('type')
            if ntype not in HANDLER_NODE_TYPES:
                continue
            if ntype == NODE_APPROVE:
                self._check_approve_node(result, node)
            elif ntype == NODE_COPY:
                self._check_copy_node(result, node)
            elif ntype == NODE_TRANSACT:
                self._check_transact_node(result, node)

        # 条件分支是否有默认分支
        self._check_gateway_default(result)

    def _check_approve_node(self, result: CheckResult, node):
        # 审批节点仅支持人工审批（已去除「审批类型」配置）
        name = node.get('name') or '审批节点'
        assignees = node.get('assignees') or []
        if not assignees:
            result.add_check('流程建模', f'「{name}」', 'error', '未设置审批人',
                             {'type': 'jump', 'target': 'step_2'})
            return
        # 检查每个审批人配置是否完整
        incomplete = []
        for assignee in assignees:
            atype = assignee.get('assigneeType')
            if atype == 3 and not (assignee.get('roles') or []):  # 角色
                incomplete.append('角色未选择')
            elif atype == 4 and not (assignee.get('assignees') or []):  # 指定成员
                incomplete.append('成员未选择')
            elif atype == 1 and assignee.get('layer') is None:  # 上级
                incomplete.append('上级层级未选择')
            elif atype == 2 and assignee.get('layer') is None:  # 部门负责人
                incomplete.append('部门负责人层级未选择')
        if incomplete:
            result.add_check('流程建模', f'「{name}」', 'warning',
                             f'审批人配置不完整: {"; ".join(incomplete)}',
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('流程建模', f'「{name}」', 'passed', f'已配置 {len(assignees)} 组审批人')

    def _check_copy_node(self, result: CheckResult, node):
        name = node.get('name') or '抄送节点'
        ccs = node.get('ccs') or []
        if not ccs:
            result.add_check('流程建模', f'「{name}」', 'error', '未设置抄送人',
                             {'type': 'jump', 'target': 'step_2'})
            return
        incomplete = []
        for cc in ccs:
            ctype = cc.get('ccType')
            if ctype == 3 and not (cc.get('roles') or []):
                incomplete.append('角色未选择')
            elif ctype == 4 and not (cc.get('assignees') or []):
                incomplete.append('成员未选择')
        if incomplete:
            result.add_check('流程建模', f'「{name}」', 'warning',
                             f'抄送人配置不完整: {"; ".join(incomplete)}',
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('流程建模', f'「{name}」', 'passed', f'已配置 {len(ccs)} 组抄送人')

    def _check_transact_node(self, result: CheckResult, node):
        name = node.get('name') or '办理节点'
        transactors = node.get('transactors') or []
        if not transactors:
            result.add_check('流程建模', f'「{name}」', 'error', '未设置办理人',
                             {'type': 'jump', 'target': 'step_2'})
            return
        if len(transactors) < 2:
            result.add_check('流程建模', f'「{name}」', 'error',
                             '办理人至少配置 2 组（自动模式作为代理池，人工模式保证可接手）',
                             {'type': 'jump', 'target': 'step_2'})
            return
        incomplete = []
        for transactor in transactors:
            ttype = transactor.get('transactorType')
            if ttype == 3 and not (transactor.get('roles') or []):
                incomplete.append('角色未选择')
            elif ttype == 4 and not (transactor.get('assignees') or []):
                incomplete.append('成员未选择')
        if incomplete:
            result.add_check('流程建模', f'「{name}」', 'warning',
                             f'办理人配置不完整: {"; ".join(incomplete)}',
                             {'type': 'jump', 'target': 'step_2'})
            return

        task_config = node.get('taskConfig') or {}
        mode = task_config.get('mode', 'manual')
        if mode not in ('manual', 'confirm', 'auto'):
            result.add_check('流程建模', f'「{name}」', 'error', '执行方式配置无效',
                             {'type': 'jump', 'target': 'step_2'})
            return
        if mode == 'manual':
            result.add_check('流程建模', f'「{name}」', 'passed',
                             f'人工办理，已配置 {len(transactors)} 组办理人')
            return

        # ---- 自动执行 / 自动执行+人工确认（任务配置）校验 ----
        actions = task_config.get('actions') or []
        if not actions:
            result.add_check('流程建模', f'「{name}」', 'error', '自动执行未配置任何动作',
                             {'type': 'jump', 'target': 'step_2'})
            return
        execution_mode = task_config.get('executionMode', 'sequential')
        if execution_mode not in ('sequential', 'parallel'):
            result.add_check('流程建模', f'「{name}」', 'error', '执行顺序配置无效',
                             {'type': 'jump', 'target': 'step_2'})
            return

        action_order = [a.get('key') for a in actions]
        action_errors = []
        for action in actions:
            action_name = action.get('name') or '未命名动作'
            if not action.get('capabilityId'):
                action_errors.append(f'动作「{action_name}」未选择能力')
                continue
            for bind in action.get('fieldBindings') or []:
                field = bind.get('capabilityField')
                source = bind.get('source', 'form')
                if source == 'form' and not bind.get('formField'):
                    action_errors.append(f'动作「{action_name}」参数「{field}」未绑定表单字段')
                elif source == 'upstream' and not (bind.get('upstreamNode') and bind.get('upstreamField')):
                    action_errors.append(f'动作「{action_name}」参数「{field}」未绑定上游输出')
                elif source == 'previous':
                    if execution_mode != 'sequential':
                        action_errors.append(f'动作「{action_name}」参数「{field}」使用了前序动作输出，并行模式不支持')
                    elif bind.get('previousActionKey') not in action_order or \
                            action_order.index(bind.get('previousActionKey')) >= action_order.index(action.get('key')):
                        action_errors.append(f'动作「{action_name}」参数「{field}」引用的前序动作无效')
        if action_errors:
            result.add_check('流程建模', f'「{name}」', 'error',
                             '；'.join(action_errors[:4]),
                             {'type': 'jump', 'target': 'step_2'})
            return
        result.add_check('流程建模', f'「{name}」', 'passed',
                         f'{"自动执行+人工确认" if mode == "confirm" else "自动执行"}，'
                         f'{len(actions)} 个动作，{"串行" if execution_mode == "sequential" else "并行"}执行')

    def _check_gateway_default(self, result: CheckResult):
        gateways = [n for n in self.nodes if n.get('type') == NODE_GATEWAY]
        if not gateways:
            return
        checked = 0
        for gw in gateways:
            branches = gw.get('conditionNodes') or []
            if not branches:
                result.add_check('流程建模', '条件分支', 'error', '条件分支下没有任何分支',
                                 {'type': 'jump', 'target': 'step_2'})
                checked += 1
                continue
            # 判断是否有默认分支（最后一个分支没有条件组，或标记为默认）
            default_branch = branches[-1]
            is_default = not (default_branch.get('conditionGroups') or [])
            if is_default:
                result.add_check('流程建模', '条件分支', 'passed', '条件分支包含默认分支')
            else:
                result.add_check('流程建模', '条件分支', 'warning',
                                 '条件分支未设置默认分支，可能存在无法覆盖的情况',
                                 {'type': 'jump', 'target': 'step_2'})
            checked += 1

    # ====================================================================
    # 4. 字段引用检查
    # ====================================================================
    def _check_field_references(self, result: CheckResult):
        ref_errors = []
        ref_warnings = []

        def walk(node):
            if not node:
                return
            # 条件分支引用的字段
            for branch in node.get('conditionNodes') or []:
                for group in branch.get('conditionGroups') or []:
                    for cond in group.get('conditions') or []:
                        var_name = cond.get('varName')
                        if not var_name:
                            continue
                        if var_name == 'INITIATOR':  # 发起人变量
                            continue
                        if var_name not in self.fields:
                            ref_errors.append(f'条件「{branch.get("name", "")}」引用了不存在的字段「{var_name}」')
                        else:
                            # 类型匹配：数值运算用于非数值字段
                            op = cond.get('operator')
                            if op in (2, 3, 4, 5) and not self._is_numeric_field(var_name):
                                ref_warnings.append(
                                    f'条件「{branch.get("name", "")}」对非数值字段「{var_name}」使用了比较运算')
            # 表单权限引用的字段
            for perm in (node.get('formPerms') or []):
                field = perm.get('field') or perm.get('name')
                if field and field not in self.fields:
                    ref_errors.append(f'表单权限引用了不存在的字段「{field}」')
            # 操作权限引用的字段
            for perm in (node.get('actionPerms') or []):
                field = perm.get('field') or perm.get('name')
                if field and field not in self.fields:
                    ref_errors.append(f'操作权限引用了不存在的字段「{field}」')
            # 递归
            for branch in node.get('conditionNodes') or []:
                walk(branch)
            walk(node.get('childNode'))

        walk(self.definition_data.get('nodeConfig'))

        if ref_errors:
            result.add_check('字段引用', '字段引用', 'error', '；'.join(ref_errors[:5]),
                             {'type': 'jump', 'target': 'step_2'})
        elif ref_warnings:
            result.add_check('字段引用', '字段引用', 'warning', '；'.join(ref_warnings[:5]),
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('字段引用', '字段引用', 'passed', '字段引用全部有效')

    def _is_numeric_field(self, name):
        field = self.fields.get(name) or {}
        ftype = field.get('type')
        # form-create 组件类型
        if ftype in ('inputNumber', 'number', 'money', 'amount', 'rate', 'slider'):
            return True
        # Beeflow widget 类型
        if isinstance(ftype, int) and ftype in NUMERIC_WIDGETS:
            return True
        return False

    # ====================================================================
    # 5. 任务绑定检查
    # ====================================================================
    def _check_task_binding(self, result: CheckResult):
        # 任务配置：办理节点自动执行动作的字段绑定校验
        transact_nodes = [
            n for n in self.nodes
            if n.get('type') in (NODE_TRANSACT, 'handle')
        ]
        enabled_nodes = []
        issues = []

        for node in transact_nodes:
            task_config = node.get('taskConfig') or {}
            if task_config.get('mode') not in ('auto', 'confirm'):
                continue
            name = node.get('name') or '办理节点'
            for action in task_config.get('actions') or []:
                action_name = action.get('name') or '未命名动作'
                for bind in action.get('fieldBindings') or []:
                    if bind.get('source') == 'form':
                        form_field = bind.get('formField')
                        if form_field and form_field not in self.fields:
                            issues.append(f'「{name}」动作「{action_name}」绑定的表单字段「{form_field}」不存在')
            enabled_nodes.append(name)

        if issues:
            result.add_check('任务绑定', '任务配置', 'error', '；'.join(issues[:5]),
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('任务绑定', '任务配置', 'passed',
                             f'已启用 {len(enabled_nodes)} 个自动执行节点' if enabled_nodes else '未启用自动执行')

    # ====================================================================
    # 6. 流程逻辑检查
    # ====================================================================
    def _check_flow_logic(self, result: CheckResult):
        node_config = self.definition_data.get('nodeConfig')
        if not node_config:
            result.add_check('流程逻辑', '流程结构', 'error', '流程定义为空',
                             {'type': 'jump', 'target': 'step_2'})
            return

        # 环检测（DFS）
        cycle = self._detect_cycle(node_config)
        if cycle:
            result.add_check('流程逻辑', '循环引用', 'error', '流程中存在循环引用，可能导致流程无法结束',
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('流程逻辑', '循环引用', 'passed', '未检测到循环引用')

        # 结束节点可达性：从开始节点出发是否能够到达结束节点
        reachable = self._can_reach_end(node_config)
        if reachable:
            result.add_check('流程逻辑', '结束可达', 'passed', '从开始节点可以到达结束节点')
        else:
            result.add_check('流程逻辑', '结束可达', 'error', '部分分支无法到达结束节点，请检查节点连线',
                             {'type': 'jump', 'target': 'step_2'})

        # 条件分支覆盖：所有分支是否都有后续节点
        uncovered = []
        for node in self.nodes:
            if node.get('type') != NODE_GATEWAY:
                continue
            for branch in node.get('conditionNodes') or []:
                if not branch.get('childNode'):
                    uncovered.append(branch.get('name') or '分支')
        if uncovered:
            result.add_check('流程逻辑', '分支覆盖', 'warning',
                             f'以下条件分支没有后续节点: {", ".join(uncovered[:3])}',
                             {'type': 'jump', 'target': 'step_2'})
        else:
            result.add_check('流程逻辑', '分支覆盖', 'passed', '条件分支均有后续节点')

    def _detect_cycle(self, node_config):
        """DFS 检测节点树中是否存在环（通过 childNode 递归）"""
        visited = set()
        path = set()
        cycle_found = [False]

        def dfs(node):
            if not node or cycle_found[0]:
                return
            key = node.get('key') or node.get('name')
            if key in path:
                cycle_found[0] = True
                return
            if key in visited:
                return
            path.add(key)
            for branch in node.get('conditionNodes') or []:
                dfs(branch)
            dfs(node.get('childNode'))
            path.discard(key)
            if key:
                visited.add(key)

        dfs(node_config)
        return cycle_found[0]

    def _can_reach_end(self, node_config):
        """判断是否存在路径能到达结束节点（宽松：任意路径可达即通过）"""
        found = [False]

        def dfs(node):
            if not node or found[0]:
                return
            if node.get('type') == NODE_END:
                found[0] = True
                return
            for branch in node.get('conditionNodes') or []:
                dfs(branch)
            dfs(node.get('childNode'))

        dfs(node_config)
        return found[0]
