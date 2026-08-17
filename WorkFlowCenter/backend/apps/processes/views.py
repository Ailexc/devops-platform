from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

from .models import (
    ProcessDefinition,
    ProcessInstance,
    NodeTask,
    TaskInstance,
    ApprovalRecord,
    InitiatorApp,
    TestScenarioRun,
)
from .serializers import (
    ProcessDefinitionSerializer,
    InitiatorAppSerializer,
    ProcessInstanceSerializer,
    NodeTaskSerializer,
    TaskInstanceSerializer,
    ApprovalRecordSerializer,
    CheckDefinitionSerializer,
    StartProcessSerializer,
    CompleteTaskSerializer,
    DelegateTaskSerializer,
)
from .services.engine import ProcessEngine
from .services.flow_checker import FlowChecker
from .services.access import user_allowed_to_submit
from .services.security import generate_api_key, hash_api_key, verify_api_key
from django.utils import timezone


def _log_api_call(app_code, method, path, status_code, duration_ms, instance_no=''):
    """记录开放 API 调用日志（程序发起等外部调用）"""
    try:
        from .models import ApiCallLog, InitiatorApp
        app = InitiatorApp.objects.filter(code=app_code).first()
        ApiCallLog.objects.create(
            app=app,
            app_code=app_code,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            instance_no=instance_no,
            success=status_code < 400,
        )
    except Exception:
        pass

User = get_user_model()

# ===========================================================================
# 演示用模拟数据：多渠道审批 + 审批/办理备注
# 真实场景：审批人可通过 Web / Lark(飞书) 等多渠道处理，且可填写备注；
# 本演示环境无真实渠道/备注数据，这里确定性模拟用于前端展示。
# ===========================================================================
CHANNELS = [
    {'code': 'web', 'label': 'Web 渠道'},
    {'code': 'lark', 'label': 'Lark 飞书渠道'},
]
CHANNEL_LABEL = {c['code']: c['label'] for c in CHANNELS}

APPROVE_REMARKS = [
    '同意，请按申请内容执行。',
    '同意，注意控制成本与风险。',
    '同意，安排运维同事跟进。',
]
APPROVE_OPINIONS = [
    '同意，请按申请流程执行。',
    '同意，成本可控，予以批准。',
    '同意，请尽快安排实施。',
]
HANDLE_REMARKS = [
    '自动执行完成，资源已分配。',
    '自动执行完成，已通知申请人。',
    '自动执行完成，执行日志正常。',
]


def _mock_hash(key):
    """基于字符串的确定性小哈希（用于稳定模拟渠道/备注）"""
    return sum(ord(c) for c in key or '')


def _mock_channel(key):
    return 'lark' if _mock_hash(key) % 2 == 0 else 'web'


def _mock_remark(key, ntype):
    if ntype == 'approve':
        pool = APPROVE_REMARKS
    elif ntype == 'handle':
        pool = HANDLE_REMARKS
    else:
        return ''
    return pool[_mock_hash(key) % len(pool)]


def _mock_opinion(key, ntype):
    if ntype != 'approve':
        return ''
    return APPROVE_OPINIONS[_mock_hash(key) % len(APPROVE_OPINIONS)]


