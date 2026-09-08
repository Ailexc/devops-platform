from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('orders', views.TicketOrderViewSet)
router.register('approvals', views.TicketApprovalViewSet)
router.register('tasks', views.TicketTaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
