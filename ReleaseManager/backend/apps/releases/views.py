import datetime
import json
import logging
import random
import threading

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Release, ReleaseTask, TaskLog, ReleaseVerification
from .serializers import (ReleaseSerializer, ReleaseTaskSerializer, TaskLogSerializer,
                          ReleaseVerificationSerializer)
from apps.applications.models import Application, AppEnvConfig
from apps.audit.models import AuditLog
from apps.approvals.models import Approval
from apps.deployments.models import DeployHistory, RollbackRecord
from apps.authz.utils import get_user_accessible_app_ids
from utils import executor_client

logger = logging.getLogger(__name__)

DEPLOY_STAGES = {'cd'}  # Per-Environment: 只有 CD 阶段走 executor


def _generate_release_no():
    today = datetime.date.today().strftime('%Y%m%d')
    suffix = f'{random.randint(0, 9999):04d}'
    return f'REL-{today}-{suffix}'


def _create_release_tasks(release):
    """Per-Environment 模型：每个发布单固定 CI + CD 两步"""
    tasks = []
    for stage, _ in ReleaseTask.STAGES:
        tasks.append(ReleaseTask(release=release, stage=stage))
    ReleaseTask.objects.bulk_create(tasks)


def _create_audit_log(user, action, resource_type, resource_id, detail=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail or {},
    )


def _stage_to_op(stage):
    """发布阶段 → executor 操作类型映射（Per-Environment）"""
    if stage == 'ci':
        return 'build'
    if stage == 'cd':
        return 'deploy'
    return stage


def _create_release_tasks(release):
    """Per-Environment 模型：每个发布单固定 CI + CD 两步"""
    tasks = []
    for stage, _ in ReleaseTask.STAGES:
        tasks.append(ReleaseTask(release=release, stage=stage))
    ReleaseTask.objects.bulk_create(tasks)


def _watch_execution(task_id, release_id, execution_id, user):
    """
    后台线程：订阅 executor 的 SSE 日志流并写入 TaskLog，
    执行结束后回写任务状态。CI 完成后自动触发 CD。
    """
    try:
        task = ReleaseTask.objects.select_related(
            'release', 'release__application', 'release__environment', 'release__env_config'
        ).get(id=task_id)
    except ReleaseTask.DoesNotExist:
        return

    try:
        for event in executor_client.stream_logs(execution_id):
            try:
                data = json.loads(event)
            except (ValueError, TypeError):
                continue
            if data.get('event') == 'done':
                break
            TaskLog.objects.create(
                task=task,
                level=data.get('level', 'info'),
                message=data.get('message', ''),
            )
        final = executor_client.get_execution(execution_id)
    except Exception as e:
        logger.error(f'与 executor 同步失败 (execution={execution_id}): {e}')
        TaskLog.objects.create(task=task, level='error', message=f'与执行端同步失败: {e}')
        task.status = 'failed'
        task.message = f'与执行端同步失败: {e}'
        task.finished_at = datetime.datetime.now()
        task.save(update_fields=['status', 'finished_at', 'message'])
        # 同步失败也要更新发布单状态
        release.status = 'failed'
        release.save(update_fields=['status'])
        return

    release = task.release

    if final['status'] == 'success':
        task.status = 'success'
        result = final.get('result') or {}
        task.message = result.get('message', '执行成功')
    else:
        task.status = 'failed'
        task.message = final.get('error') or (final.get('result') or {}).get('message', '执行失败')
    task.finished_at = datetime.datetime.now()
    task.save(update_fields=['status', 'finished_at', 'message'])

    TaskLog.objects.create(
        task=task,
        level='info' if task.status == 'success' else 'error',
        message=f'阶段任务{"执行成功" if task.status == "success" else "执行失败"}',
    )

    # CI 成功 → 自动触发 CD；CI 失败 → 更新发布单状态
    if task.stage == 'ci':
        if task.status == 'success':
            _auto_trigger_cd(release, user)
        elif task.status == 'failed':
            release.status = 'failed'
            release.save(update_fields=['status'])

    # CD 完成 → 更新发布单状态
    if task.stage == 'cd':
        release.current_stage = 'cd'
        release.save(update_fields=['current_stage'])
        if task.status == 'success':
            release.status = 'completed'
            release.save(update_fields=['status'])
            # 配置随发布走：本次发布对应的配置版本已随 CD 下发到集群，标记为已应用
            release.config_releases.filter(status='pending').update(status='applied')
            # 写入部署历史
            DeployHistory.objects.create(
                release=release,
                application=release.application,
                environment=release.environment,
                version=release.version,
                image_tag=release.image_tag,
                action='deploy',
                status='success',
                strategy=release.deploy_strategy,
                canary_percent=release.canary_percent,
                created_by=user,
            )
            # 自动触发发布验证：仅对常规发布（rolling/blue_green/canary），
            # 运维类（restart/stop/scale/traffic）不触发
            if release.release_mode == 'regular':
                threading.Thread(
                    target=_trigger_verification,
                    args=(release, user),
                    daemon=True,
                ).start()
        elif task.status == 'failed':
            release.status = 'failed'
            release.save(update_fields=['status'])

    _create_audit_log(user, 'deploy', 'release', release.id,
                      {'release_no': release.release_no, 'stage': task.stage,
                       'status': task.status, 'execution_id': execution_id})


