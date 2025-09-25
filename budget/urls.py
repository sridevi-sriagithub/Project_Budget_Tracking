

from django.urls import path
from .views import (
    PaymentListCreateAPIView,
    MilestoneListCreateAPIView, MilestoneDetailAPIView,
    TransactionCreateAPIView, AdditionalRequestListCreateAPIView,
    AdditionalRequestApproveAPIView, NotificationListAPIView,
    RuleListCreateAPIView, EstimationCreateAPIView,AddHoldView, ReleaseHoldView,ProjectEstimationAPIView,ProjectPaymentTrackingAPIView,ProjectEstimationPaymentAPIView,ProfitLossAdvancedAPIView,
    ChangeRequestListView, ChangeRequestApproveView, ChangeRequestRejectView,ChangeRequestCreateView,ProjectEstimationChangeAPIView,InvoiceGenerateAPIView,download_invoice,AdditionalRequestRejectAPIView
)

urlpatterns = [
    path("estimations/", EstimationCreateAPIView.as_view(), name="estimation-list"),
    path("estimations/<int:pk>/", EstimationCreateAPIView.as_view(), name="estimation-detail"),
    path('project/<int:pk>/estimation/', ProjectEstimationAPIView.as_view(), name='project-estimation'),
    path('project/<int:pk>/payments/', ProjectPaymentTrackingAPIView.as_view(), name='project-payments'),
    path('project/<int:pk>/estimation/payment/', ProjectEstimationPaymentAPIView.as_view(), name='project-financial-detail'),
    path("project/<int:pk>/estimation/change/", ProjectEstimationChangeAPIView.as_view(), name="project-estimation-change"),
    path("payments/", PaymentListCreateAPIView.as_view(), name="payments-list"),
    path("payments/<int:payment_id>/", PaymentListCreateAPIView.as_view(), name="payments-detail"),

    path('projects/<int:pk>/add-hold/', AddHoldView.as_view(), name='add-hold'),
    path('holds/', AddHoldView.as_view(), name='holds-list'),
    path('holds/<int:hold_id>/release/', ReleaseHoldView.as_view(), name='release-hold'),
    path('holds/release/', ReleaseHoldView.as_view(), name='hold-detail'),

    path("milestones/", MilestoneListCreateAPIView.as_view(), name="milestones-list"),
    path("milestones/<int:pk>/", MilestoneDetailAPIView.as_view(), name="milestones-detail"),
    
    path("profit-loss-advanced/<int:pk>/", ProfitLossAdvancedAPIView.as_view(), name="profit-loss-advanced"),
    path("transactions/", TransactionCreateAPIView.as_view(), name="transactions-create"),

    path("additional-requests/", AdditionalRequestListCreateAPIView.as_view(), name="additional-list"),
    path("additional-requests/<int:req_id>/approve/", AdditionalRequestApproveAPIView.as_view(), name="additional-approve"),
    path("additional-requests/<int:req_id>/reject/", AdditionalRequestRejectAPIView.as_view(), name="additional-reject"),

    # path("projects/<int:project_id>/change-requests/", ChangeRequestListView.as_view(), name="change-request-list"),
    # path("change-requests/<int:cr_id>/approve/", ChangeRequestApproveView.as_view(), name="change-request-approve"),
    # path("change-requests/<int:cr_id>/reject/", ChangeRequestRejectView.as_view(), name="change-request-reject"),
    path("projects/<int:pk>/change-requests/", ChangeRequestListView.as_view(), name="change-request-list"),
    # urls.py
    path("projects/<int:pk>/change-requests/create/",ChangeRequestCreateView.as_view(),name="change-request-create"),


    # Approve a specific change request
    path("change-requests/<int:pk>/approve/", ChangeRequestApproveView.as_view(), name="change-request-approve"),

    # Reject a specific change request
    path("change-requests/<int:pk>/reject/", ChangeRequestRejectView.as_view(), name="change-request-reject"),
    path("invoices/generate/<int:pk>/", InvoiceGenerateAPIView.as_view(), name="generate-invoice"),
    path('download-invoice/<str:filename>/', download_invoice, name='download-invoice'),


    path("notifications/", NotificationListAPIView.as_view(), name="notifications"),
    path("rules/", RuleListCreateAPIView.as_view(), name="rules")
]
