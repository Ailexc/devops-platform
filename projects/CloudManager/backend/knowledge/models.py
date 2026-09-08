from django.db import models


class DocCategory(models.Model):
    """系统文档分类（目录）"""
    code = models.CharField('分类编码', max_length=32, unique=True)
    name = models.CharField('分类名称', max_length=64)
    icon = models.CharField('图标', max_length=16, blank=True, default='📄')
    sort = models.IntegerField('排序', default=0)

    class Meta:
        db_table = 'knowledge_doc_category'
        verbose_name = '系统文档分类'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class DocEntry(models.Model):
    """系统文档：HTML 格式内容，前端加载并点击查看详情"""
    category = models.ForeignKey(DocCategory, on_delete=models.CASCADE,
                                 related_name='docs', verbose_name='所属分类')
    slug = models.CharField('标识', max_length=64, unique=True)
    title = models.CharField('标题', max_length=128)
    summary = models.CharField('摘要', max_length=256, blank=True, default='')
    tags = models.CharField('标签', max_length=128, blank=True, default='',
                            help_text='逗号分隔')
    html_content = models.TextField('HTML 内容')
    sort = models.IntegerField('排序', default=0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'knowledge_doc_entry'
        verbose_name = '系统文档'
        verbose_name_plural = verbose_name
        ordering = ['category', 'sort', 'id']

    def __str__(self):
        return self.title
