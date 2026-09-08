from django.urls import path
from . import views

urlpatterns = [
    path('infra/environments/', views.environment_list, name='environment-list'),
    path('infra/clusters/', views.cluster_list, name='cluster-list'),
    path('infra/clusters/', views.cluster_create, name='cluster-create'),
    path('infra/namespaces/', views.namespace_list, name='namespace-list'),
]