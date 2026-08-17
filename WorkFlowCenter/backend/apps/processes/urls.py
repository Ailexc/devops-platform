from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProcessDefinitionViewSet,
    ProcessInstanceViewSet,
    NodeTaskViewSet,
    TaskInstanceViewSet,
    ApprovalRecordViewSet,
    InitiatorAppViewSet,
)

router = DefaultRouter()
router.register('process-definitions', ProcessDefinitionViewSet, basename='process-definition')
router.register('process-instances', ProcessInstanceViewSet, basename='process-instance')
router.register('initiator-apps', InitiatorAppViewSet, basename='initiator-app')
router.register('node-tasks', NodeTaskViewSet, basename='node-task')
router.register('task-instances', TaskInstanceViewSet, basename='task-instance')
router.register('approval-records', ApprovalRecordViewSet, basename='approval-record')

urlpatterns = [
    path('', include(router.urls)),
]
