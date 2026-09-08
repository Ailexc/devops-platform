from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TicketTypeViewSet, TicketViewSet, CommentViewSet, NotificationViewSet

router = DefaultRouter()
router.register('ticket-types', TicketTypeViewSet, basename='ticket-type')
router.register('tickets', TicketViewSet, basename='ticket')
router.register('comments', CommentViewSet, basename='comment')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
