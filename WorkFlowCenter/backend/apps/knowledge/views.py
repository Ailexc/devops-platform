from rest_framework import viewsets, status
from rest_framework.response import Response

from .services import list_categories, list_documents, get_document


class DocumentViewSet(viewsets.ViewSet):
    """知识库文档：文件驱动，列表(摘要) + 详情(HTML 正文，pk=key)"""

    def list(self, request):
        return Response({
            'categories': list_categories(),
            'documents': list_documents(),
        })

    def retrieve(self, request, pk=None):
        doc = get_document(pk)
        if not doc:
            return Response({'detail': '文档不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(doc)