def _render_release_config(release):
    """按 应用×环境 渲染该应用所有启用配置模板，返回 {template_name: rendered_content}

    同时记录 ConfigRelease（配置版本随发布走）：
      - 版本号 = 同模板同环境最大版本 + 1（无历史从 1 开始）
      - 无模板时返回空 dict（下发跳过，不报错）
    渲染异常向上抛出 → 由调用方中断本次发布。
    """
    from apps.configs.models import ConfigTemplate, ConfigRelease
    from apps.configs.views import render_template

    env = release.environment
    result = {}
    templates = ConfigTemplate.objects.filter(
        application=release.application, is_active=True
    )
    for tpl in templates:
        # 系统变量注入：{{ version }} = 发布单版本号、{{ release_no }} = 发布单号
        # （优先于模板静态变量，保证配置内容与发布验证读到的版本一致）
        content = render_template(tpl, env, system_vars={
            'version': release.version,
            'release_no': release.release_no,
        })
        last = ConfigRelease.objects.filter(
            template=tpl, environment=env
        ).order_by('-version').first()
        version = (last.version + 1) if last else 1
        ConfigRelease.objects.create(
            template=tpl, environment=env, version=version,
            rendered_content=content, release=release,
            created_by=release.creator,
        )
        result[tpl.name] = content
    return result


def _auto_trigger_cd(release, user):
    """CI 完成后自动触发 CD 部署"""
    try:
        cd_task = release.tasks.get(stage='cd')
    except ReleaseTask.DoesNotExist:
        return

    cd_task.status = 'running'
    cd_task.started_at = datetime.datetime.now()
    cd_task.operator = user
    cd_task.save(update_fields=['status', 'started_at', 'operator'])

    app = release.application
    env_config = release.env_config
    ns = env_config.namespace.name if env_config.namespace else "release-demo"
    image = f"123456789.dkr.ecr.us-east-1.amazonaws.com/{app.code}:{release.version}"

    # 判断首次部署（查询该应用在该环境是否已有成功部署记录）
    is_first = not DeployHistory.objects.filter(
        application=app, environment=release.environment, action='deploy', status='success'
    ).exists()

    # 按部署策略分发 CD 操作：滚动=deploy，蓝绿=blue_green，灰度=canary
    strategy = release.deploy_strategy or 'rolling'
    op = 'deploy'
    if strategy == 'blue_green':
        op = 'blue_green'
    elif strategy == 'canary':
        op = 'canary'

    params = {
        'namespace': ns,
        'name': app.code,
        'image': image,
        'replicas': env_config.replicas,
        'env_code': release.environment.code if hasattr(release.environment, 'code') else 'dev',
        'version': release.version,
        'release_no': release.release_no,
        'stage': 'cd',
        'is_first_deploy': is_first,
        'deploy_type': release.deploy_mode or 'k8s',
        'canary_replicas': 1,
    }

    # 配置随发布走：按 应用×环境 渲染配置模板 → 记录 ConfigRelease → 随 CD 传参下发。
    # 渲染失败 → 中断发布（配置错误不应带病上线），与 CD failed 分支一致。
    try:
        configs = _render_release_config(release)
    except Exception as e:
        logger.error(f'配置渲染失败 (release={release.release_no}): {e}')
        cd_task.status = 'failed'
        cd_task.message = f'配置渲染失败: {e}'
        cd_task.finished_at = datetime.datetime.now()
        cd_task.save(update_fields=['status', 'message', 'finished_at'])
        release.status = 'failed'
        release.save(update_fields=['status'])
        TaskLog.objects.create(task=cd_task, level='error', message=f'配置渲染失败: {e}')
        return
    if configs:
        params['configs'] = configs

    try:
        execution = executor_client.submit(op, params)
        execution_id = execution['execution_id']
        cd_task.message = f'CI 完成，自动触发 CD (execution_id={execution_id})'
        cd_task.save(update_fields=['message'])
        TaskLog.objects.create(
            task=cd_task, level='info',
            message=f'CI 构建完成，自动触发 CD 部署 (execution_id={execution_id})',
        )
        # 后台线程消费 CD 日志
        threading.Thread(
            target=_watch_execution,
            args=(cd_task.id, release.id, execution_id, user),
            daemon=True,
        ).start()
    except Exception as e:
        logger.error(f'自动触发 CD 失败: {e}')
        cd_task.status = 'failed'
        cd_task.message = f'触发 CD 失败: {e}'
        cd_task.finished_at = datetime.datetime.now()
        cd_task.save(update_fields=['status', 'finished_at', 'message'])


