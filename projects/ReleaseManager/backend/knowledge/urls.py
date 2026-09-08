from django.urls import path
from . import views

urlpatterns = [
    path("knowledge/modules/", views.module_list, name="knowledge-modules"),
    path("knowledge/modules/<slug:module_id>/", views.module_detail, name="knowledge-module-detail"),
    path("knowledge/articles/<slug:module_id>/<slug:article_id>/", views.article_content, name="knowledge-article"),
    path("knowledge/interviews/<slug:module_id>/", views.interview_content, name="knowledge-interview"),
    path("knowledge/yuque-config/", views.yuque_config, name="knowledge-yuque"),
]
