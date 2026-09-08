from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import ExecutionRecord
from .serializers import (
    ExecutionRecordDetailSerializer,
    ExecutionRecordListSerializer,
)


@extend_schema(
    summary="执行历史列表",
    description="任务级执行记录分页列表（module/status/scope/trigger 过滤）",
    responses={200: OpenApiTypes.OBJECT},
)
class HistoryListView(APIView):
    """GET /api/v1/history — 执行历史列表（轻量摘要，仅任务级记录）。

    过滤: module / status / scope / trigger；默认隐藏进程级子记录。
    """

    def get(self, request):
        qs = ExecutionRecord.objects.filter(parent__isnull=True)

        module = request.query_params.get("module")
        if module:
            qs = qs.filter(module=module)

        status_ = request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)

        scope = request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)

        trigger = request.query_params.get("trigger")
        if trigger:
            qs = qs.filter(trigger=trigger)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        total = qs.count()
        records = qs[(page - 1) * page_size : page * page_size]

        return Response({
            "records": ExecutionRecordListSerializer(records, many=True).data,
            "total": total,
            "page": page,
            "page_size": page_size,
        })


@extend_schema(
    summary="执行历史详情",
    description="完整记录 + 进程列表（子记录）",
    responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
class HistoryDetailView(APIView):
    """GET /api/v1/history/<id>/ — 详情页：完整记录 + 进程列表（子记录）。

    前端只看有没有子记录决定是否显示进程块，不判断 scope。
    """

    def get(self, request, record_id):
        try:
            record = ExecutionRecord.objects.get(pk=record_id)
        except ExecutionRecord.DoesNotExist:
            return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ExecutionRecordDetailSerializer(record).data)


@extend_schema(
    summary="一键重试",
    description="按父记录 params 重新派发；冲突返回 409（无请求体）",
    request=None,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT},
)
class HistoryRetryView(APIView):
    """POST /api/v1/history/<id>/retry/ — 一键重试（任务级或进程级）。

    - 任务级记录：按父记录 params 原参数重新派发
    - 进程级记录：从父记录 params + 子进程 result.details 推断 scope/target 重发
    """

    def post(self, request, record_id):
        from core.execution_service import TaskConflictError, dispatch_execution

        try:
            record = ExecutionRecord.objects.get(pk=record_id)
        except ExecutionRecord.DoesNotExist:
            return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)

        parent = record if record.parent_id is None else record.parent
        params = parent.params or {}
        if not params.get("account") or not params.get("region"):
            return Response(
                {"error": "该记录没有派发参数，无法重试"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = params["account"]
        region = params["region"]
        mode = params.get("mode", "full")
        resource_ids = params.get("resource_ids") or []

        if record.parent_id is None:
            # 任务级：按原参数重发
            scope = record.scope
            target = params.get("target", "")
        else:
            # 进程级：从子进程结果推断 scope/target
            details = (record.result or {}).get("details") or {}
            if "source" in details and "target" in details:
                scope, target = "relation", f"{details['source']}:{details['target']}"
            elif details.get("resource"):
                scope, target = "resource", details["resource"]
            else:
                return Response(
                    {"error": "无法从该进程推断重试参数"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            outcome = dispatch_execution(
                account, region, scope, target, mode,
                trigger="人工", resource_ids=resource_ids,
            )
            return Response({
                "execution_id": outcome["record"].id,
                "status": "dispatched",
            })
        except TaskConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