# ── 发布自动验证（op=verify）────────────────────────────────


def _trigger_verification(release, user):
    """创建验证记录（running）→ 提交 executor op=verify → 后台线程回写结果"""
    try:
        verification = ReleaseVerification.objects.create(
            release=release, status='running', created_by=user,
        )
    except Exception as e:
        logger.error(f'创建验证记录失败: {e}')
        return

    app = release.application
    env_config = release.env_config
    ns = env_config.namespace.name if env_config.namespace else "release-demo"
    env_code = release.environment.code if hasattr(release.environment, 'code') else 'dev'
    params = {
        'name': app.code,
        'env_code': env_code,
        'version': release.version,
        'deploy_strategy': release.deploy_strategy or 'rolling',
        'namespace': ns,
        'release_no': release.release_no,
    }
    try:
        execution = executor_client.submit('verify', params)
        execution_id = execution['execution_id']
        logger.info(f'已提交发布验证 release={release.id} execution_id={execution_id}')
        threading.Thread(
            target=_watch_verification,
            args=(verification.id, execution_id),
            daemon=True,
        ).start()
    except Exception as e:
        logger.error(f'提交验证执行失败: {e}')
        verification.status = 'failed'
        verification.summary = f'提交验证执行失败: {e}'
        verification.save(update_fields=['status', 'summary'])


def _watch_verification(verification_id, execution_id):
    """
    后台线程：等待 executor op=verify 完成（SSE 直到 done），
    回写验证记录 status / results / summary。
    """
    try:
        verification = ReleaseVerification.objects.get(id=verification_id)
    except ReleaseVerification.DoesNotExist:
        return

    try:
        for event in executor_client.stream_logs(execution_id):
            try:
                data = json.loads(event)
            except (ValueError, TypeError):
                continue
            if data.get('event') == 'done':
                break
        final = executor_client.get_execution(execution_id)
    except Exception as e:
        logger.error(f'验证执行同步失败 (execution={execution_id}): {e}')
        verification.status = 'failed'
        verification.summary = f'与执行端同步失败: {e}'
        verification.save(update_fields=['status', 'summary'])
        return

    result = final.get('result') or {}
    ver_status = result.get('status')
    if ver_status not in ('success', 'failed', 'skipped'):
        ver_status = 'success' if final.get('status') == 'success' else 'failed'
    verification.status = ver_status
    verification.results = result.get('checks', [])
    verification.summary = result.get('summary', '')
    verification.save(update_fields=['status', 'results', 'summary'])


# ─── 1. 发布单列表 / 创建 ──────────────────────────────────


