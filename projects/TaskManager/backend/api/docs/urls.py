from django.urls import path
from . import views

urlpatterns = [
    path("", views.DocListView.as_view(), name="doc-list"),
    path("<path:filename>", views.DocDetailView.as_view(), name="doc-detail"),
]
