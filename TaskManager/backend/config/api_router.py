from django.urls import path, include

urlpatterns = [
    path("dashboard/", include("api.dashboard.urls")),
    path("tasks/", include("api.tasks.urls")),
    path("config/", include("api.config.urls")),
    path("history/", include("api.history.urls")),
    path("docs/", include("api.docs.urls")),
    path("auth/", include("api.auth.urls")),
]
