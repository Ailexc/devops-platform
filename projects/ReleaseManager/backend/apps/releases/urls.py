from django.urls import path
from . import views

urlpatterns = [
    path('releases/', views.release_list, name='release-list'),
    path('releases/<int:release_id>/', views.release_detail, name='release-detail'),
    path('releases/<int:release_id>/submit-approval/', views.submit_approval, name='release-submit-approval'),
    path('releases/<int:release_id>/approve/', views.approve_action, name='release-approve'),
    path('releases/<int:release_id>/execute/', views.execute_release, name='release-execute'),
    path('releases/<int:release_id>/cancel/', views.cancel_release, name='release-cancel'),
    path('releases/<int:release_id>/rollback/', views.rollback_release, name='release-rollback'),
    path('releases/<int:release_id>/tasks/', views.release_tasks, name='release-tasks'),
    path('releases/<int:release_id>/tasks/<int:task_id>/execute/', views.execute_task, name='execute-task'),
    path('releases/<int:release_id>/tasks/<int:task_id>/logs/', views.task_logs, name='task-logs'),
    path('releases/<int:release_id>/tasks/<int:task_id>/retry/', views.retry_task, name='retry-task'),
    path('releases/<int:release_id>/ci-logs/', views.release_ci_logs, name='release-ci-logs'),
    path('releases/<int:release_id>/cd-logs/', views.release_cd_logs, name='release-cd-logs'),
    path('releases/<int:release_id>/pipeline/', views.release_pipeline, name='release-pipeline'),
    path('releases/<int:release_id>/verifications/', views.release_verifications, name='release-verifications'),
    path('releases/<int:release_id>/verify/', views.trigger_verification, name='release-verify'),
]