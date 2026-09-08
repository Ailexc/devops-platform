from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('categories', views.DocCategoryViewSet)
router.register('docs', views.DocEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
