from django.urls import path
from . import views

urlpatterns = [
    path("regions/", views.RegionConfigView.as_view(), name="config-regions"),
    path("accounts/", views.AccountListView.as_view(), name="config-accounts"),
]
