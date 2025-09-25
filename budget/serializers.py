from rest_framework import serializers
from .models import ProjectEstimation, ProjectPaymentTracking, ProjectPaymentMilestone, ChangeRequest
from project_creation.models import Project, Client
from .models import (ProjectPaymentTracking, ProjectPaymentMilestone, PaymentTransaction,
                     AdditionalBudgetRequest, Notification, Rule, PaymentHistory, AuditLog,Hold,BudgetPolicy,Invoice)
from roles.models import UserRole
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone



class EstimationSerializer(serializers.ModelSerializer):

    project_name = serializers.SerializerMethodField()
    estimation_provider_name = serializers.SerializerMethodField()
    estimation_review_name = serializers.SerializerMethodField()
    estimation_review_by_client_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    modified_by_name = serializers.SerializerMethodField()

    # Consistency and summary fields
    is_data_consistent = serializers.SerializerMethodField()
    payment_summary = serializers.SerializerMethodField()
    consistency_issues = serializers.SerializerMethodField()

    class Meta:
        model = ProjectEstimation
        fields = (
            "id", "project", "project_name",
            "estimation_provider", "estimation_provider_name",
            "estimation_review", "estimation_review_name",
            "estimation_review_by_client", "estimation_review_by_client_name",
            "created_at", "modified_at", "estimation_date", "version",
            "initial_amount", "additional_amount",
            "total_amount", "pending_amount", "received_amount",
            "is_approved", "purchase_order_status",
            "created_by", "created_by_name",
            "modified_by", "modified_by_name",
            "is_data_consistent", "payment_summary", "consistency_issues",
        )
        read_only_fields = (
            "id", "pending_amount", "total_amount",
            "is_data_consistent", "payment_summary", "consistency_issues",
            "created_at", "modified_at", "created_by_name", "modified_by_name",
            "project_name", "estimation_provider_name",
            "estimation_review_name", "estimation_review_by_client_name",
        )

    # ====== Related Names ======
    def get_project_name(self, obj):
        return getattr(obj.project, "project_name", None)

    def get_estimation_provider_name(self, obj):
        return getattr(obj.estimation_provider.user, "username", None) if obj.estimation_provider else None

    def get_estimation_review_name(self, obj):
        return getattr(obj.estimation_review.user, "username", None) if obj.estimation_review else None

    def get_estimation_review_by_client_name(self, obj):
        return getattr(obj.estimation_review_by_client, "client_name", None) if obj.estimation_review_by_client else None

    def get_created_by_name(self, obj):
        return getattr(obj.created_by, "username", None)

    def get_modified_by_name(self, obj):
        return getattr(obj.modified_by, "username", None)

    # ====== Consistency & Payment ======
    def get_is_data_consistent(self, obj):
        return getattr(obj, "status_with_validation", {}).get('is_consistent', True)

    def get_consistency_issues(self, obj):
        return getattr(obj, "status_with_validation", {}).get('issues', [])

    def get_payment_summary(self, obj):
        return getattr(obj, "payment_summary", {})


    # def validate(self, attrs):
    
    #     project = attrs.get('project') or getattr(self.instance, 'project', None)
    #     if not project:
    #         raise serializers.ValidationError("Project is required.")
    #     if not Project.objects.filter(id=project.id, is_active=True).exists():
    #         raise serializers.ValidationError("Active project not found.")

    #     # --- UserRole & Client validation ---
    #     for field, model, name in [
    #         ('estimation_provider', UserRole, 'Estimation provider'),
    #         ('estimation_review', UserRole, 'Estimation reviewer'),
    #         ('estimation_review_by_client', Client, 'Client reviewer'),
    #     ]:
    #         obj = attrs.get(field) or getattr(self.instance, field, None)
    #         if obj and not model.objects.filter(pk=obj.pk).exists():
    #             raise serializers.ValidationError(f"{name} is invalid.")

    #     # --- Status validation ---
    #     purchase_order_status = attrs.get(
    #         'purchase_order_status',
    #         getattr(self.instance, 'purchase_order_status', ProjectEstimation.STATUS_PENDING)
    #     )

    #     allowed_statuses = [choice[0] for choice in ProjectEstimation.STATUS_CHOICES]
    #     if purchase_order_status not in allowed_statuses:
    #         raise serializers.ValidationError("Invalid purchase order status.")

    #     # Automatically set is_approved based on status
    #     attrs['is_approved'] = purchase_order_status == ProjectEstimation.STATUS_APPROVED

    #     # --- Amount validation ---
    #     initial_amount = attrs.get('initial_amount', getattr(self.instance, 'initial_amount', Decimal('0.00')))
    #     additional_amount = attrs.get('additional_amount', getattr(self.instance, 'additional_amount', Decimal('0.00')))
    #     received_amount = attrs.get('received_amount', getattr(self.instance, 'received_amount', Decimal('0.00')))
    #     if any(a < 0 for a in [initial_amount, additional_amount, received_amount]):
    #         raise serializers.ValidationError("Amounts cannot be negative.")

    #     total_amount = initial_amount + additional_amount
    #     if received_amount > total_amount:
    #         raise serializers.ValidationError({"error":"Received amount cannot exceed total amount."})

    #     # --- Versioning & Creation Rules ---
    #     if not getattr(self.instance, 'id', None):  # Only on create 
    #         if ProjectEstimation.objects.filter(
    #             project=project,
    #             purchase_order_status__in=[ProjectEstimation.STATUS_APPROVED, ProjectEstimation.STATUS_RECEIVED]
    #         ).exists():
    #             raise serializers.ValidationError({"error":
    #                 "A project already has an Approved/Received estimation. New estimation cannot be created."}
    #             )

    #         last_estimation = ProjectEstimation.objects.filter(project=project).order_by('-version').first()
    #         attrs['version'] = (last_estimation.version + 1) if last_estimation else 1
    #     else:
    #         attrs['version'] = getattr(self.instance, 'version', 1)

    #         # --- Enforce only one Approved estimation ---
    #         if purchase_order_status == ProjectEstimation.STATUS_APPROVED:
    #             approved_exists = ProjectEstimation.objects.filter(
    #                 project=project,
    #                 purchase_order_status=ProjectEstimation.STATUS_APPROVED
    #             ).exclude(id=self.instance.id).exists()
    #             if approved_exists:
    #                 raise serializers.ValidationError({"error":
    #                     "Another estimation is already approved for this project. Cannot approve this one."}
    #                 )

    #     # --- Date validation ---
    #     estimation_date = attrs.get('estimation_date', getattr(self.instance, 'estimation_date', timezone.now().date()))
    #     if estimation_date > timezone.now().date():
    #         raise serializers.ValidationError({"error":"Estimation date cannot be in the future."})

    #     # --- Auto-calc amounts ---
    #     attrs['total_amount'] = total_amount
    #     attrs['pending_amount'] = total_amount - received_amount

    #     # --- Status change check ---
    #     if self.instance:
    #         current_status = self.instance.purchase_order_status
    #         new_status = attrs.get('purchase_order_status', current_status)
    #         if current_status == ProjectEstimation.STATUS_RECEIVED and new_status != ProjectEstimation.STATUS_RECEIVED:
    #             raise serializers.ValidationError({"error":"Cannot change status from 'Received'"})

    #     return attrs
    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        project = attrs.get('project') or getattr(instance, 'project', None)
        
        # ===== Project Validation =====
        if not project:
            raise serializers.ValidationError("Project is required.")
        if not Project.objects.filter(id=project.id, is_active=True).exists():
            raise serializers.ValidationError("Active project not found.")

        # ===== UserRole & Client Validation =====
        for field, model, name in [
            ('estimation_provider', UserRole, 'Estimation provider'),
            ('estimation_review', UserRole, 'Estimation reviewer'),
            ('estimation_review_by_client', Client, 'Client reviewer'),
        ]:
            obj = attrs.get(field) or getattr(instance, field, None)
            if obj and not model.objects.filter(pk=obj.pk).exists():
                raise serializers.ValidationError(f"{name} is invalid.")

        # ===== Status Validation =====
        new_status = attrs.get(
            'purchase_order_status',
            getattr(instance, 'purchase_order_status', ProjectEstimation.STATUS_PENDING)
        )

        # Prevent creating or updating directly to RECEIVED
        if new_status == ProjectEstimation.STATUS_RECEIVED:
            if not instance:
                raise serializers.ValidationError({
                    "purchase_order_status": "Cannot create a new estimation as 'Received'. Must be Approved first."
                })
            if instance.purchase_order_status != ProjectEstimation.STATUS_APPROVED:
                raise serializers.ValidationError({
                    "purchase_order_status": "Cannot mark as 'Received' unless estimation is Approved."
                })

        # Automatically set is_approved based on status
        attrs['is_approved'] = new_status == ProjectEstimation.STATUS_APPROVED

        # ===== Amount Validation =====
        initial_amount = attrs.get('initial_amount', getattr(instance, 'initial_amount', Decimal('0.00')))
        additional_amount = attrs.get('additional_amount', getattr(instance, 'additional_amount', Decimal('0.00')))
        received_amount = attrs.get('received_amount', getattr(instance, 'received_amount', Decimal('0.00')))

        if any(a < 0 for a in [initial_amount, additional_amount, received_amount]):
            raise serializers.ValidationError("Amounts cannot be negative.")

        total_amount = initial_amount + additional_amount
        if received_amount > total_amount:
            raise serializers.ValidationError({"error": "Received amount cannot exceed total amount."})

        attrs['total_amount'] = total_amount
        attrs['pending_amount'] = total_amount - received_amount

        # ===== Versioning & Creation Rules =====
        if not instance:  # Only on create
            if ProjectEstimation.objects.filter(
                project=project,
                purchase_order_status__in=[ProjectEstimation.STATUS_APPROVED, ProjectEstimation.STATUS_RECEIVED]
            ).exists():
                raise serializers.ValidationError({"error":
                    "A project already has an Approved/Received estimation. New estimation cannot be created."
                })

            last_estimation = ProjectEstimation.objects.filter(project=project).order_by('-version').first()
            attrs['version'] = (last_estimation.version + 1) if last_estimation else 1
        else:
            attrs['version'] = getattr(instance, 'version', 1)

            # Enforce only one Approved estimation
            if new_status == ProjectEstimation.STATUS_APPROVED:
                approved_exists = ProjectEstimation.objects.filter(
                    project=project,
                    purchase_order_status=ProjectEstimation.STATUS_APPROVED
                ).exclude(id=instance.id).exists()
                if approved_exists:
                    raise serializers.ValidationError({"error":
                        "Another estimation is already approved for this project. Cannot approve this one."
                    })

        # ===== Date Validation =====
        estimation_date = attrs.get('estimation_date', getattr(instance, 'estimation_date', timezone.now().date()))
        if estimation_date > timezone.now().date():
            raise serializers.ValidationError({"error": "Estimation date cannot be in the future."})

        # ===== Prevent status change from RECEIVED =====
        if instance and instance.purchase_order_status == ProjectEstimation.STATUS_RECEIVED and new_status != ProjectEstimation.STATUS_RECEIVED:
            raise serializers.ValidationError({"error": "Cannot change status from 'Received'."})

        return attrs

            



    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.purchase_order_status == ProjectEstimation.STATUS_RECEIVED:
            instance.received_amount = instance.total_amount
            instance.pending_amount = Decimal("0.00")
            instance.save()
        return instance

    def update(self, instance, validated_data):
        if validated_data.get("purchase_order_status") == ProjectEstimation.STATUS_RECEIVED:
            raise serializers.ValidationError({
                "purchase_order_status": "Cannot mark as 'Received' via update. Use receive_money() method."
            })
        instance = super().update(instance, validated_data)
        instance.save()
        return instance
class ChangeRequestSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ChangeRequest
        fields = (
            "id",
            "project",
            "project_name",
            "requested_amount",
            "reason",
            "status",
            "requested_by",
            "requested_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "created_at",
            "modified_at",
        )
        read_only_fields = ("status", "reviewed_by", "reviewed_at", "created_at", "modified_at")

    def get_project_name(self, obj):
        return getattr(obj.project, "project_name", None)

    def get_requested_by_name(self, obj):
        return getattr(obj.requested_by, "username", None) if obj.requested_by else None

    def get_reviewed_by_name(self, obj):
        return getattr(obj.reviewed_by, "username", None) if obj.reviewed_by else None

class ProjectPaymentMilestoneSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPaymentMilestone
        fields = [
            "id", "payment_tracking", "name", "amount", "due_date", "status",
            "actual_completion_date", "notes", "created_by", "modified_by",
            "created_at", "modified_at"
        ]
        read_only_fields = ["created_at", "modified_at"]

    def get_created_by(self, obj):
        return getattr(obj.created_by, "username", None)

    def get_modified_by(self, obj):
        return getattr(obj.modified_by, "username", None)

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Milestone amount must be positive.")
        return value


class HoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hold
        fields = ['id', 'amount','hold_reason', 'is_active', 'created_at', 'released_at','payment_tracking']




