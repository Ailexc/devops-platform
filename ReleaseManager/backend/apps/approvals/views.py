from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Approval
from .serializers import ApprovalSerializer
from apps.audit.models import AuditLog
from apps.authz.utils import apply_permission_request


@api_view(['GET'])
def approval_list(request):
    """审批列表"""
    qs = Approval.objects.select_related('approver', 'release', 'permission_request__user').order_by('-created_at')

    # 支持按类型筛选
    approval_type = request.query_params.get('type')
    if approval_type:
        qs = qs.filter(approval_type=approval_type)

    # 支持按权限申请子类型筛选
    request_type = request.query_params.get('request_type')
    if request_type:
        types = request_type.split(',')
        qs = qs.filter(approval_type='permission', permission_request__request_type__in=types)

    return Response({'code': 200, 'data': ApprovalSerializer(qs, many=True).data})


@api_view(['GET'])
def pending_approvals(request):
    """我的待审批列表"""
    qs = Approval.objects.filter(action='pending', approver=request.user) \
        .select_related('approver', 'release', 'permission_request__user') \
        .order_by('-created_at')

    # 支持按类型筛选
    approval_type = request.query_params.get('type')
    if approval_type:
        qs = qs.filter(approval_type=approval_type)

    # 支持按权限申请子类型筛选
    request_type = request.query_params.get('request_type')
    if request_type:
        types = request_type.split(',')
        qs = qs.filter(approval_type='permission', permission_request__request_type__in=types)

    return Response({'code': 200, 'data': ApprovalSerializer(qs, many=True).data})


@api_view(['POST'])
def approve_approval(request, approval_id):
    """审批通过"""
    approval = get_object_or_404(Approval, id=approval_id)
    action = request.data.get('action', 'approved')
    comment = request.data.get('comment', '')

    approval.action = 'approved' if action == 'approved' else 'rejected'
    approval.comment = comment
    approval.save()

    if approval.release:
        if action == 'approved':
            approval.release.status = 'approved'
            approval.release.approval_status = 'passed'
        else:
            approval.release.status = 'rejected'
            approval.release.approval_status = 'rejected'
        approval.release.save(update_fields=['status', 'approval_status'])

    AuditLog.objects.create(
        user=request.user,
        action='approve',
        resource_type='approval',
        resource_id=approval.id,
        detail={
            'approval_type': approval.approval_type,
            'release_id': approval.release_id,
            'comment': request.data.get('comment', ''),
        },
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({'code': 200, 'message': '审批通过', 'data': ApprovalSerializer(approval).data})


@api_view(['POST'])
def reject_approval(request, approval_id):
    """审批驳回"""
    approval = get_object_or_404(Approval, id=approval_id)
    approval.action = 'rejected'
    approval.comment = request.data.get('comment', '')
    approval.save()

    if approval.release:
        approval.release.status = 'rejected'
        approval.release.approval_status = 'rejected'
        approval.release.save(update_fields=['status', 'approval_status'])

    if approval.permission_request:
        approval.permission_request.status = 'rejected'
        approval.permission_request.save()

    AuditLog.objects.create(
        user=request.user,
        action='reject',
        resource_type='approval',
        resource_id=approval.id,
        detail={
            'approval_type': approval.approval_type,
            'release_id': approval.release_id,
            'comment': request.data.get('comment', ''),
        },
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({'code': 200, 'message': '审批驳回', 'data': ApprovalSerializer(approval).data})


@api_view(['POST'])
def approve_step(request, approval_id):
    """
    步骤级审批通过 - 审批当前步骤的一条记录，若该步骤全部通过则推进到下一步
    """
    approval = get_object_or_404(Approval, id=approval_id)
    approval.action = 'approved'
    approval.comment = request.data.get('comment', '')
    approval.save()

    # 检查当前步骤是否全部通过
    if approval.permission_request:
        step_pending = Approval.objects.filter(
            permission_request=approval.permission_request,
            step_order=approval.step_order,
            action='pending',
        ).exists()

        if not step_pending:
            # 当前步骤全部通过，检查是否有下一步
            next_step = approval.step_order + 1
            next_approvals = Approval.objects.filter(
                permission_request=approval.permission_request,
                step_order=next_step,
            )
            if not next_approvals.exists():
                # 所有步骤通过，权限生效
                _apply_permission(approval.permission_request)

    AuditLog.objects.create(
        user=request.user,
        action='approve',
        resource_type='approval',
        resource_id=approval.id,
        detail={
            'approval_type': approval.approval_type,
            'step_order': approval.step_order,
            'comment': request.data.get('comment', ''),
        },
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({'code': 200, 'message': '审批通过', 'data': ApprovalSerializer(approval).data})


@api_view(['POST'])
def reject_step(request, approval_id):
    """
    步骤级审批驳回 - 驳回当前步骤，整个申请被驳回
    """
    approval = get_object_or_404(Approval, id=approval_id)
    approval.action = 'rejected'
    approval.comment = request.data.get('comment', '')
    approval.save()

    if approval.permission_request:
        # 驳回整个申请
        approval.permission_request.status = 'rejected'
        approval.permission_request.save()
        # 驳回所有其他待审批记录
        Approval.objects.filter(
            permission_request=approval.permission_request,
            action='pending',
        ).update(action='rejected')

    AuditLog.objects.create(
        user=request.user,
        action='reject',
        resource_type='approval',
        resource_id=approval.id,
        detail={
            'approval_type': approval.approval_type,
            'step_order': approval.step_order,
            'comment': request.data.get('comment', ''),
        },
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({'code': 200, 'message': '审批驳回', 'data': ApprovalSerializer(approval).data})


def _apply_permission(perm_req):
    """权限申请全部审批通过后，统一调用 apply_permission_request 执行权限变更"""
    apply_permission_request(perm_req)