from rest_framework import viewsets

from .models import DocCategory, DocEntry
from .serializers import (DocCategorySerializer, DocDetailSerializer,
                          DocEntrySummarySerializer)


class DocCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """文档目录：分类 + 每类文档摘要，前端左侧目录树使用"""
    queryset = DocCategory.objects.prefetch_related('docs').all()
    serializer_class = DocCategorySerializer


class DocEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """文档条目：list 返回摘要（可分类过滤），retrieve 按 slug 返回 HTML 正文"""
    queryset = DocEntry.objects.select_related('category').all()
    lookup_field = 'slug'
    filterset_fields = ['category']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DocDetailSerializer
        return DocEntrySummarySerializer
