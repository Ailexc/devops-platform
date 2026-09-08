from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import graph_views, sync_views

router = DefaultRouter()
router.register('accounts', views.CloudAccountViewSet)
router.register('resources', views.ResourceViewSet)
router.register('relations', views.ResourceRelationViewSet)
router.register('changes', views.ResourceChangeViewSet)
router.register('applications', views.ApplicationViewSet)
router.register('environments', views.EnvironmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('topology/', views.resource_topology, name='resource-topology'),
    path('graph/applications/', graph_views.applications, name='graph-applications'),
    path('graph/organization/', graph_views.organization, name='graph-organization'),
    path('graph/applications/<int:app_id>/', graph_views.application_detail, name='graph-application-detail'),
    path('graph/environments/<int:env_id>/', graph_views.environment_detail, name='graph-environment-detail'),
    path('graph/resources/<int:resource_id>/neighbors/', graph_views.resource_neighbors, name='graph-resource-neighbors'),
    path('graph/resources/<int:resource_id>/impact/', graph_views.resource_impact, name='graph-resource-impact'),
    path('graph/resources/<int:source_id>/path/', graph_views.resource_path, name='graph-resource-path'),
    path('graph/resources/<int:source_id>/connectivity/', graph_views.resource_connectivity, name='graph-resource-connectivity'),
    path('graph/relation-changes/', graph_views.relation_changes, name='graph-relation-changes'),
    path('graph/pending-changes/', graph_views.pending_changes, name='graph-pending-changes'),
    path('sync-jobs/', sync_views.sync_jobs, name='sync-jobs'),
    path('events/', sync_views.sync_events, name='sync-events'),
]