@api_view(['GET', 'POST'])
def release_list(request):
    if request.method == 'GET':
        # 获取用户有权限的应用 ID，按权限过滤发布单
        allowed_app_ids = get_user_accessible_app_ids(request.user)
        qs = Release.objects.filter(
            application_id__in=allowed_app_ids
        ).select_related('application', 'environment', 'creator')
        # 按应用筛选
        app_id = request.query_params.get('app')
        if app_id:
            qs = qs.filter(application_id=app_id)
        # 按环境筛选
        env_id = request.query_params.get('environment')
        if env_id:
            qs = qs.filter(env_config__environment_id=env_id)
        # 按状态筛选
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = ReleaseSerializer(qs, many=True)
        return Response({'code': 200, 'data': serializer.data})

    # POST — 创建发布单（Per-Environment：单个环境）
    data = request.data.copy()

    env_config_id = data.get('env_config')
    if env_config_id and not data.get('environment'):
        try:
            env_cfg = AppEnvConfig.objects.get(id=env_config_id)
            data['environment'] = env_cfg.environment_id
        except AppEnvConfig.DoesNotExist:
            pass

    serializer = ReleaseSerializer(data=data)
    if not serializer.is_valid():
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    app_id = data.get('application')
    deploy_mode = 'k8s'
    if app_id:
        try:
            # app.deploy_mode 可能为 None（种子数据缺陷），兜底为 k8s，避免 NOT NULL 约束失败
            deploy_mode = Application.objects.get(id=app_id).deploy_mode or 'k8s'
        except Application.DoesNotExist:
            pass

    # 判断是否需要审批：根据审批策略表
    env_id = data.get('environment')
    need_approval = False  # 默认不需要
    if env_id:
        try:
            from apps.infrastructures.models import Environment
            from apps.releases.strategy import ReleaseApprovalStrategy
            env = Environment.objects.get(id=env_id)
            strategy = ReleaseApprovalStrategy.objects.filter(environment=env).first()
            if strategy and strategy.mode != 'none':
                need_approval = True
        except Environment.DoesNotExist:
            pass

    release = serializer.save(
        creator=request.user,
        release_no=_generate_release_no(),
        deploy_mode=deploy_mode,
        status='draft',
        approval_status='not_needed' if not need_approval else 'not_submitted',
        need_approval=need_approval,
    )
    _create_release_tasks(release)
    _create_audit_log(request.user, 'create', 'release', release.id,
                      {'release_no': release.release_no, 'title': release.title})

    return Response({'code': 200, 'data': ReleaseSerializer(release).data},
                    status=status.HTTP_201_CREATED)


# ─── 1.1 发起审批 ─────────────────────────────────────────


def _resolve_approver(release, source):
    """根据审批人来源动态解析审批人"""
    from apps.accounts.models import User
    app = release.application

    if source == 'app_owner':
        # 应用负责人
        owner_id = getattr(app, 'owner_id', None)
        if owner_id:
            return User.objects.filter(id=owner_id).first()
        # fallback: owner_ids 列表
        owner_ids = getattr(app, 'owner_ids', []) or []
        if owner_ids:
            return User.objects.filter(id__in=owner_ids).first()
    elif source == 'group_leader':
        # 组负责人：应用所属组的组长
        owner_group = getattr(app, 'owner_group', None)
        if owner_group:
            leader = getattr(owner_group, 'leader', None)
            if leader:
                return leader
    elif source == 'bl_leader':
        # 业务线负责人
        bl = getattr(app, 'business_line', None)
        if bl:
            leader = getattr(bl, 'leader', None)
            if leader:
                return leader

    return None


