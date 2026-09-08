from django.contrib import admin

from .models import DocCategory, DocEntry


@admin.register(DocCategory)
class DocCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'icon', 'sort')
    list_editable = ('sort',)


@admin.register(DocEntry)
class DocEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'slug', 'sort', 'updated_at')
    list_filter = ('category',)
    search_fields = ('title', 'summary')
    list_editable = ('sort',)
