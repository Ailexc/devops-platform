from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('bills', views.CostBillViewSet)
router.register('items', views.CostItemViewSet)
router.register('budgets', views.BudgetViewSet)
router.register('suggestions', views.OptimizationSuggestionViewSet)
router.register('rules', views.OptimizationRuleViewSet)
router.register('reports', views.OptimizationReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('overview/summary/', views.OverviewView.as_view()),
    path('application-cost/', views.ApplicationCostView.as_view()),
]
