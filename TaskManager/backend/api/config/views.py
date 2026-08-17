from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


@extend_schema(
    summary="区域同步配置",
    description="GET 查询 / PUT 更新区域配置（cron/concurrency/enabled），并同步调度层",
    request=inline_serializer(
        "RegionConfigRequest",
        fields={
            "account": serializers.CharField(),
            "region": serializers.CharField(),
            "cron": serializers.CharField(required=False),
            "concurrency": serializers.IntegerField(required=False),
        },
    ),
    responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
class RegionConfigView(APIView):
    """GET/PUT /api/v1/config/regions — 区域级同步配置（配置层 + 调度层）。"""

    def get(self, request):
        from core.config_service import list_account_regions
        regions = []
        for acct in list_account_regions():
            for reg in acct["regions"]:
                regions.append({
                    "account": acct["name"],
                    "region": reg["code"],
                    "cron": reg["cron"],
                    "concurrency": reg["concurrency"],
                    "enabled": reg["enabled"],
                    "source": reg["source"],
                })
        return Response({"regions": regions})

    def put(self, request):
        """更新区域配置（cron/concurrency/enabled），并同步调度层 PeriodicTask。"""
        from core.config_service import get_account_region
        from core.schedule_manager import REGION_TASK_TYPE, clear_cron, set_cron

        account = request.data.get("account")
        region = request.data.get("region")
        cron = request.data.get("cron")
        concurrency = request.data.get("concurrency")

        row = get_account_region(account, region) if (account and region) else None
        if not row:
            return Response({"error": f"账号/区域未配置: {account}/{region}"}, status=status.HTTP_404_NOT_FOUND)

        if cron is not None:
            row.cron = cron
        if concurrency is not None:
            row.concurrency = int(concurrency)
        row.save()

        # 同步调度层：区域级 PeriodicTask 的 cron
        name = f"{account}-{region}-_region-{REGION_TASK_TYPE}"
        try:
            if cron:
                set_cron(name, cron)
            else:
                clear_cron(name)
        except Exception:
            pass  # 调度任务尚未预建时忽略

        return Response({"status": "updated", "account": account, "region": region})


@extend_schema(
    summary="账号列表",
    description="配置层账号列表及区域数量",
    responses={200: OpenApiTypes.OBJECT},
)
class AccountListView(APIView):
    """GET /api/v1/config/accounts — 账号列表（配置层）。"""

    def get(self, request):
        from core.config_service import list_account_regions
        accounts = [
            {
                "name": acct["name"],
                "account_id": acct["account_id"],
                "region_count": len(acct["regions"]),
            }
            for acct in list_account_regions()
        ]
        return Response({"accounts": accounts})
