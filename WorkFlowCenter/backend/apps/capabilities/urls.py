from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CapabilityViewSet, TaskJobViewSet

router = DefaultRouter()
router.register('capabilities', CapabilityViewSet, basename='capability')
router.register('task-jobs', TaskJobViewSet, basename='task-job')

urlpatterns = [
    path('', include(router.urls)),
]
