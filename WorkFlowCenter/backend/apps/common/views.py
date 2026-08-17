from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIConfig
from .serializers import (
    AIConfigSerializer,
    GenerateFormSerializer,
    TestConnectionSerializer,
)
from .services.ai_service import generate_form, AIServiceError


class AIConfigViewSet(viewsets.ModelViewSet):
    """AI 配置视图集"""
    queryset = AIConfig.objects.all()
    serializer_class = AIConfigSerializer

    @action(detail=False, methods=['post'], url_path='generate-form')
    def generate_form(self, request):
        """AI 生成表单"""
        serializer = GenerateFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        config_id = data.get('config_id')
        provider = data.get('provider')

        config = None
        if config_id:
            config = AIConfig.objects.filter(pk=config_id).first()
        if config is None and provider:
            config = AIConfig.objects.filter(
                provider=provider, is_active=True,
            ).first()
        if config is None:
            config = AIConfig.get_default()

        try:
            result = generate_form(config, data['prompt'])
        except AIServiceError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'provider': config.provider,
            'model_id': config.effective_model_id(),
            **result,
        })

    @action(detail=False, methods=['post'], url_path='test')
    def test_connection(self, request):
        """测试 AI 连接（发送一个最小请求）"""
        serializer = TestConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        config_id = data.get('config_id')
        provider = data.get('provider')

        config = None
        if config_id:
            config = AIConfig.objects.filter(pk=config_id).first()
        if config is None and provider:
            config = AIConfig.objects.filter(
                provider=provider, is_active=True,
            ).first()
        if config is None:
            config = AIConfig.get_default()

        try:
            result = generate_form(config, '生成一个简单的反馈意见表单，包含意见内容和联系方式')
        except AIServiceError as e:
            return Response(
                {'detail': f'连接失败: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'detail': '连接成功',
            'provider': config.provider,
            'model_id': config.effective_model_id(),
            'form_schema': result.get('form_schema'),
        })

    @action(detail=False, methods=['post'], url_path='generate-flow')
    def generate_flow(self, request):
        """AI 生成流程"""
        from .serializers import GenerateFlowSerializer
        from .services.ai_service import generate_flow as generate_flow_service

        serializer = GenerateFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        config_id = data.get('config_id')
        provider = data.get('provider')

        config = None
        if config_id:
            config = AIConfig.objects.filter(pk=config_id).first()
        if config is None and provider:
            config = AIConfig.objects.filter(
                provider=provider, is_active=True,
            ).first()
        if config is None:
            config = AIConfig.get_default()

        try:
            result = generate_flow_service(
                config, 
                data['prompt'],
                current_form=data.get('current_form')
            )
        except AIServiceError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'provider': config.provider,
            'model_id': config.effective_model_id(),
            **result,
        })


    @action(detail=False, methods=['post'], url_path='generate-form-stream')
    def generate_form_stream(self, request):
        """AI 流式生成表单"""
        from django.http import StreamingHttpResponse
        from .serializers import GenerateFormSerializer
        from .services.ai_service import stream_generate_form, AIServiceError

        serializer = GenerateFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        config_id = data.get('config_id')
        provider = data.get('provider')

        config = None
        if config_id:
            config = AIConfig.objects.filter(pk=config_id).first()
        if config is None and provider:
            config = AIConfig.objects.filter(
                provider=provider, is_active=True,
            ).first()
        if config is None:
            config = AIConfig.get_default()

        def event_stream():
            try:
                for chunk in stream_generate_form(config, data['prompt']):
                    yield f"data: {chunk}\n\n"
            except AIServiceError as e:
                yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    @action(detail=False, methods=['post'], url_path='generate-flow-stream')
    def generate_flow_stream(self, request):
        """AI 流式生成流程"""
        from django.http import StreamingHttpResponse
        from .serializers import GenerateFlowSerializer
        from .services.ai_service import stream_generate_flow, AIServiceError

        serializer = GenerateFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        config_id = data.get('config_id')
        provider = data.get('provider')

        config = None
        if config_id:
            config = AIConfig.objects.filter(pk=config_id).first()
        if config is None and provider:
            config = AIConfig.objects.filter(
                provider=provider, is_active=True,
            ).first()
        if config is None:
            config = AIConfig.get_default()

        def event_stream():
            try:
                for chunk in stream_generate_flow(
                    config, 
                    data['prompt'],
                    current_form=data.get('current_form')
                ):
                    yield f"data: {chunk}\n\n"
            except AIServiceError as e:
                yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
