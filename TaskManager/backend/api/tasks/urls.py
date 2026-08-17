from django.urls import path
from . import views

urlpatterns = [
    path("tree/", views.TaskTreeView.as_view(), name="task-tree"),
    path("execute/", views.TaskExecuteView.as_view(), name="task-execute"),
    path("schedule/", views.TaskScheduleView.as_view(), name="task-schedule"),
    path("locks/", views.LockStatusView.as_view(), name="task-locks"),
    path("preview/", views.TaskPreviewView.as_view(), name="task-preview"),
    path("test/run/", views.TestTaskRunView.as_view(), name="test-task-run"),
    path("test/status/<str:task_id>/", views.TestTaskStatusView.as_view(), name="test-task-status"),
    path("test/file/", views.TestFilePreviewView.as_view(), name="test-file-preview"),
]
