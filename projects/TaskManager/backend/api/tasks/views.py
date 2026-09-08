import os

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


@extend_schema(
    summary="任务树",
    description="配置层+能力层+调度层+锁状态 四源合并的任务树",
    responses={200: OpenApiTypes.OBJECT},
)
class TaskTreeView(APIView):
    """GET /api/v1/tasks/tree — 三源合并任务树（配置层+能力层+调度层）。"""

    def get(self, request):
        from core.task_tree_service import build_task_tree
        return Response(build_task_tree())


@extend_schema(
    summary="下发同步任务",
    description="下发区域/资源组/资源/关系级同步任务；资源集合冲突返回 409",
    request=inline_serializer(
        "TaskExecuteRequest",
        fields={
            "account": serializers.CharField(),
            "region": serializers.CharField(),
            "scope": serializers.CharField(required=False),
            "target": serializers.CharField(required=False),
            "mode": serializers.CharField(required=False),
            "resource_ids": serializers.ListField(child=serializers.CharField(), required=False),
        },
    ),
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT},
)
class TaskExecuteView(APIView):
    """POST /api/v1/tasks/execute — 下发同步任务（区域/资源组/资源/关系）。

    Body: {"account", "region", "scope", "target", "mode", "resource_ids"}
      scope: region | group | resource | relation
      target: 资源组名 / 资源类型 / "源:目标" 关系
    重复下发（资源集合有交集）→ 409。
    """

    def post(self, request):
        from core.config_service import get_account_region
        from core.execution_service import TaskConflictError, dispatch_execution

        account = request.data.get("account")
        region = request.data.get("region")
        mode = request.data.get("mode", "full")  # full | incremental | targeted
        scope = request.data.get("scope", "region")
        target = request.data.get("target", "")
        resource_ids = request.data.get("resource_ids", [])

        if not account or not region:
            return Response({"error": "account and region are required"}, status=status.HTTP_400_BAD_REQUEST)
        if not get_account_region(account, region):
            return Response(
                {"error": f"账号/区域未配置: {account}/{region}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if scope == "resource" and resource_ids:
            mode = "targeted"

        try:
            outcome = dispatch_execution(account, region, scope, target, mode, trigger="人工", resource_ids=resource_ids)
            return Response({
                "execution_id": outcome["record"].id,
                "task_id": outcome["record"].id,
                "status": "dispatched",
                "celery_task_id": outcome["record"].celery_task_id,
            })
        except TaskConflictError as e:
            return Response({"error": str(e), "conflict": e.conflict}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="设置/取消 cron",
    description="写调度层 PeriodicTask；cron 为空/None 表示取消",
    request=inline_serializer(
        "TaskScheduleRequest",
        fields={
            "name": serializers.CharField(),
            "cron": serializers.CharField(required=False),
        },
    ),
    responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
class TaskScheduleView(APIView):
    """PUT /api/v1/tasks/schedule/ — 设置/取消 cron（写调度层 PeriodicTask）。

    Body: {"name": "生产环境-ap-northeast-1-计算-EC2", "cron": "0 2 * * *"}
      cron 为空/None → 取消（enabled=False, crontab=None）
    """

    def put(self, request):
        from django_celery_beat.models import PeriodicTask
        from core.schedule_manager import clear_cron, get_task_status, set_cron

        name = request.data.get("name")
        cron = (request.data.get("cron") or "").strip()

        if not name:
            return Response({"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if cron:
                result = set_cron(name, cron)
            else:
                result = clear_cron(name)
            return Response({"status": "updated", "name": name, **result})
        except PeriodicTask.DoesNotExist:
            return Response({"error": f"调度任务不存在: {name}"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="并发锁状态",
    description="当前执行中的多级并发锁列表",
    responses={200: OpenApiTypes.OBJECT},
)
class LockStatusView(APIView):
    """GET /api/v1/tasks/locks/ — 当前执行中的并发锁。"""

    def get(self, request):
        from core.concurrency_lock import lock_manager
        return Response({"locks": lock_manager.list_active()})


@extend_schema(
    summary="预览 Diff",
    description="预览将要执行的增删改（当前为 stub）",
    request=None,
    responses={200: OpenApiTypes.OBJECT},
)
class TaskPreviewView(APIView):
    """POST /api/v1/tasks/preview — preview diff before executing."""

    def post(self, request):
        # Stub — will run the diff pipeline without writing in later phases
        return Response({
            "preview": {
                "adds": [
                    {"id": "i-0new1", "reason": "AWS有CMDB无"},
                ],
                "updates": [
                    {"id": "i-0a1b2c3d", "reason": "running→stopped"},
                ],
                "deletes": [
                    {"id": "i-deleted1", "reason": "CMDB有AWS无"},
                ],
            }
        })


ALLOWED_PREVIEW_PREFIX = "/tmp/cmdb_test"


@extend_schema(
    summary="预览测试文件",
    description="预览 /tmp/cmdb_test 下的测试产物文件",
    responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
class TestFilePreviewView(APIView):
    """GET /api/v1/tasks/test/file/?path=xxx — preview file content."""

    def get(self, request):
        file_path = request.query_params.get("path", "")
        if not file_path or not os.path.isfile(file_path):
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        if not os.path.abspath(file_path).startswith(ALLOWED_PREVIEW_PREFIX):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            ext = os.path.splitext(file_path)[1].lower()
            mime = {".json": "application/json", ".md": "text/markdown"}.get(ext, "text/plain")
            return Response({"content": content, "mime": mime, "path": file_path})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="运行测试任务",
    description="下发一个测试 Celery 任务（network_collect / data_quality_check / openlibrary_collect）",
    request=inline_serializer(
        "TestTaskRunRequest",
        fields={"task": serializers.CharField()},
    ),
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
)
class TestTaskRunView(APIView):
    """POST /api/v1/tasks/test/run — dispatch a test Celery task.

    Body: {"task": "network_collect" | "data_quality_check"}
    """

    TASK_META = {
        "network_collect": {
            "module": "测试",
            "task": "网络采集模拟",
            "target": "jsonplaceholder API",
            "description": "采集 {count} 条用户数据，写入 {file}",
        },
        "data_quality_check": {
            "module": "测试",
            "task": "本地数据质检",
            "target": "CMDB 演示数据",
            "description": "检查 {accounts} 账号 · {regions} 区域 · {resources} 资源类型",
        },
        "openlibrary_collect": {
            "module": "测试",
            "task": "Open Library 图书采集分析",
            "target": "Open Library Search API",
            "description": "采集 5 个主题共 {total_unique} 本图书，分析年代分布、作者排行等",
        },
    }

    def post(self, request):
        from datetime import datetime
        task_key = request.data.get("task")
        if task_key not in self.TASK_META:
            return Response(
                {"error": f"Unknown task: {task_key}. Available: {list(self.TASK_META.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            meta = self.TASK_META[task_key]
            import importlib
            task_path = f"api.tasks.task_defs.{task_key}"
            module_path, task_name = task_path.rsplit(".", 1)
            mod = importlib.import_module(module_path)
            task_fn = getattr(mod, task_name)
            result = task_fn.delay()

            # 写入数据库
            from datetime import datetime
            from api.history.models import ExecutionRecord
            record = ExecutionRecord.objects.create(
                task_name=meta["task"],
                module=meta["module"],
                target=meta["target"],
                trigger="测试",
                scope="test",
                status="running",
                celery_task_id=result.id,
                detail=f"任务 {result.id[:8]} 执行中",
            )

            # 生命周期事件：created + dispatched
            from core.lifecycle_tracker import LifecycleTracker
            tracker = LifecycleTracker(result.id)
            tracker.append("created", "任务创建", f"task: {task_key}, trigger: 测试")
            tracker.append("dispatched", "任务派发", f"celery_task_id: {result.id[:12]}")

            return Response({
                "task_id": result.id,
                "task": task_key,
                "status": "dispatched",
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="测试任务状态",
    description="轮询测试任务执行结果（pending/running/completed/failed）",
    responses={200: OpenApiTypes.OBJECT},
)
class TestTaskStatusView(APIView):
    """GET /api/v1/tasks/test/status/<task_id> — poll Celery task result."""

    TASK_DISPLAY = {
        "network_collect": {"module": "测试", "task": "网络采集模拟", "target": "jsonplaceholder API"},
        "data_quality_check": {"module": "测试", "task": "本地数据质检", "target": "CMDB 演示数据"},
        "openlibrary_collect": {"module": "测试", "task": "Open Library 图书采集分析", "target": "Open Library Search API"},
    }

    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)

        if result.state == "PENDING":
            return Response({"task_id": task_id, "status": "pending"})
        elif result.state == "STARTED":
            return Response({"task_id": task_id, "status": "running"})
        elif result.state == "SUCCESS":
            # Check actual result status, not just Celery state
            result_data = result.result if isinstance(result.result, dict) else {}
            actual_status = result_data.get("status", "success")
            # Map to frontend-expected values
            if actual_status == "failed":
                frontend_status = "failed"
                db_status = "failed"
            else:
                frontend_status = "completed"
                db_status = "success"
            self._update_history(task_id, result_data, db_status)
            resp = {"task_id": task_id, "status": frontend_status, "result": result_data}
            if actual_status == "failed":
                resp["error"] = result_data.get("summary", result_data.get("error", "任务执行失败"))
            return Response(resp)
        elif result.state == "FAILURE":
            self._update_history(task_id, {"error": str(result.info)}, "failed")
            return Response({"task_id": task_id, "status": "failed", "error": str(result.info)})
        else:
            return Response({"task_id": task_id, "status": result.state})

    def _update_history(self, task_id, result_data, status):
        """Update the history record for this task."""
        from datetime import datetime
        from api.history.models import ExecutionRecord

        try:
            record = ExecutionRecord.objects.get(celery_task_id=task_id)
        except ExecutionRecord.DoesNotExist:
            return

        record.status = status
        record.duration = result_data.get("duration", "-") if isinstance(result_data, dict) else "-"
        record.detail = result_data.get("summary", "") if isinstance(result_data, dict) else ""
        record.result = result_data if isinstance(result_data, dict) else None
        record.finished_at = datetime.now()
        if status == "failed":
            record.error = result_data.get("error", "未知错误") if isinstance(result_data, dict) else str(result_data)
        record.save()
