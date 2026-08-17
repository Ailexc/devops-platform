from django.urls import path
from . import views

urlpatterns = [
    path('artifact-repositories/', views.repository_list, name='artifact-repository-list'),
    path('artifacts/', views.artifact_list, name='artifact-list'),
    path('artifacts/<int:artifact_id>/', views.artifact_detail, name='artifact-detail'),
    path('artifacts/by-app/<int:app_id>/', views.artifacts_by_app, name='artifacts-by-app'),
    path('artifacts/<int:artifact_id>/promotions/', views.artifact_promotions, name='artifact-promotions'),
    path('artifacts/<int:artifact_id>/promote/', views.promote_artifact, name='promote-artifact'),
]