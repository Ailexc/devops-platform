from django.urls import path
from . import views

urlpatterns = [
    path("", views.HistoryListView.as_view(), name="history-list"),
    path("<int:record_id>/", views.HistoryDetailView.as_view(), name="history-detail"),
    path("<int:record_id>/retry/", views.HistoryRetryView.as_view(), name="history-retry"),
]
