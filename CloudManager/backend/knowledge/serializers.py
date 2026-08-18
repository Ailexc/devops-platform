from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import DocCategory, DocEntry


class DocEntrySummarySerializer(serializers.ModelSerializer):
    """文档摘要（列表用，不含 HTML 正文）"""
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = DocEntry
        fields = ['id', 'slug', 'title', 'summary', 'tags', 'category',
                  'category_name', 'sort', 'updated_at']


class DocCategorySerializer(serializers.ModelSerializer):
    """文档目录：分类 + 该分类下文档摘要"""
    doc_count = serializers.SerializerMethodField()
    docs = DocEntrySummarySerializer(many=True, read_only=True)

    class Meta:
        model = DocCategory
        fields = ['id', 'code', 'name', 'icon', 'sort', 'doc_count', 'docs']

    def get_doc_count(self, obj):
        return obj.docs.count()


class DocDetailSerializer(DocEntrySummarySerializer):
    """文档详情：HTML 正文从 docs 目录的 {slug}.html 文件读取"""
    html_content = serializers.SerializerMethodField()

    class Meta(DocEntrySummarySerializer.Meta):
        fields = DocEntrySummarySerializer.Meta.fields + ['html_content']

    def get_html_content(self, obj):
        path = Path(settings.BASE_DIR) / 'knowledge' / 'docs' / f'{obj.slug}.html'
        if path.exists():
            return path.read_text(encoding='utf-8')
        # 兜底：文件缺失时回退到数据库字段
        return obj.html_content or ''
