"""同步服务 API：定时同步触发 / 事件回调 / 同步任务列表"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import SyncJob
from .serializers import SyncJobSerializer
from .sync import handle_event, run_schedule_sync


@api_view(['GET', 'POST'])
def sync_jobs(request):
    """手动触发定时同步 / 查看同步任务列表"""
    if request.method == 'POST':
        job_type = request.data.get('job_type', 'manual')
        job = run_schedule_sync(job_type=job_type, source_system='collection-a')
        return Response(SyncJobSerializer(job).data)
    jobs = SyncJob.objects.all()[:20]
    return Response(SyncJobSerializer(jobs, many=True).data)


@api_view(['POST'])
def sync_events(request):
    """事件同步回调（模拟采集系统B 推送）"""
    if not request.data:
        return Response({'error': '请求体不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    job = handle_event(request.data)
    return Response(SyncJobSerializer(job).data)
