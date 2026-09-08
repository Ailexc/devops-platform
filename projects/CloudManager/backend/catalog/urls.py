from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.ServiceCategoryViewSet)
router.register('items', views.ServiceItemViewSet)
router.register('quotas', views.QuotaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
