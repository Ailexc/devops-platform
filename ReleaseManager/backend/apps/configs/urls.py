from django.urls import path
from . import views

urlpatterns = [
    path('config-templates/', views.template_list, name='config-template-list'),
    path('config-templates/<int:template_id>/', views.template_detail, name='config-template-detail'),
    path('config-templates/<int:template_id>/render/', views.template_render, name='config-template-render'),
    path('config-variables/', views.variable_list, name='config-variable-list'),
    path('config-variables/<int:var_id>/', views.variable_detail, name='config-variable-detail'),
    path('config-variable-values/', views.variable_value_list, name='config-variable-value-list'),
    path('config-variable-values/<int:value_id>/', views.variable_value_detail, name='config-variable-value-detail'),
    path('config-variable-values/batch/', views.variable_value_batch, name='config-variable-value-batch'),
    path('config-releases/', views.release_list, name='config-release-list'),
    path('config-releases/by-release/<int:release_id>/', views.release_configs_by_release, name='config-release-by-release'),
    path('config-releases/<int:release_id>/diff/', views.release_diff, name='config-release-diff'),
]