from django.contrib import admin
from .models import (
  ProjectPaymentTracking, ProjectPaymentMilestone, PaymentTransaction,
    AdditionalBudgetRequest, AuditLog, Notification, Rule, PaymentHistory, ProjectEstimation
)

admin.site.register(ProjectEstimation)
admin.site.register(ProjectPaymentTracking)
admin.site.register(ProjectPaymentMilestone)
admin.site.register(PaymentTransaction)
admin.site.register(AdditionalBudgetRequest)
admin.site.register(AuditLog)
admin.site.register(Notification)
admin.site.register(Rule)
admin.site.register(PaymentHistory)
