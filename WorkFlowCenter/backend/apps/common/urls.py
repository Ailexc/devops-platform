from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AIConfigViewSet

router = DefaultRouter()
router.register('ai/config', AIConfigViewSet, basename='ai-config')

urlpatterns = [
    path('', include(router.urls)),
]
