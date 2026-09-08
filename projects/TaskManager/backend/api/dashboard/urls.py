from django.urls import path
from . import views

urlpatterns = [
    path("stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
    path("workers/", views.WorkerStatusView.as_view(), name="dashboard-workers"),
    path("resource-health/", views.ResourceHealthView.as_view(), name="dashboard-resource-health"),
    path("task-trend/", views.TaskTrendView.as_view(), name="dashboard-task-trend"),
    path("health-ranking/", views.HealthRankingView.as_view(), name="dashboard-health-ranking"),
    path("current/", views.CurrentRunningView.as_view(), name="dashboard-current"),
    path("recent-events/", views.RecentEventsView.as_view(), name="dashboard-recent-events"),
    path("resource-breakdown/", views.ResourceBreakdownView.as_view(), name="dashboard-resource-breakdown"),
    path("aws-resources/", views.AWSResourcesView.as_view(), name="dashboard-aws-resources"),
]
