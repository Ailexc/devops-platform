from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Capability, TaskJob
from .serializers import CapabilitySerializer, TaskJobSerializer


class CapabilityViewSet(viewsets.ModelViewSet):
    """能力视图集"""
    queryset = Capability.objects.all()
    serializer_class = CapabilitySerializer
    filterset_fields = ['is_active', 'execute_mode']
    search_fields = ['code', 'name']

    @action(detail=True, methods=['post'], url_path='test')
    def test(self, request, pk=None):
        """测试执行能力（调试用，不落 TaskJob）"""
        from .services.executor import CapabilityExecutor, MockJobPlatformClient
        capability = self.get_object()
        input_data = request.data or {}

        # 根据 endpoint 是否配置，选择 Mock 或 HTTP 客户端
        if capability.endpoint:
            from .services.executor import HttpJobPlatformClient
            client = HttpJobPlatformClient()
        else:
            client = MockJobPlatformClient()

        executor = CapabilityExecutor(client=client)
        try:
            result = executor.client.execute(
                capability.endpoint or '',
                {**input_data, '_capability_code': capability.code},
            )
            return Response({
                'success': True,
                'output': result,
                'mode': 'http' if capability.endpoint else 'mock',
            })
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e), 'mode': 'http' if capability.endpoint else 'mock'},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class TaskJobViewSet(viewsets.ReadOnlyModelViewSet):
    """任务执行视图集"""
    queryset = TaskJob.objects.select_related('capability', 'instance', 'task').all()
    serializer_class = TaskJobSerializer
    filterset_fields = ['status', 'capability', 'instance']

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_job(self, request, pk=None):
        """手动执行任务（调试用）：可传入覆盖输入数据"""
        from .services.executor import default_executor
        job = self.get_object()
        input_data = request.data or job.input_data
        output = default_executor.execute_capability(job.job_id, input_data=input_data)
        job.refresh_from_db()
        return Response(TaskJobSerializer(job).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """任务执行统计（任务中心仪表盘用）"""
        total = TaskJob.objects.count()
        succeeded = TaskJob.objects.filter(status=TaskJob.Status.SUCCEEDED).count()
        failed = TaskJob.objects.filter(status=TaskJob.Status.FAILED).count()
        running = TaskJob.objects.filter(status=TaskJob.Status.RUNNING).count()
        return Response({
            'total': total,
            'succeeded': succeeded,
            'failed': failed,
            'running': running,
        })