class ProcessDefinitionViewSet(viewsets.ModelViewSet):
    """流程定义视图集"""
    queryset = ProcessDefinition.objects.all()
    serializer_class = ProcessDefinitionSerializer
    filterset_fields = ['status', 'key', 'category']
    search_fields = ['name', 'key']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # 编辑已发布流程后自动回到草稿状态，需重新发布（避免「只有草稿状态的流程才能发布」的困惑）
        if serializer.instance.status == ProcessDefinition.Status.PUBLISHED:
            serializer.save(status=ProcessDefinition.Status.DRAFT)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """发布流程定义（仅草稿可发布，且须通过流程检查）"""
        definition = self.get_object()
        if definition.status != ProcessDefinition.Status.DRAFT:
            return Response(
                {'detail': '只有草稿状态的流程才能发布'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 发布前自检：存在错误项则拒绝发布
        check = FlowChecker(
            definition_data=definition.definition_json,
            form_schema=definition.form_schema,
            basic_info={
                'name': definition.name,
                'key': definition.key,
                'submit_scope': definition.submit_scope,
                'submit_scope_ids': definition.submit_scope_ids,
                'admin_ids': definition.admin_ids,
                'allow_program_initiate': definition.allow_program_initiate,
                'initiator_app_ids': definition.initiator_app_ids,
                'launch_status': definition.launch_status,
                'allow_self_approve': definition.allow_self_approve,
            },
            rules=definition.rules_json,
        ).check()
        if check['summary']['errors'] > 0:
            return Response(
                {'detail': f"流程存在 {check['summary']['errors']} 个错误项，请先修复后再发布"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        definition.status = ProcessDefinition.Status.PUBLISHED
        definition.save(update_fields=['status', 'updated_at'])
        return Response(ProcessDefinitionSerializer(definition).data)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """停用流程定义"""
        definition = self.get_object()
        if definition.status != ProcessDefinition.Status.PUBLISHED:
            return Response(
                {'detail': '只有已发布状态的流程才能停用'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        definition.status = ProcessDefinition.Status.DISABLED
        definition.save(update_fields=['status', 'updated_at'])
        return Response(ProcessDefinitionSerializer(definition).data)

    @action(detail=True, methods=['post'], url_path='check')
    def check(self, request, pk=None):
        """检查流程配置（基于已保存的定义）"""
        definition = self.get_object()
        result = FlowChecker(
            definition_data=definition.definition_json,
            form_schema=definition.form_schema,
            basic_info={
                'name': definition.name,
                'key': definition.key,
                'submit_scope': definition.submit_scope,
                'submit_scope_ids': definition.submit_scope_ids,
                'admin_ids': definition.admin_ids,
                'allow_program_initiate': definition.allow_program_initiate,
                'initiator_app_ids': definition.initiator_app_ids,
                'launch_status': definition.launch_status,
                'allow_self_approve': definition.allow_self_approve,
            },
            rules=definition.rules_json,
        ).check()
        return Response(result)

    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        """校验流程配置（无需保存，用于编辑器第 4 步实时检查）"""
        serializer = CheckDefinitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = FlowChecker(
            definition_data=data.get('definition_json', {}),
            form_schema=data.get('form_schema', {}),
            basic_info={
                'name': data.get('name', ''),
                'key': data.get('key', ''),
                'submit_scope': data.get('submit_scope', ''),
                'submit_scope_ids': data.get('submit_scope_ids', []),
                'admin_ids': data.get('admin_ids', []),
                'allow_program_initiate': data.get('allow_program_initiate', False),
                'initiator_app_ids': data.get('initiator_app_ids', []),
                'launch_status': data.get('launch_status', ''),
                'allow_self_approve': data.get('allow_self_approve', True),
            },
            rules=data.get('rules_json', []),
        ).check()
        return Response(result)

    @action(detail=True, methods=['post'], url_path='preview-path')
    def preview_path(self, request, pk=None):
        """根据表单数据预计算审批路径（提单前预览/预检测）"""
        from .services.flow_path import compute_flow_path

        definition = self.get_object()
        form_data = request.data.get('form_data') or {}
        return Response({'path': compute_flow_path(definition.definition_json, form_data)})

    @action(detail=True, methods=['get'], url_path='rule-meta')
    def rule_meta(self, request, pk=None):
        """返回可配置的数据源字典 + 操作符（供前端规则配置器下拉）"""
        from .services.rule_meta import rule_meta

        definition = self.get_object()
        return Response(rule_meta(definition.form_schema))

    @action(detail=True, methods=['post'], url_path='preview-check')
    def preview_check(self, request, pk=None):
        """提单预检：基础校验 + 业务规则求值 + 办理节点 Dry Run"""
        from .services.preview import preview_check

        definition = self.get_object()
        form_data = request.data.get('form_data') or {}
        user = request.user if request.user.is_authenticated else None
        return Response(preview_check(definition, form_data, user))

    @action(detail=True, methods=['post'], url_path='submit-check')
    def submit_check(self, request, pk=None):
        """提交权威复检（防绕过）：业务规则 error 级命中或基础校验失败则拒绝提交"""
        from .services.preview import preview_check

        definition = self.get_object()
        form_data = request.data.get('form_data') or {}
        user = request.user if request.user.is_authenticated else None
        result = preview_check(definition, form_data, user)
        if result['summary']['blocked']:
            return Response(
                {'detail': '提单预检未通过，请根据提示修改后重试', **result},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result)


class InitiatorAppViewSet(viewsets.ModelViewSet):
    """发起程序（外部接入方）视图集"""
    queryset = InitiatorApp.objects.all()
    serializer_class = InitiatorAppSerializer
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = generate_api_key()
        serializer.save(
            created_by=request.user,
            api_key_hash=hash_api_key(api_key),
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            {**serializer.data, 'api_key': api_key},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=['post'], url_path='reset-key')
    def reset_key(self, request, pk=None):
        """重置 API Key（返回一次明文）"""
        app = self.get_object()
        api_key = generate_api_key()
        app.api_key_hash = hash_api_key(api_key)
        app.save(update_fields=['api_key_hash', 'updated_at'])
        return Response({'id': app.id, 'api_key': api_key})

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """开放 API 调用统计：汇总 + 按接入方"""
        from .models import ApiCallLog
        summary = {
            'total': ApiCallLog.objects.count(),
            'success': ApiCallLog.objects.filter(success=True).count(),
            'failed': ApiCallLog.objects.filter(success=False).count(),
        }
        by_app = []
        for app in InitiatorApp.objects.all():
            qs = ApiCallLog.objects.filter(app=app)
            last = qs.order_by('-created_at').first()
            by_app.append({
                'id': app.id,
                'name': app.name,
                'code': app.code,
                'total': qs.count(),
                'failed': qs.filter(success=False).count(),
                'last_call_at': last.created_at if last else None,
                'last_status': last.status_code if last else None,
            })
        return Response({'summary': summary, 'by_app': by_app})


class ProcessInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """流程实例视图集"""
    queryset = ProcessInstance.objects.select_related('definition', 'started_by').all()
    serializer_class = ProcessInstanceSerializer
    filterset_fields = ['status', 'definition']
    search_fields = ['instance_no', 'business_key']

    def get_queryset(self):
        """支持 ?mine=1 仅返回当前用户发起的实例"""
        queryset = super().get_queryset()
        user = self.request.user
        if self.request.query_params.get('mine') == '1' and user and user.is_authenticated:
            queryset = queryset.filter(started_by=user)
        return queryset

    @action(detail=False, methods=['post'], url_path='start', url_name='start', permission_classes=[AllowAny])
    def start_process(self, request):
        """启动流程"""
        serializer = StartProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        app_code = request.headers.get('X-App-Code', '')
        app_key = request.headers.get('X-App-Key', '')

        # ---------------- 程序发起路径 ----------------
        if app_code or app_key:
            started_at = timezone.now()
            response = None
            try:
                response = self._start_by_app(request, data, app_code, app_key)
                return response
            finally:
                _log_api_call(
                    app_code=app_code,
                    method=request.method,
                    path=request.path,
                    status_code=response.status_code if response else 500,
                    duration_ms=int((timezone.now() - started_at).total_seconds() * 1000),
                    instance_no=((response.data or {}).get('instance_no', '') if response and hasattr(response, 'data') else ''),
                )

        # ---------------- 人员发起路径 ----------------
        user = request.user
        if not user or not user.is_authenticated:
            return Response(
                {'detail': '请先登录或使用程序发起凭证'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        definition = self._get_published_definition(data['definition_id'])
        if definition is None:
            return Response(
                {'detail': '流程定义不存在或未发布'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        allowed, reason = user_allowed_to_submit(definition, user)
        if not allowed:
            return Response({'detail': reason}, status=status.HTTP_403_FORBIDDEN)

        instance = ProcessEngine.start(
            definition=definition,
            form_data=data.get('form_data', {}),
            started_by=user,
            business_key=data.get('business_key', ''),
            initiator_source='',
        )
        return Response(
            ProcessInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    def _get_published_definition(self, definition_id):
        try:
            return ProcessDefinition.objects.get(
                pk=definition_id,
                status=ProcessDefinition.Status.PUBLISHED,
            )
        except ProcessDefinition.DoesNotExist:
            return None

    def _start_by_app(self, request, data, app_code, app_key):
        """程序发起路径：凭证认证 + 绑定校验 + 提单人校验 + 幂等"""
        if not app_code or not app_key:
            return Response(
                {'detail': '程序发起必须同时携带 X-App-Code 与 X-App-Key'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            app = InitiatorApp.objects.get(code=app_code)
        except InitiatorApp.DoesNotExist:
            return Response(
                {'detail': '程序凭证无效'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not app.is_active:
            return Response(
                {'detail': '该程序已停用'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not verify_api_key(app, app_key):
            return Response(
                {'detail': '程序凭证无效'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        definition = self._get_published_definition(data['definition_id'])
        if definition is None:
            return Response(
                {'detail': '流程定义不存在或未发布'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not definition.allow_program_initiate:
            return Response(
                {'detail': '该流程未开启程序发起'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if app.id not in (definition.initiator_app_ids or []):
            return Response(
                {'detail': f'程序「{app.name}」未绑定到该流程'},
                status=status.HTTP_403_FORBIDDEN,
            )

        initiator_user_id = data.get('initiator_user_id')
        if not initiator_user_id:
            return Response(
                {'detail': '程序发起必须指定提单人（initiator_user_id）'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            initiator = User.objects.get(pk=initiator_user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {'detail': '提单人不存在或已停用'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        allowed, reason = user_allowed_to_submit(definition, initiator)
        if not allowed:
            return Response({'detail': reason}, status=status.HTTP_403_FORBIDDEN)

        business_key = data.get('business_key', '')
        if not business_key:
            return Response(
                {'detail': '程序发起必须携带 business_key（用于幂等）'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 幂等：同一 business_key 重复发起返回已有实例
        existing = ProcessInstance.objects.filter(business_key=business_key).first()
        if existing:
            return Response(ProcessInstanceSerializer(existing).data)

        instance = ProcessEngine.start(
            definition=definition,
            form_data=data.get('form_data', {}),
            started_by=initiator,
            business_key=business_key,
            initiator_source=app.code,
        )
        return Response(
            ProcessInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend_process(self, request, pk=None):
        """挂起流程"""
        instance = ProcessEngine.suspend(int(pk))
        return Response(ProcessInstanceSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='resume')
    def resume_process(self, request, pk=None):
        """恢复流程"""
        instance = ProcessEngine.resume(int(pk))
        return Response(ProcessInstanceSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='terminate')
    def terminate_process(self, request, pk=None):
        """终止流程"""
        instance = ProcessEngine.terminate(int(pk), request.user)
        return Response(ProcessInstanceSerializer(instance).data)

    @action(detail=True, methods=['get'], url_path='approval-records')
    def approval_records(self, request, pk=None):
        """查看审批流水（发起 + 各审批/办理动作），含演示用渠道与备注"""
        instance = self.get_object()
        records = instance.approval_records.select_related('user', 'task').all()
        data = ApprovalRecordSerializer(records, many=True).data
        for rec, obj in zip(data, records):
            # 演示：审批/办理多渠道 + 备注（真实场景 Web/Lark、审批人可填备注）
            if obj.action in ('approve', 'reject', 'delegate'):
                ch = _mock_channel(f'{obj.id}-{obj.task_id or 0}')
                rec['channel'] = ch
                rec['channel_label'] = CHANNEL_LABEL.get(ch, '')
            else:
                rec['channel'] = ''
                rec['channel_label'] = ''
            if obj.action in ('approve', 'reject'):
                rec['remark'] = APPROVE_REMARKS[obj.id % len(APPROVE_REMARKS)]
            else:
                rec['remark'] = ''
        return Response(data)

    @action(detail=True, methods=['get'], url_path='tasks')
    def instance_tasks(self, request, pk=None):
        """查看流程下的所有任务"""
        instance = self.get_object()
        tasks = instance.node_tasks.all()
        return Response(NodeTaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=['get'], url_path='flow-status')
    def flow_status(self, request, pk=None):
        """申请详情：流程各节点运行状态与执行日志（点击节点查看）

        与提单预览同源：用 compute_flow_path 按实例表单数据计算「实际经过的审批路径」
        （路由/条件节点与被跳过的分支不展示），再叠加各节点任务/动作的执行状态与日志。
        """
        instance = self.get_object()
        definition = instance.definition
        from .services.flow_path import compute_flow_path
        path_nodes = compute_flow_path(definition.definition_json, instance.variables)

        # 原始节点定义（取 taskConfig 等配置，供 mode 展示）
        from .services.definition_convert import normalized_definition
        raw_nodes = {
            n.get('key'): n
            for n in normalized_definition(definition.definition_json)['nodes']
        }

        node_tasks = {
            t.node_key: t
            for t in instance.node_tasks.select_related('assignee').all()
        }
        jobs = list(
            instance.task_jobs.select_related('capability').order_by('created_at')
        )
        jobs_by_node = {}
        for j in jobs:
            jobs_by_node.setdefault(j.node_key, []).append(j)

        current = instance.current_node_key
        is_terminated = instance.status == ProcessInstance.Status.TERMINATED
        finished = instance.status in (
            ProcessInstance.Status.COMPLETED,
            ProcessInstance.Status.TERMINATED,
        )

        # 已终止实例（驳回/终止）：记录「最后实际走到」的节点下标。
        # 后续节点仍然展示（让用户知道还有哪些环节没走到），但标记为「未执行」，
        # 区别于正常完成流程里被路由跳过的「已跳过」。
        stop_index = None
        if is_terminated:
            for idx, pn in enumerate(path_nodes):
                if pn.get('key') in node_tasks:
                    stop_index = idx
            # 极早期终止（尚无任务）：只到发起节点为止
            if stop_index is None:
                stop_index = 0

        result = []
        for idx, pn in enumerate(path_nodes):
            key = pn.get('key')
            ntype = pn.get('type')
            raw = raw_nodes.get(key, {})
            task = node_tasks.get(key)
            node_jobs = jobs_by_node.get(key, [])
            if is_terminated and stop_index is not None and idx > stop_index:
                # 终止点之后的节点：实际未走到
                state = 'not_executed'
            elif task:
                # 驳回节点：展示为「已驳回」而非通用「已完成」
                if task.result == 'reject':
                    state = 'rejected'
                else:
                    state = task.status
            elif ntype == 'start':
                # 发起节点无任务，实例一经创建即已通过
                state = 'completed'
            elif ntype == 'end':
                state = 'completed' if finished else 'pending'
            elif key == current:
                state = 'completed' if finished else 'running'
            elif finished:
                state = 'skipped'
            else:
                state = 'pending'
            proxy_name = ''
            if task and task.assignee_id:
                proxy_name = task.assignee.get_full_name() or task.assignee.username
            # 演示：多渠道审批 + 意见/备注（真实场景 Web/Lark 多渠道、审批/办理人可填意见与备注）
            show_channel = ntype in ('approve', 'handle', 'cc')
            ch = _mock_channel(key)
            # 真实意见优先（剔除 E2E 测试通用文案），否则用模拟意见
            opinion = (task.opinion if task and task.opinion and 'E2E' not in task.opinion else '') or _mock_opinion(key, ntype)
            result.append({
                'key': key,
                'name': pn.get('name', ''),
                'type': ntype,
                'type_label': pn.get('type_label', ntype),
                'detail': pn.get('detail') or {},
                'status': state,
                'mode': (raw.get('taskConfig') or {}).get('mode') if ntype in ('handle', 'approve', 'cc') else None,
                'proxy_name': proxy_name,
                'error': task.opinion if task and task.status == NodeTask.Status.ABNORMAL else '',
                'channels': CHANNELS if show_channel else [],
                'channel': ch if show_channel else '',
                'channel_label': CHANNEL_LABEL.get(ch, '') if show_channel else '',
                'opinion': opinion,
                'remark': _mock_remark(key, ntype),
                'actions': [
                    {
                        'action_key': j.action_key,
                        'action_name': j.action_name or j.capability.name,
                        'capability_code': j.capability.code,
                        'sync': j.sync,  # 同步/异步执行标识（异步：提交队列即返回，结果经回调回写）
                        'status': j.status,
                        'error_message': j.error_message,
                        'input_data': j.input_data,
                        'output_data': j.output_data,
                        'logs': j.logs or [],
                        'created_at': j.created_at.isoformat(),
                    }
                    for j in node_jobs
                ],
            })

        return Response({
            'instance_no': instance.instance_no,
            'status': instance.status,
            'status_display': instance.get_status_display(),
            'current_node_key': instance.current_node_key,
            'nodes': result,
        })

    @action(detail=False, methods=['get'], url_path='e2e-meta')
    def e2e_meta(self, request):
        """测试模块：返回可测流程 + 测试场景（含各场景预设表单） + 表单 Schema"""
        from .services.e2e import get_scenarios

        defs = ProcessDefinition.objects.filter(status=ProcessDefinition.Status.PUBLISHED)
        items = [{
            'id': d.id,
            'key': d.key,
            'name': d.name,
            'submit_scope': d.submit_scope,
            'form_schema': d.form_schema or {},
            'rules_count': len(d.rules_json or []),
            'scenarios': [
                {
                    'key': s['key'],
                    'name': s['name'],
                    'mode': s['mode'],
                    'desc': s.get('desc', ''),
                    'preset_form': s.get('form', {}),
                }
                for s in get_scenarios(d.key)
            ],
        } for d in defs]
        return Response(items)

    @action(detail=False, methods=['get'], url_path='e2e-history')
    def e2e_history(self, request):
        """测试模块：返回某流程的测试场景运行记录（详情页测试记录）"""
        qs = TestScenarioRun.objects.select_related('definition', 'instance').order_by('-created_at')
        definition_key = request.query_params.get('definition_key')
        definition_id = request.query_params.get('definition_id')
        scenario_key = request.query_params.get('scenario_key')
        if definition_key:
            qs = qs.filter(definition__key=definition_key)
        if definition_id:
            qs = qs.filter(definition_id=definition_id)
        if scenario_key:
            qs = qs.filter(scenario_key=scenario_key)
        qs = qs[:50]
        return Response([{
            'id': r.id,
            'instance_id': r.instance_id,
            'instance_no': r.instance.instance_no if r.instance_id else '',
            'definition_key': r.definition.key,
            'definition_name': r.definition.name,
            'scenario_key': r.scenario_key,
            'scenario_name': r.scenario_name,
            'scenario_mode': r.scenario_mode,
            'scenario_mode_display': r.get_scenario_mode_display(),
            'ok': r.ok,
            'instance_status': r.instance.status if r.instance_id else '',
            'instance_status_display': r.instance.get_status_display() if r.instance_id else '',
            'summary': r.summary,
            'duration_ms': r.duration_ms,
            'started_at': r.created_at.isoformat() if r.created_at else None,
        } for r in qs])

    @action(detail=False, methods=['post'], url_path='e2e-run')
    def e2e_run(self, request):
        """测试模块：按测试场景跑通单个流程（提交→审批→自动办理→完成 / 进行中 / 异常 / 驳回）"""
        from .services.e2e import run_e2e

        result = run_e2e(
            definition_id=request.data.get('definition_id'),
            definition_key=request.data.get('definition_key'),
            form_data=request.data.get('form_data'),
            title=request.data.get('title', ''),
            scenario_key=request.data.get('scenario_key', ''),
        )
        return Response(result)


class NodeTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """节点任务视图集"""
    queryset = NodeTask.objects.select_related('instance', 'assignee').all()
    serializer_class = NodeTaskSerializer
    filterset_fields = ['status', 'node_type', 'assignee', 'instance']
    search_fields = ['node_name']

    def get_queryset(self):
        """支持按用户视角过滤：?type=todo|done|cc|created"""
        queryset = super().get_queryset()
        task_type = self.request.query_params.get('type')
        user = self.request.user
        if task_type and user and user.is_authenticated:
            if task_type == 'todo':
                # 待办：我是指定处理人或候选人，且未完成
                # 注意：SQLite 不支持 JSONField __contains，需 Python 层过滤候选人
                pending_statuses = [
                    NodeTask.Status.PENDING,
                    NodeTask.Status.CLAIMED,
                    NodeTask.Status.ABNORMAL,
                ]
                # 先拿到所有未完成任务的 PK 和 candidate_users
                all_pending = list(
                    queryset.filter(status__in=pending_statuses)
                    .values_list('pk', 'assignee_id', 'candidate_users')
                )
                matched_pks = [
                    pk for pk, assignee_id, candidates in all_pending
                    if assignee_id == user.id or user.id in (candidates or [])
                ]
                queryset = queryset.filter(pk__in=matched_pks)
            elif task_type == 'done':
                # 已办：我处理完成的
                queryset = queryset.filter(
                    assignee=user,
                    status=NodeTask.Status.COMPLETED,
                )
            elif task_type == 'cc':
                # 抄送我的
                queryset = queryset.filter(
                    approval_records__user=user,
                    approval_records__action='cc',
                ).distinct()
            elif task_type == 'created':
                # 我发起的
                queryset = queryset.filter(instance__started_by=user)
        return queryset

    @action(detail=False, methods=['get'], url_path='my')
    def my_tasks(self, request):
        """我的任务（统一入口，支持 type 过滤）"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NodeTaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(NodeTaskSerializer(queryset, many=True).data)

    @action(detail=True, methods=['post'], url_path='claim')
    def claim_task(self, request, pk=None):
        """签收任务"""
        task = ProcessEngine.claim(int(pk), request.user)
        return Response(NodeTaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_task(self, request, pk=None):
        """完成任务（审批通过/驳回）"""
        serializer = CompleteTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.validated_data['result']
        opinion = serializer.validated_data.get('opinion', '')

        # 审批意见必填
        if not opinion or not opinion.strip():
            return Response(
                {'detail': '审批意见不能为空'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if result == 'reject':
            task = ProcessEngine.reject(int(pk), request.user, opinion)
        else:
            task = ProcessEngine.complete(
                int(pk), request.user, result=result, opinion=opinion
            )
        return Response(NodeTaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='rerun')
    def rerun_task(self, request, pk=None):
        """异常任务：代理办理人重新执行失败的动作"""
        task = NodeTask.objects.select_for_update().get(pk=pk)
        ProcessEngine._assert_task_pending_or_claimed(task)
        ProcessEngine._assert_user_authorized(task, request.user)
        if task.status != NodeTask.Status.ABNORMAL:
            return Response(
                {'detail': '只有异常状态的自动办理任务可以重新执行'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .services.task_runner import AutoTaskError, rerun_node_actions
        try:
            rerun_node_actions(task.instance, task)
        except AutoTaskError as e:
            return Response(
                {'detail': f'重新执行失败：{e.message}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(NodeTaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='delegate')
    def delegate_task(self, request, pk=None):
        """转办任务"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        serializer = DelegateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            to_user = User.objects.get(pk=serializer.validated_data['to_user_id'])
        except User.DoesNotExist:
            return Response(
                {'detail': '目标用户不存在'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = ProcessEngine.delegate(int(pk), request.user, to_user)
        return Response(NodeTaskSerializer(task).data)

    @action(detail=False, methods=['get'], url_path='my-pending')
    def my_pending(self, request):
        """我待处理的任务"""
        tasks = NodeTask.objects.filter(
            assignee=request.user,
            status__in=[
                NodeTask.Status.PENDING,
                NodeTask.Status.CLAIMED,
                NodeTask.Status.ABNORMAL,
            ],
        ).select_related('instance')
        return Response(NodeTaskSerializer(tasks, many=True).data)


class TaskInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """任务实例视图集"""
    queryset = TaskInstance.objects.select_related('task', 'assignee').all()
    serializer_class = TaskInstanceSerializer
    filterset_fields = ['task', 'assignee', 'status']


class ApprovalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """审批记录视图集"""
    queryset = ApprovalRecord.objects.select_related('user', 'instance', 'task').all()
    serializer_class = ApprovalRecordSerializer
    filterset_fields = ['instance', 'user', 'action']