@api_view(['POST'])
def submit_approval(request, release_id):
    """发起审批：根据审批策略动态分发审批人"""
    try:
        release = Release.objects.select_related('environment', 'application').get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    if not release.need_approval:
        return Response({'code': 400, 'message': '该发布无需审批，可直接发布'}, status=status.HTTP_400_BAD_REQUEST)

    if release.approval_status not in ('not_submitted', 'rejected'):
        return Response({'code': 400, 'message': f'当前审批状态 ({release.approval_status}) 不可发起'},
                        status=status.HTTP_400_BAD_REQUEST)

    if release.status == 'completed':
        return Response({'code': 400, 'message': '已完成的发布单不可发起审批'}, status=status.HTTP_400_BAD_REQUEST)

    # 查询审批策略
    from apps.releases.strategy import ReleaseApprovalStrategy
    strategy = ReleaseApprovalStrategy.objects.filter(environment=release.environment).first()

    if not strategy or strategy.mode == 'none':
        release.approval_status = 'passed'
        release.status = 'approved'
        release.save(update_fields=['approval_status', 'status'])
        _create_audit_log(request.user, 'auto_approve', 'release', release.id,
                          {'release_no': release.release_no})
        return Response({'code': 200, 'message': '无需审批，已自动通过',
                         'data': ReleaseSerializer(release).data})

    # 动态解析审批人
    if strategy.mode == 'single':
        approver = _resolve_approver(release, strategy.approver_source)
        if approver:
            Approval.objects.create(
                approval_type='release', release=release, approver=approver,
                action='pending', step_order=1,
                step_name=f'{strategy.get_approver_source_display()}审批',
                total_steps=1,
            )
    elif strategy.mode == 'multi' and strategy.step_sources:
        for i, step in enumerate(strategy.step_sources):
            approver = _resolve_approver(release, step.get('source', strategy.approver_source))
            if approver:
                Approval.objects.create(
                    approval_type='release', release=release, approver=approver,
                    action='pending', step_order=i + 1,
                    step_name=step.get('name', f'步骤 {i+1}'),
                    total_steps=len(strategy.step_sources),
                )

    release.approval_status = 'submitting'
    release.save(update_fields=['approval_status'])

    approvers = Approval.objects.filter(release=release, approval_type='release', action='pending')
    _create_audit_log(request.user, 'submit_approval', 'release', release.id,
                      {'release_no': release.release_no, 'strategy': strategy.get_mode_display(),
                       'approvers': [a.approver.display_name for a in approvers]})

    return Response({'code': 200, 'message': '审批已提交', 'data': ReleaseSerializer(release).data})


# ─── 1.2 审批操作（通过/驳回）──────────────────────────────


@api_view(['POST'])
def approve_action(request, release_id):
    """审批通过或驳回 —— release_id 也可能是 approval_id（兼容两种调用）"""
    # 兼容：如果传入的是 approval_id，直接找到对应的 release
    approval_obj = Approval.objects.filter(id=release_id).first()
    if approval_obj and approval_obj.release:
        release = approval_obj.release
        action = request.data.get('action', 'approved')
        comment = request.data.get('comment', '')
    else:
        try:
            release = Release.objects.get(id=release_id)
        except Release.DoesNotExist:
            return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)
        action = request.data.get('action', 'approved')
        comment = request.data.get('comment', '')

    if release.approval_status != 'submitting':
        return Response({'code': 400, 'message': '当前不在审批中状态'}, status=status.HTTP_400_BAD_REQUEST)

    # 找到最新的 pending 审批记录并更新
    if approval_obj and approval_obj.action == 'pending':
        approval_obj.action = 'approved' if action == 'approved' else 'rejected'
        approval_obj.comment = comment
        approval_obj.save(update_fields=['action', 'comment'])
    else:
        approval_record = Approval.objects.filter(release=release, action='pending').first()
        if approval_record:
            approval_record.action = 'approved' if action == 'approved' else 'rejected'
            approval_record.comment = comment
            approval_record.save(update_fields=['action', 'comment'])

    release.approval_status = 'passed' if action == 'approved' else 'rejected'
    release.status = 'approved' if action == 'approved' else 'rejected'
    release.save(update_fields=['approval_status', 'status'])

    _create_audit_log(request.user, 'approve', 'release', release.id,
                      {'release_no': release.release_no, 'action': action})

    return Response({'code': 200, 'message': f'审批已{"通过" if action == "approved" else "驳回"}',
                     'data': ReleaseSerializer(release).data})


# ─── 1.3 执行发布（真正触发 CI→CD）────────────────────────


