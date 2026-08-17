from django.urls import path
from . import views

urlpatterns = [
    path('approvals/', views.approval_list, name='approval-list'),
    path('approvals/pending/', views.pending_approvals, name='approval-pending'),
    path('approvals/<int:approval_id>/approve/', views.approve_approval, name='approval-approve'),
    path('approvals/<int:approval_id>/reject/', views.reject_approval, name='approval-reject'),
    path('approvals/<int:approval_id>/approve-step/', views.approve_step, name='approve-step'),
    path('approvals/<int:approval_id>/reject-step/', views.reject_step, name='reject-step'),
]