from decimal import Decimal
from rest_framework import serializers

# class ProjectPaymentTrackingSerializer(serializers.ModelSerializer):
#     milestones = ProjectPaymentMilestoneSerializer(many=True, read_only=True)
#     holds = HoldSerializer(many=True, read_only=True)
    
#     total_available_budget = serializers.SerializerMethodField()
#     total_milestones_amount = serializers.SerializerMethodField()
#     completed_milestones_amount = serializers.SerializerMethodField()
#     total_holds_amount = serializers.SerializerMethodField()
#     pending = serializers.SerializerMethodField()
#     budget_utilization_percentage = serializers.SerializerMethodField()
#     created_by = serializers.SerializerMethodField()
#     modified_by = serializers.SerializerMethodField()

#     class Meta:
#         model = ProjectPaymentTracking
#         fields = [
#             "id", "project", "payment_type", "resource", "currency",
#             "approved_budget", "additional_amount",
#             "payout", "retention_amount", "penalty_amount",
#             "total_available_budget", "total_milestones_amount", "completed_milestones_amount",
#             "total_holds_amount", "pending", "budget_utilization_percentage",
#             "is_budget_locked", "budget_exceeded_approved",
#             "created_by", "modified_by", "created_at", "modified_at",
#             "milestones", "holds",
#         ]
#         read_only_fields = [
#             "created_at", "modified_at", "total_available_budget", "total_milestones_amount",
#             "completed_milestones_amount", "total_holds_amount", "pending", "budget_utilization_percentage",
#             "milestones", "holds",
#         ]

  
#     def get_total_available_budget(self, obj):
#         return obj.total_available_budget