@api_view(['POST'])
def execute_release(request, release_id):
    """人工点击「发布」：触发 CI→CD 执行"""
    try:
        release = Release.objects.select_related('application').get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    # 校验状态
    if release.status not in ('draft', 'approved'):
        msg = '草稿或审批通过后才可发布'
        if release.need_approval and release.approval_status != 'passed':
            msg = '需要审批通过后才可发布'
        return Response({'code': 400, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)

    if release.need_approval and release.approval_status != 'passed':
        return Response({'code': 400, 'message': '审批尚未通过，请先完成审批'}, status=status.HTTP_400_BAD_REQUEST)

    # 更新状态
    release.status = 'running'
    release.current_stage = 'ci'
    release.save(update_fields=['status', 'current_stage'])

    # 触发 CI
    ci_task = release.tasks.get(stage='ci')
    ci_task.status = 'running'
    ci_task.started_at = datetime.datetime.now()
    ci_task.operator = request.user
    ci_task.save(update_fields=['status', 'started_at', 'operator'])

    env_config = release.env_config
    app = release.application
    language = app.language if hasattr(app, 'language') else 'python'
    params = {
        'name': app.code,
        'version': release.version,
        'branch': release.branch or 'main',
        'commit_id': release.commit_id or 'abc1234',
        'language': language,
        'repo_url': app.repo_url or f'https://gitlab.internal/spug/{app.code}.git',
        'builder_image': getattr(app, 'builder_image', '') or '',
        'base_image': getattr(app, 'base_image', '') or '',
        'release_no': release.release_no,
        'stage': 'ci',
    }

    try:
        execution = executor_client.submit('build', params)
        execution_id = execution['execution_id']
        ci_task.message = f'已提交构建 (execution_id={execution_id})'
        ci_task.save(update_fields=['message'])
        TaskLog.objects.create(
            task=ci_task, level='info',
            message=f'CI 构建已提交 (execution_id={execution_id})，自动执行中...',
        )
        threading.Thread(
            target=_watch_execution,
            args=(ci_task.id, release.id, execution_id, request.user),
            daemon=True,
        ).start()
    except Exception as e:
        logger.error(f'提交 CI 构建失败: {e}')
        ci_task.status = 'failed'
        ci_task.message = f'提交构建失败: {e}'
        ci_task.finished_at = datetime.datetime.now()
        ci_task.save(update_fields=['status', 'finished_at', 'message'])

    _create_audit_log(request.user, 'deploy', 'release', release.id,
                      {'release_no': release.release_no, 'action': 'execute'})

    return Response({'code': 200, 'data': ReleaseSerializer(release).data})


# ─── 2. 发布单详情 ─────────────────────────────────────────


@api_view(['GET', 'PUT', 'DELETE'])
def release_detail(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({'code': 200, 'data': ReleaseSerializer(release).data})

    if request.method == 'PUT':
        serializer = ReleaseSerializer(release, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'code': 200, 'data': ReleaseSerializer(release).data})

    # DELETE
    if release.status != 'pending':
        return Response({'code': 400, 'message': '仅待审批状态的发布单可删除'}, status=status.HTTP_400_BAD_REQUEST)
    release.delete()
    return Response({'code': 200, 'message': '已删除'})


# ─── 3. 提交审批 ────────────────────────────────────────────


@api_view(['POST'])
def submit_release(request, release_id):
    try:
        release = Release.objects.select_related('application', 'environment', 'creator').get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    if release.status != 'pending':
        return Response({'code': 400, 'message': '仅待审批状态的发布单可提交审批'}, status=status.HTTP_400_BAD_REQUEST)

    release.status = 'approved'
    release.save(update_fields=['status'])

    # 创建审批记录
    Approval.objects.create(
        approval_type='release',
        release=release,
        approver=request.user,
        action='approved',
    )

    # 创建部署历史
    DeployHistory.objects.create(
        release=release,
        application=release.application,
        environment=release.environment,
        version=release.version,
        image_tag=release.image_tag,
        action='deploy',
        strategy=release.deploy_strategy,
        canary_percent=release.canary_percent,
        created_by=request.user,
    )

    # 审计日志
    _create_audit_log(request.user, 'approve', 'release', release.id,
                      {'release_no': release.release_no, 'status': 'approved'})

    return Response({'code': 200, 'data': ReleaseSerializer(release).data})


# ─── 4. 取消发布单 ──────────────────────────────────────────


@api_view(['POST'])
def cancel_release(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    if release.status != 'pending':
        return Response({'code': 400, 'message': '仅待审批状态的发布单可取消'}, status=status.HTTP_400_BAD_REQUEST)

    release.status = 'cancelled'
    release.save(update_fields=['status'])

    _create_audit_log(request.user, 'update', 'release', release.id,
                      {'release_no': release.release_no, 'status': 'cancelled'})

    return Response({'code': 200, 'data': ReleaseSerializer(release).data})


# ─── 5. 回滚发布单 ──────────────────────────────────────────


@api_view(['POST'])
def rollback_release(request, release_id):
    try:
        release = Release.objects.select_related('application', 'environment', 'creator').get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    if release.status != 'completed':
        return Response({'code': 400, 'message': '仅已完成状态的发布单可回滚'}, status=status.HTTP_400_BAD_REQUEST)

    release.status = 'rolled_back'
    release.save(update_fields=['status'])

    # 创建部署历史（回滚动作）
    dh = DeployHistory.objects.create(
        release=release,
        application=release.application,
        environment=release.environment,
        version=release.version,
        image_tag=release.image_tag,
        action='rollback',
        strategy=release.deploy_strategy,
        canary_percent=release.canary_percent,
        created_by=request.user,
    )

    # 创建回滚记录
    RollbackRecord.objects.create(
        release=release,
        deploy_history=dh,
        from_version=release.version,
        to_version=release.version,
        reason=request.data.get('reason', ''),
        operator=request.user,
    )

    _create_audit_log(request.user, 'rollback', 'release', release.id,
                      {'release_no': release.release_no, 'status': 'rolled_back'})

    return Response({'code': 200, 'data': ReleaseSerializer(release).data})


# ─── 6. 发布阶段任务列表 ────────────────────────────────────


@api_view(['GET'])
def release_tasks(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    tasks = release.tasks.select_related('operator').all()
    serializer = ReleaseTaskSerializer(tasks, many=True)
    return Response({'code': 200, 'data': serializer.data})


# ─── 6.1 任务日志 ────────────────────────────────────────


@api_view(['GET'])
def task_logs(request, release_id, task_id):
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    try:
        task = ReleaseTask.objects.get(id=task_id, release=release)
    except ReleaseTask.DoesNotExist:
        return Response({'code': 404, 'message': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)

    logs = task.logs.all()
    return Response({'code': 200, 'data': TaskLogSerializer(logs, many=True).data})


# ─── 7. 执行任务（Per-Environment：重试失败的 CI 或 CD）────────────


@api_view(['POST'])
def execute_task(request, release_id, task_id):
    """手动重新执行失败的 CI 或 CD 阶段"""
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    try:
        task = ReleaseTask.objects.get(id=task_id, release=release)
    except ReleaseTask.DoesNotExist:
        return Response({'code': 404, 'message': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)

    if task.status not in ('pending', 'failed'):
        return Response({'code': 400, 'message': '当前状态不可执行'}, status=status.HTTP_400_BAD_REQUEST)

    task.status = 'running'
    task.started_at = datetime.datetime.now()
    task.operator = request.user
    task.message = ''
    task.save(update_fields=['status', 'started_at', 'operator', 'message'])
    TaskLog.objects.create(task=task, level='info', message='手动重新执行')

    app = release.application
    env_config = release.env_config

    if task.stage == 'ci':
        language = app.language if hasattr(app, 'language') else 'python'
        params = {
            'name': app.code, 'version': release.version,
            'branch': release.branch or 'main', 'commit_id': release.commit_id or 'abc1234',
            'language': language,
            'repo_url': app.repo_url or f'https://gitlab.internal/spug/{app.code}.git',
            'builder_image': getattr(app, 'builder_image', '') or '',
            'base_image': getattr(app, 'base_image', '') or '',
            'release_no': release.release_no, 'stage': 'ci',
        }
        op = 'build'
    elif task.stage == 'cd':
        ns = env_config.namespace.name if env_config.namespace else "release-demo"
        is_first = not DeployHistory.objects.filter(
            application=app, environment=release.environment, action='deploy', status='success'
        ).exists()
        # 按部署策略分发 CD 操作
        strategy = release.deploy_strategy or 'rolling'
        op = 'blue_green' if strategy == 'blue_green' else ('canary' if strategy == 'canary' else 'deploy')
        params = {
            'namespace': ns, 'name': app.code,
            'image': f"123456789.dkr.ecr.us-east-1.amazonaws.com/{app.code}:{release.version}",
            'replicas': env_config.replicas,
            'env_code': release.environment.code if hasattr(release.environment, 'code') else 'dev',
            'version': release.version, 'release_no': release.release_no,
            'stage': 'cd', 'is_first_deploy': is_first,
            'deploy_type': release.deploy_mode or 'k8s',
            'canary_replicas': 1,
        }
    else:
        return Response({'code': 400, 'message': f'未知阶段: {task.stage}'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        execution = executor_client.submit(op, params)
        execution_id = execution['execution_id']
        task.message = f'重新执行 (execution_id={execution_id})'
        task.save(update_fields=['message'])
        TaskLog.objects.create(task=task, level='info', message=task.message)
        threading.Thread(
            target=_watch_execution,
            args=(task.id, release.id, execution_id, request.user),
            daemon=True,
        ).start()
    except Exception as e:
        task.status = 'failed'
        task.message = f'提交失败: {e}'
        task.finished_at = datetime.datetime.now()
        task.save(update_fields=['status', 'finished_at', 'message'])

    return Response({'code': 200, 'data': ReleaseTaskSerializer(task).data})


# ─── 8. 重试任务 ────────────────────────────────────────────


@api_view(['POST'])
def retry_task(request, release_id, task_id):
    """重置失败任务为 pending，然后重新执行"""
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    try:
        task = ReleaseTask.objects.get(id=task_id, release=release)
    except ReleaseTask.DoesNotExist:
        return Response({'code': 404, 'message': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)

    if task.status != 'failed':
        return Response({'code': 400, 'message': '仅失败状态的任务可重试'}, status=status.HTTP_400_BAD_REQUEST)

    # 重置后直接调用 execute_task 逻辑
    task.status = 'pending'
    task.retry_count += 1
    task.started_at = None
    task.finished_at = None
    task.message = ''
    task.save(update_fields=['status', 'retry_count', 'started_at', 'finished_at', 'message'])
    TaskLog.objects.create(task=task, level='info', message='任务已重置，重新执行')

    # 直接走 execute_task 逻辑
    return execute_task(request, release_id, task_id)


# ─── 9. CI/CD 日志端点 ───────────────────────────────────────


@api_view(['GET'])
def release_ci_logs(request, release_id):
    """CI 阶段日志"""
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)
    try:
        task = release.tasks.get(stage='ci')
    except ReleaseTask.DoesNotExist:
        return Response({'code': 200, 'data': []})
    logs = task.logs.all()
    return Response({'code': 200, 'data': TaskLogSerializer(logs, many=True).data})


@api_view(['GET'])
def release_cd_logs(request, release_id):
    """CD 阶段日志"""
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)
    try:
        task = release.tasks.get(stage='cd')
    except ReleaseTask.DoesNotExist:
        return Response({'code': 200, 'data': []})
    logs = task.logs.all()
    return Response({'code': 200, 'data': TaskLogSerializer(logs, many=True).data})


# ─── 10. 流水线状态 ──────────────────────────────────────────


@api_view(['GET'])
def release_pipeline(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    tasks = release.tasks.all().order_by('id')
    stage_status_map = {t.stage: t.status for t in tasks}

    pipeline = []
    for stage_key, stage_label in ReleaseTask.STAGES:
        pipeline.append({
            'stage': stage_key,
            'stage_display': stage_label,
            'status': stage_status_map.get(stage_key, 'pending'),
        })

    return Response({'code': 200, 'data': {
        'release_id': release.id,
        'release_no': release.release_no,
        'status': release.status,
        'current_stage': release.current_stage,
        'pipeline': pipeline,
    }})


# ─── 11. 发布验证 ────────────────────────────────────────────


@api_view(['GET'])
def release_verifications(request, release_id):
    """发布单的验证记录列表（最新在前）"""
    try:
        release = Release.objects.get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    records = release.verifications.select_related('created_by').all()
    return Response({'code': 200, 'data': ReleaseVerificationSerializer(records, many=True).data})


@api_view(['POST'])
def trigger_verification(request, release_id):
    """手动触发发布验证（创建 running 记录 → 提交 executor → 后台回写结果）"""
    try:
        release = Release.objects.select_related(
            'application', 'environment', 'env_config'
        ).get(id=release_id)
    except Release.DoesNotExist:
        return Response({'code': 404, 'message': '发布单不存在'}, status=status.HTTP_404_NOT_FOUND)

    _trigger_verification(release, request.user)
    _create_audit_log(request.user, 'verify', 'release', release.id,
                      {'release_no': release.release_no, 'action': 'manual_verify'})

    record = release.verifications.first()
    return Response({'code': 200, 'data': ReleaseVerificationSerializer(record).data})