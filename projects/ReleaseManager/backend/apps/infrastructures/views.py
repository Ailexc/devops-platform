from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Environment, Cluster, K8sNamespace
from .serializers import EnvironmentSerializer, ClusterSerializer, K8sNamespaceSerializer
from apps.applications.models import Application, AppEnvConfig
from apps.authz.models import ReleaseApprovalConfig


@api_view(['GET', 'POST'])
def environment_list(request):
    if request.method == 'GET':
        queryset = Environment.objects.all()
        serializer = EnvironmentSerializer(queryset, many=True)
        return Response({'code': 200, 'data': serializer.data})

    elif request.method == 'POST':
        serializer = EnvironmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def cluster_list(request):
    queryset = Cluster.objects.all()
    environment_id = request.query_params.get('environment_id')
    if environment_id:
        queryset = queryset.filter(environment_id=environment_id)
    serializer = ClusterSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['POST'])
def cluster_create(request):
    serializer = ClusterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def namespace_list(request):
    queryset = K8sNamespace.objects.all()
    cluster_id = request.query_params.get('cluster_id')
    if cluster_id:
        queryset = queryset.filter(cluster_id=cluster_id)
    serializer = K8sNamespaceSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['POST'])
def scale_application(request, app_id):
    """
    实例伸缩接口
    POST /api/v1/apps/{id}/scale/
    {"env_code": "dev", "target_replicas": 0, "reason": "夜间停机节省资源"}
    """
    import logging
    logger = logging.getLogger(__name__)

    app = Application.objects.filter(pk=app_id).first()
    if not app:
        return Response({'code': 404, 'message': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)

    env_code = request.data.get('env_code')
    target_replicas = request.data.get('target_replicas')
    reason = request.data.get('reason', '')

    if not env_code:
        return Response({'code': 400, 'message': 'env_code 不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    if target_replicas is None:
        return Response({'code': 400, 'message': 'target_replicas 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    env = Environment.objects.filter(code=env_code).first()
    if not env:
        return Response({'code': 404, 'message': f'环境 {env_code} 不存在'}, status=status.HTTP_404_NOT_FOUND)

    env_config = AppEnvConfig.objects.filter(application=app, environment=env).first()
    if not env_config:
        return Response({'code': 404, 'message': f'应用在 {env_code} 环境没有配置'}, status=status.HTTP_404_NOT_FOUND)

    # 校验不能超过配置上限
    if target_replicas > env_config.replicas:
        return Response(
            {'code': 400, 'message': f'目标实例数({target_replicas})不能超过应用配置的环境副本数上限({env_config.replicas})'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if target_replicas < 0:
        return Response({'code': 400, 'message': '目标实例数不能为负数'}, status=status.HTTP_400_BAD_REQUEST)

    # 查询审批配置
    approval_config = ReleaseApprovalConfig.objects.filter(env_type=env.env_type, is_active=True).first()

    if approval_config and approval_config.requires_approval:
        # 需要审批 — 复用 Approval 表（使用 Approval 模型的发布审批通道，release 可为 None）
        from apps.approvals.models import Approval

        current_replicas = env_config.replicas
        action_type = 'scale_down' if target_replicas < current_replicas else 'scale_up'
        if target_replicas == 0:
            action_type = 'stop'
        elif current_replicas == 0:
            action_type = 'start'

        action_labels = {
            'stop': '停机', 'start': '启动',
            'scale_up': '扩容', 'scale_down': '缩容',
        }

        approval = Approval.objects.create(
            approval_type='scale',
            release=None,
            approver=request.user,
            action='pending',
            comment=f"实例伸缩: {app.name} ({env.name}) {current_replicas} → {target_replicas}{f'. {reason}' if reason else ''}",
            extra_data={
                'app_id': app.id,
                'app_name': app.name,
                'env_code': env.code,
                'env_name': env.name,
                'deploy_type': env.deploy_type,
                'current_replicas': current_replicas,
                'target_replicas': target_replicas,
                'action_type': action_type,
                'action_label': action_labels.get(action_type, '伸缩'),
                'reason': reason,
            },
        )

        return Response({
            'code': 200,
            'data': {
                'requires_approval': True,
                'approval_id': approval.id,
                'message': '伸缩操作需审批，已提交审批单',
            }
        })

    # 无需审批，创建 Release 记录 + 提交执行
    import datetime
    import random
    from apps.releases.models import Release, ReleaseTask

    current_replicas = env_config.replicas
    action_type = 'scale_down' if target_replicas < current_replicas else 'scale_up'
    if target_replicas == 0:
        action_type = 'stop'
    elif current_replicas == 0:
        action_type = 'start'

    action_labels = {
        'stop': '停机', 'start': '启动',
        'scale_up': '扩容', 'scale_down': '缩容',
    }

    # 生成发布单号
    today = datetime.date.today().strftime('%Y%m%d')
    suffix = f'{random.randint(0, 9999):04d}'
    release_no = f'REL-{today}-{suffix}'

    release = Release.objects.create(
        release_no=release_no,
        title=f'实例伸缩: {action_labels.get(action_type, "伸缩")} {current_replicas} → {target_replicas}',
        description=reason or '',
        application=app,
        env_config=env_config,
        environment=env,
        version='',
        image_tag='',
        status='completed',
        approval_status='not_needed',
        need_approval=False,
        release_mode='scale',
        deploy_strategy=env_config.deploy_strategy,
        deploy_mode=env.deploy_type,
        current_replicas=current_replicas,
        target_replicas=target_replicas,
        creator=request.user,
    )

    try:
        from utils import executor_client
        params = {
            'name': app.code,
            'namespace': env_config.namespace.name if env_config.namespace else 'release-demo',
            'replicas': target_replicas,
            'env_code': env.code,
            'deploy_type': env.deploy_type,
        }
        result = executor_client.submit('scale', params)
        execution_id = result.get('execution_id', '')
        logger.info(f"伸缩执行已提交: {app.code}/{env.code} → {target_replicas}, exec_id={execution_id}")
    except Exception as e:
        logger.error(f"伸缩执行提交失败: {e}")
        return Response(
            {'code': 500, 'message': f'执行端提交失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({
        'code': 200,
        'data': {
            'requires_approval': False,
            'execution_id': execution_id,
            'release_id': release.id,
            'message': f"{action_labels.get(action_type, '伸缩')}: {current_replicas} → {target_replicas}",
        }
    })


@api_view(['POST'])
def application_operations(request, app_id):
    """
    统一运维操作入口：重启 / 停机 / 启动 / 实例伸缩 / 流量管理
    POST /api/v1/apps/{id}/operations/
    {"env_code": "dev", "action": "restart|stop|start|scale|traffic",
     "target_replicas": 5, "traffic_action": "take_out|restore", "reason": "可选"}
    所有运维操作统一创建发布单（release_mode 区分），逻辑与 scale_application 对齐。
    """
    import logging
    import datetime
    import random
    logger = logging.getLogger(__name__)

    app = Application.objects.filter(pk=app_id).first()
    if not app:
        return Response({'code': 404, 'message': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)

    env_code = request.data.get('env_code')
    action = request.data.get('action')
    reason = request.data.get('reason', '')

    if not env_code:
        return Response({'code': 400, 'message': 'env_code 不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    if action not in ('restart', 'stop', 'start', 'scale', 'traffic'):
        return Response({'code': 400, 'message': f'不支持的 action: {action}'},
                        status=status.HTTP_400_BAD_REQUEST)

    env = Environment.objects.filter(code=env_code).first()
    if not env:
        return Response({'code': 404, 'message': f'环境 {env_code} 不存在'}, status=status.HTTP_404_NOT_FOUND)

    env_config = AppEnvConfig.objects.filter(application=app, environment=env).first()
    if not env_config:
        return Response({'code': 404, 'message': f'应用在 {env_code} 环境没有配置'},
                        status=status.HTTP_404_NOT_FOUND)

    # action → release_mode / executor op / 参数映射
    action_meta = {
        'restart': {'release_mode': 'restart', 'op': 'restart', 'label': '重启',
                    'target_replicas': env_config.replicas},
        'stop': {'release_mode': 'stop', 'op': 'scale', 'label': '停机', 'target_replicas': 0},
        'start': {'release_mode': 'start', 'op': 'scale', 'label': '启动',
                  'target_replicas': env_config.replicas},
    }

    if action == 'scale':
        target_replicas = request.data.get('target_replicas')
        if target_replicas is None:
            return Response({'code': 400, 'message': 'scale 操作需要 target_replicas'},
                            status=status.HTTP_400_BAD_REQUEST)
        if target_replicas > env_config.replicas:
            return Response({'code': 400,
                             'message': f'目标实例数({target_replicas})不能超过应用配置的环境副本数上限({env_config.replicas})'},
                            status=status.HTTP_400_BAD_REQUEST)
        if target_replicas < 0:
            return Response({'code': 400, 'message': '目标实例数不能为负数'},
                            status=status.HTTP_400_BAD_REQUEST)
        action_meta['scale'] = {'release_mode': 'scale', 'op': 'scale', 'label': '实例伸缩',
                                'target_replicas': target_replicas}

    if action == 'traffic':
        traffic_action = request.data.get('traffic_action')
        if traffic_action not in ('take_out', 'restore'):
            return Response({'code': 400,
                             'message': 'traffic 操作需要 traffic_action (take_out/restore)'},
                            status=status.HTTP_400_BAD_REQUEST)
        action_meta['traffic'] = {'release_mode': 'traffic', 'op': 'traffic', 'label': '流量管理',
                                  'target_replicas': env_config.replicas,
                                  'traffic_action': traffic_action}

    meta = action_meta[action]
    current_replicas = env_config.replicas
    target_replicas = meta['target_replicas']

    # 审批判定
    approval_config = ReleaseApprovalConfig.objects.filter(env_type=env.env_type, is_active=True).first()
    if approval_config and approval_config.requires_approval:
        from apps.approvals.models import Approval
        approval = Approval.objects.create(
            approval_type='ops',
            release=None,
            approver=request.user,
            action='pending',
            comment=f"{meta['label']}: {app.name} ({env.name}){f'. {reason}' if reason else ''}",
            extra_data={
                'app_id': app.id,
                'app_name': app.name,
                'env_code': env.code,
                'env_name': env.name,
                'deploy_type': env.deploy_type,
                'action': action,
                'action_label': meta['label'],
                'current_replicas': current_replicas,
                'target_replicas': target_replicas,
                'traffic_action': meta.get('traffic_action', ''),
                'reason': reason,
            },
        )
        return Response({
            'code': 200,
            'data': {
                'requires_approval': True,
                'approval_id': approval.id,
                'message': f'{meta["label"]}操作需审批，已提交审批单',
            }
        })

    # 无需审批：创建 Release 记录 + 提交 executor
    from apps.releases.models import Release

    today = datetime.date.today().strftime('%Y%m%d')
    suffix = f'{random.randint(0, 9999):04d}'
    release_no = f'REL-{today}-{suffix}'

    release = Release.objects.create(
        release_no=release_no,
        title=f'{meta["label"]}: {app.name} ({env.name})',
        description=reason or '',
        application=app,
        env_config=env_config,
        environment=env,
        version='',
        image_tag='',
        status='completed',
        approval_status='not_needed',
        need_approval=False,
        release_mode=meta['release_mode'],
        deploy_strategy=env_config.deploy_strategy,
        deploy_mode=env.deploy_type,
        current_replicas=current_replicas,
        target_replicas=target_replicas,
        traffic_action=meta.get('traffic_action', ''),
        creator=request.user,
    )

    try:
        from utils import executor_client
        params = {
            'name': app.code,
            'namespace': env_config.namespace.name if env_config.namespace else 'release-demo',
            'replicas': target_replicas,
            'env_code': env.code,
            'deploy_type': env.deploy_type,
            'release_no': release.release_no,
        }
        if action == 'traffic':
            params['traffic_action'] = meta['traffic_action']
        result = executor_client.submit(meta['op'], params)
        execution_id = result.get('execution_id', '')
        logger.info(f"运维操作已提交: {app.code}/{env.code} action={action} exec_id={execution_id}")
    except Exception as e:
        logger.error(f"运维操作执行提交失败: {e}")
        return Response({'code': 500, 'message': f'执行端提交失败: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'code': 200,
        'data': {
            'requires_approval': False,
            'execution_id': execution_id,
            'release_id': release.id,
            'message': f"{meta['label']}: {current_replicas} → {target_replicas}",
        }
    })