#     def get_total_milestones_amount(self, obj):
#         return obj.total_milestones_amount

#     def get_completed_milestones_amount(self, obj):
#         return obj.completed_milestones_amount

#     def get_total_holds_amount(self, obj):
#         return obj.total_holds_amount

#     def get_pending(self, obj):
#         return obj.pending

#     def get_budget_utilization_percentage(self, obj):
#         return obj.budget_utilization_percentage

#     def get_created_by(self, obj):
#         return getattr(obj.created_by, "username", None)

#     def get_modified_by(self, obj):
#         return getattr(obj.modified_by, "username", None)

class ProjectPaymentTrackingSerializer(serializers.ModelSerializer):
    milestones = ProjectPaymentMilestoneSerializer(many=True, read_only=True)
    holds = HoldSerializer(many=True, read_only=True)

    total_available_budget = serializers.SerializerMethodField()
    total_milestones_amount = serializers.SerializerMethodField()
    completed_milestones_amount = serializers.SerializerMethodField()
    calculated_payout_from_milestones = serializers.SerializerMethodField()
    total_holds_amount = serializers.SerializerMethodField()
    pending = serializers.SerializerMethodField()
    budget_utilization_percentage = serializers.SerializerMethodField()
    payout_variance = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()
    total_payout = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPaymentTracking
        fields = [
            "id", "project", "payment_type", "resource", "currency",
            "approved_budget", "additional_amount",
            "payout", "is_payout_manual", "calculated_payout_from_milestones", "payout_variance",
            "retention_amount", "penalty_amount",
            "total_available_budget", "total_milestones_amount", "completed_milestones_amount",
            "total_holds_amount", "pending", "budget_utilization_percentage",
            "is_budget_locked", "budget_exceeded_approved",
            "created_by", "modified_by", "created_at", "modified_at",
            "milestones", "holds","total_payout",
        ]
        read_only_fields = [
            "created_at", "modified_at", "total_available_budget", "total_milestones_amount",
            "completed_milestones_amount", "calculated_payout_from_milestones", "payout_variance",
            "total_holds_amount", "pending", "budget_utilization_percentage",
            "milestones", "holds",
        ]

    def _safe_decimal(self, value):
        try:
            return str(Decimal(value))
        except Exception:
            return "0.00"
    def get_total_payout(self, obj):
        milestones_total = sum(m.amount for m in obj.milestones.all())
        return float(obj.payout or 0) + float(milestones_total)
    

    def get_total_available_budget(self, obj):
        return self._safe_decimal(getattr(obj, "total_available_budget", 0))

    def get_total_milestones_amount(self, obj):
        return self._safe_decimal(getattr(obj, "total_milestones_amount", 0))

    def get_completed_milestones_amount(self, obj):
        return self._safe_decimal(getattr(obj, "completed_milestones_amount", 0))

    def get_calculated_payout_from_milestones(self, obj):
        return self._safe_decimal(getattr(obj, "calculated_payout_from_milestones", 0))

    def get_total_holds_amount(self, obj):
        return self._safe_decimal(getattr(obj, "total_holds_amount", 0))

    def get_pending(self, obj):
        return self._safe_decimal(getattr(obj, "pending", 0))

    def get_budget_utilization_percentage(self, obj):
        return self._safe_decimal(getattr(obj, "budget_utilization_percentage", 0))

    def get_payout_variance(self, obj):
        return self._safe_decimal(getattr(obj, "payout_variance", 0))

    def get_created_by(self, obj):
        return getattr(obj.created_by, "username", None) if obj.created_by else None

    def get_modified_by(self, obj):
        return getattr(obj.modified_by, "username", None) if obj.modified_by else None

class ProjectPaymentTrackingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPaymentTracking
        fields = "__all__"
        extra_kwargs = {
            "project": {"required": False},
            "payment_type": {"required": False},
        }

            
class ProfitLossSerializer(serializers.Serializer):
    estimated_submitted = serializers.DecimalField(max_digits=16, decimal_places=2)
    estimated_approved = serializers.DecimalField(max_digits=16, decimal_places=2)
    project_cost_approved_budget = serializers.DecimalField(max_digits=16, decimal_places=2)
    project_cost_actuals = serializers.DecimalField(max_digits=16, decimal_places=2)
    payout = serializers.DecimalField(max_digits=16, decimal_places=2)
    pending = serializers.DecimalField(max_digits=16, decimal_places=2)

    # New fields
    profit = serializers.SerializerMethodField()
    loss = serializers.SerializerMethodField()
    warning = serializers.SerializerMethodField()

    def get_profit(self, obj):
        # profit = estimated_approved - project_cost_actuals (if positive)
        profit_value = Decimal(obj['estimated_approved']) - Decimal(obj['project_cost_actuals'])
        return profit_value if profit_value > 0 else Decimal("0.00")

    def get_loss(self, obj):
        # loss = project_cost_actuals - estimated_approved (if positive)
        loss_value = Decimal(obj['project_cost_actuals']) - Decimal(obj['estimated_approved'])
        return loss_value if loss_value > 0 else Decimal("0.00")

    def get_warning(self, obj):
        if Decimal(obj['project_cost_approved_budget']) > Decimal(obj['estimated_approved']):
            diff = Decimal(obj['project_cost_approved_budget']) - Decimal(obj['estimated_approved'])
            return f"Project cost exceeds approved estimate by {diff}. Consider a ChangeRequest."
        return None

            # Instead of blocking, attach warning


class PaymentTransactionSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PaymentTransaction
        fields = ["id", "payment_tracking", "amount", "transaction_date", "method", "notes", "created_by", "created_at"]
        read_only_fields = ["created_at"]

class AdditionalBudgetRequestSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    approved_by = serializers.SerializerMethodField()
    approved_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = AdditionalBudgetRequest
        # fields = ["id", "payment_tracking", "requested_amount", "reason", "status", "created_by", "created_at", "approved_by", "approved_at", "approval_notes"]
        fields= '__all__'
        read_only_fields = ["status", "created_at", "approved_by", "approved_at", "approval_notes"]

    def get_approved_by(self, obj):
        return obj.approved_by.username if obj.approved_by else None

    def validate_requested_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Requested amount must be positive.")
        return value
    


class BudgetPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetPolicy
        fields = "__all__"
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = "__all__"


class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = "__all__"


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    client_name = serializers.CharField(source="project.client.name", read_only=True)
    estimation_summary = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_date", "due_date",
            "amount", "status", "notes", "pdf_file",
            "project", "project_name", "client_name", "estimation", "estimation_summary",
            "created_at", "modified_at"
        ]
        read_only_fields = ["invoice_number", "pdf_file", "status"]

    def get_estimation_summary(self, obj):
        return {
            "total_amount": obj.estimation.total_amount,
            "received_amount": obj.estimation.received_amount,
            "pending_amount": obj.estimation.pending_amount,
            "payment_summary": obj.estimation.payment_summary
        }