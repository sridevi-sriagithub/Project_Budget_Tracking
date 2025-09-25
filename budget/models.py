from django.db import models
# Create your models here.
from project_creation.models import Project
from login.models import User
from roles.models import UserRole
from django.utils import timezone
from project_creation.models import Client
from django.core.exceptions import ValidationError
from django.db.models import Sum
from masterdata.models import MasterData
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from masterdata.models import MasterData
from django.db.models.functions import Coalesce

from django.db.models import Sum, Value, DecimalField

class ProjectEstimation(models.Model):
    # ====== Status constants ======
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_RECEIVED = "Received"
    STATUS_REJECTED = "Rejected"
    STATUS_CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # ====== Fields ======
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="estimations")
    estimation_provider = models.ForeignKey(
        UserRole, on_delete=models.SET_NULL, null=True, blank=True, related_name="estimations_provided"
    )
    estimation_review = models.ForeignKey(
        UserRole, on_delete=models.SET_NULL, null=True, blank=True, related_name="estimations_reviewed"
    )
    estimation_review_by_client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="client_estimations"
    )

    estimation_date = models.DateField(default=timezone.now)
    version = models.PositiveIntegerField(default=1)

    initial_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    additional_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    pending_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    received_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    is_approved = models.BooleanField(default=False)
    purchase_order_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="estimations_created"
    )
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="estimations_modified"
    )

    # ====== Meta ======
    class Meta:
        ordering = ["-created_at"]

    # ====== String representation ======
    def __str__(self):
        return f"{self.project.project_name if self.project else 'Project'} - v{self.version} ({self.purchase_order_status})"

    # ====== Clean validation ======
    def clean(self):
        """Validate data consistency before saving"""
        super().clean()
        if self.received_amount > self.total_amount:
            raise ValidationError("Received amount cannot exceed total amount")
        if self.purchase_order_status == self.STATUS_RECEIVED and self.pending_amount > 0:
            raise ValidationError("Received status requires pending amount to be zero")

    # ====== Save override ======
    def save(self, *args, **kwargs):
        # Recalculate total and pending
        self.total_amount = (self.initial_amount or Decimal("0.00")) + (self.additional_amount or Decimal("0.00"))
        self.pending_amount = self.total_amount - (self.received_amount or Decimal("0.00"))
        if self.pending_amount < 0:
            self.pending_amount = Decimal("0.00")

        # Enforce full payment if status is Received
        if self.purchase_order_status == self.STATUS_RECEIVED:
            self.received_amount = self.total_amount
            self.pending_amount = Decimal("0.00")

        super().save(*args, **kwargs)

    # ====== Utility methods ======
    @classmethod
    def latest_estimation(cls, project):
        return cls.objects.filter(project=project).order_by("-version").first()

    # @transaction.atomic
    # def receive_money(self, receiver, amount=None):
    #     """Record money received for this estimation"""
    #     if self.purchase_order_status in [self.STATUS_REJECTED, self.STATUS_CANCELLED]:
    #         raise ValueError(f"Cannot receive money for {self.purchase_order_status.lower()} estimation")

    #     amount_to_receive = amount or self.pending_amount
    #     if amount_to_receive <= 0:
    #         raise ValueError("Amount to receive must be positive")
    #     if amount_to_receive > self.pending_amount:
    #         raise ValueError(f"Cannot receive {amount_to_receive}. Only {self.pending_amount} is pending")

    #     self.received_amount += amount_to_receive
    #     self.modified_by = receiver
    #     self.modified_at = timezone.now()
    #     self.save(update_fields=["received_amount", "pending_amount", "purchase_order_status", "modified_by", "modified_at", "total_amount"])

    @transaction.atomic
    def receive_money(self, receiver, amount=None):
        """Record money received for this estimation"""

        # Only approved estimations can receive money
        if not self.is_approved or self.purchase_order_status != self.STATUS_APPROVED:
            raise ValueError("Only approved estimations can be marked as received")

        if self.purchase_order_status in [self.STATUS_REJECTED, self.STATUS_CANCELLED]:
            raise ValueError(f"Cannot receive money for {self.purchase_order_status.lower()} estimation")

        amount_to_receive = amount or self.pending_amount
        if amount_to_receive <= 0:
            raise ValueError("Amount to receive must be positive")
        if amount_to_receive > self.pending_amount:
            raise ValueError(f"Cannot receive {amount_to_receive}. Only {self.pending_amount} is pending")

        # Update amounts
        self.received_amount += amount_to_receive
        self.pending_amount = self.total_amount - self.received_amount
        if self.pending_amount < 0:
            self.pending_amount = Decimal("0.00")

        # Update status if fully received
        if self.pending_amount == 0:
            self.purchase_order_status = self.STATUS_RECEIVED

        self.modified_by = receiver
        self.modified_at = timezone.now()
        self.save(update_fields=["received_amount", "pending_amount", "purchase_order_status", "modified_by", "modified_at"])


    @transaction.atomic
    def approve_estimation(self, approver):
        """Approve the estimation"""
        if self.purchase_order_status in [self.STATUS_REJECTED, self.STATUS_CANCELLED, self.STATUS_RECEIVED]:
            raise ValueError(f"Cannot approve {self.purchase_order_status.lower()} estimation")
        self.is_approved = True
        self.modified_by = approver
        self.save()

    @transaction.atomic
    def reject_estimation(self, rejector):
        """Reject the estimation"""
        if self.purchase_order_status == self.STATUS_RECEIVED:
            raise ValueError("Cannot reject received estimation")
        self.purchase_order_status = self.STATUS_REJECTED
        self.is_approved = False
        self.modified_by = rejector
        self.save()

    @transaction.atomic
    def cancel_estimation(self, canceller):
        """Cancel the estimation"""
        if self.purchase_order_status == self.STATUS_RECEIVED:
            raise ValueError("Cannot cancel received estimation")
        self.purchase_order_status = self.STATUS_CANCELLED
        self.is_approved = False
        self.modified_by = canceller
        self.save()

    @transaction.atomic
    def fix_data_consistency(self):
        """Fix inconsistent amounts and status"""
        self.total_amount = (self.initial_amount or Decimal("0.00")) + (self.additional_amount or Decimal("0.00"))
        if self.purchase_order_status == self.STATUS_RECEIVED:
            self.received_amount = self.total_amount
            self.pending_amount = Decimal("0.00")
        else:
            self.pending_amount = self.total_amount - (self.received_amount or Decimal("0.00"))
            if self.pending_amount < 0:
                self.pending_amount = Decimal("0.00")
        super().save()

    @classmethod
    def find_inconsistent_records(cls):
        """Find all records with data inconsistencies"""
        return cls.objects.filter(
            models.Q(purchase_order_status=cls.STATUS_RECEIVED, pending_amount__gt=0) |
            models.Q(received_amount__gt=models.F('total_amount')) |
            models.Q(pending_amount__lt=0)
        )

    @classmethod
    @transaction.atomic
    def bulk_fix_inconsistent_data(cls):
        """Fix all inconsistent records in the database"""
        inconsistent = cls.find_inconsistent_records()
        fixed_count = 0
        for estimation in inconsistent:
            try:
                estimation.fix_data_consistency()
                fixed_count += 1
            except Exception as e:
                print(f"Error fixing estimation {estimation.id}: {e}")
        return fixed_count

    # ====== Properties ======
    @property
    def status_with_validation(self):
        is_consistent = True
        issues = []

        if self.purchase_order_status == self.STATUS_RECEIVED and self.pending_amount > 0:
            is_consistent = False
            issues.append("Status is 'Received' but pending amount > 0")
        if self.received_amount > self.total_amount:
            is_consistent = False
            issues.append("Received amount exceeds total amount")
        calculated_pending = self.total_amount - self.received_amount
        if abs(self.pending_amount - calculated_pending) > 0.01:
            is_consistent = False
            issues.append("Pending amount calculation is incorrect")

        return {
            "status": self.purchase_order_status,
            "is_consistent": is_consistent,
            "issues": issues,
            "pending_amount": self.pending_amount,
            "received_amount": self.received_amount,
            "total_amount": self.total_amount,
        }

    @property
    def payment_summary(self):
        percentage_received = 0
        if self.total_amount > 0:
            percentage_received = (self.received_amount / self.total_amount) * 100
        return {
            "total_amount": self.total_amount,
            "received_amount": self.received_amount,
            "pending_amount": self.pending_amount,
            "percentage_received": round(percentage_received, 2),
            "is_fully_paid": self.pending_amount == 0,
            "status": self.purchase_order_status,
        }

class ChangeRequest(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_RECEIVED = "Received"
    STATUS_REJECTED = "Rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_REJECTED, "Rejected"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="change_requests")
    requested_amount = models.DecimalField(max_digits=18, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="cr_requested")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="cr_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"CR#{self.id} for {self.project.project_name if self.project else 'Project'} - {self.requested_amount}"

    def approve(self, reviewer_user):
        if self.status != self.STATUS_PENDING:
            raise ValueError("Only pending CRs can be approved")

        from .services import BudgetMonitorService

        with transaction.atomic():
            self.status = self.STATUS_APPROVED
            self.reviewed_by = reviewer_user
            self.reviewed_at = timezone.now()
            self.save(update_fields=["status", "reviewed_by", "reviewed_at", "modified_at"])

            latest_est = ProjectEstimation.latest_estimation(self.project)
            new_version = (latest_est.version + 1) if latest_est else 1
            initial_amt = latest_est.total_amount if latest_est else Decimal("0.00")
            received_amt = latest_est.received_amount if latest_est else Decimal("0.00")

            ProjectEstimation.objects.create(
                project=self.project,
                estimation_date=timezone.now().date(),
                version=new_version,
                initial_amount=initial_amt,
                additional_amount=self.requested_amount,
                received_amount=received_amt,
                is_approved=True,
                purchase_order_status=ProjectEstimation.STATUS_APPROVED,
                created_by=reviewer_user,
                modified_by=reviewer_user,
            )

            BudgetMonitorService.monitor_project(self.project)

    def mark_received(self, reviewer_user):
        if self.status != self.STATUS_APPROVED:
            raise ValueError("Only approved CRs can be marked received")

        with transaction.atomic():
            self.status = self.STATUS_RECEIVED
            self.reviewed_by = reviewer_user
            self.reviewed_at = timezone.now()
            self.save(update_fields=["status", "reviewed_by", "reviewed_at", "modified_at"])

            latest_est = ProjectEstimation.latest_estimation(self.project)
            if latest_est:
                latest_est.receive_money(receiver=reviewer_user, amount=self.requested_amount)

        return latest_est
   
try:
    from project_creation.models import Project
except Exception:
  
    raise


CURRENCY_CHOICES = [
    ("INR", "Indian Rupee"),
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
]
class ProjectPaymentTracking(models.Model):
    COST_TYPE_CHOICES = [
        ("Manpower", "Manpower"),
        ("Operation Cost", "Operation Cost"),
        ("Transport", "Transport"),
        ("Interest", "Interest"),
        ("Other", "Other"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="payments")
    payment_type = models.CharField(max_length=50, choices=COST_TYPE_CHOICES)
    resource = models.ForeignKey(MasterData, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    currency = models.CharField(max_length=6, choices=CURRENCY_CHOICES, default="INR")
    approved_budget = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    additional_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    payout = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    is_payout_manual = models.BooleanField(default=False, help_text="True if payout was manually set")
    retention_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    penalty_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    is_budget_locked = models.BooleanField(default=False)
    budget_exceeded_approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="payment_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="payment_modified")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project Payment Tracking"
        verbose_name_plural = "Project Payment Trackings"

    # class Meta:
    #     ordering = ["-created_at"]

    def __str__(self):
        return f"{getattr(self.project, 'project_name', self.project_id)} - {self.payment_type} (#{self.id})"

    @property
    def total_available_budget(self) -> Decimal:
        return (self.approved_budget or Decimal("0.00")) + (self.additional_amount or Decimal("0.00"))

    @property
    def total_milestones_amount(self) -> Decimal:
        if not self.pk:
            return Decimal("0.00")
        total = self.milestones.aggregate(
            total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["total"]
        return Decimal(total or 0)

    @property
    def calculated_payout_from_milestones(self) -> Decimal:
        if not self.pk:
            return Decimal("0.00")
        total = self.milestones.filter(status="Completed").aggregate(
            total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["total"]
        return Decimal(total or 0)

    @property
    def completed_milestones_amount(self) -> Decimal:
        return self.calculated_payout_from_milestones

    # @property
    # def total_holds_amount(self) -> Decimal:
    #     if not hasattr(self, "holds"):
    #         return Decimal("0.00")
    #     total = self.holds.filter(is_active=True).aggregate(
    #         total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
    #     )["total"]
    #     return Decimal(total or 0)
    @property
    def total_holds_amount(self) -> Decimal:
        """Return total active holds, but avoid querying before instance has a pk."""
        if not self.pk:  # New object, no holds yet
            return Decimal("0.00")
        total = self.holds.filter(is_active=True).aggregate(
            total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["total"]
        return Decimal(total or 0)

    @property
    def pending(self) -> Decimal:
        return (
            self.total_available_budget
            - (self.payout or Decimal("0.00"))
            - self.total_holds_amount
            - (self.retention_amount or Decimal("0.00"))
            + (self.penalty_amount or Decimal("0.00"))
        )

    @property
    def payout_variance(self) -> Decimal:
        if not self.is_payout_manual:
            return Decimal("0.00")
        return (self.payout or Decimal("0.00")) - self.calculated_payout_from_milestones

    @property
    def budget_utilization_percentage(self) -> Decimal:
        if self.total_available_budget == Decimal("0.00"):
            return Decimal("0.00")
        used = (self.payout or Decimal("0.00")) + (self.retention_amount or Decimal("0.00")) + self.total_holds_amount
        return (used / self.total_available_budget * Decimal("100.00")).quantize(Decimal("0.01"))

    @property
    def is_budget_exceeded(self) -> bool:
        return self.total_milestones_amount > self.total_available_budget

    # def validate_budget_limit(self, new_payout=None):
    #     """Ensure payout + holds + retention <= total budget"""
    #     payout_to_check = Decimal(new_payout) if new_payout is not None else self.payout
    #     total_used = payout_to_check + self.retention_amount + self.total_holds_amount
    #     if total_used > self.total_available_budget:
    #         raise ValidationError(
    #             f"Budget exceeded! Allowed: {self.total_available_budget}, Attempted: {total_used}"
    #         )
    # def validate_budget_limit(self, new_payout=None):
    #     """Ensure payout + holds + retention <= total available budget"""
    #     payout_to_check = Decimal(new_payout) if new_payout is not None else (self.payout or Decimal("0.00"))
    #     total_used = payout_to_check + (self.retention_amount or Decimal("0.00")) + self.total_holds_amount

    #     if total_used > self.total_available_budget:
    #         raise ValidationError(
    #             f"Budget exceeded! Allowed: {self.total_available_budget}, Attempted: {total_used}"
    #         )
    def validate_budget_limit(self, new_payout=None):
        """Ensure payout + holds + retention <= total budget"""
        payout_to_check = Decimal(new_payout) if new_payout is not None else (self.payout or Decimal("0.00"))

        # On create, skip holds since they cannot exist yet
        holds_amount = self.total_holds_amount if self.pk else Decimal("0.00")

        total_used = payout_to_check + (self.retention_amount or Decimal("0.00")) + holds_amount

        if total_used > self.total_available_budget:
            raise ValidationError(
                f"Budget exceeded! Allowed: {self.total_available_budget}, Attempted: {total_used}"
            )


    # def set_manual_payout(self, amount):
    #     amount = Decimal(str(amount))
    #     self.validate_budget_limit(new_payout=amount)
    #     self.payout = amount
    #     self.is_payout_manual = True

    # def auto_calculate_payout(self):
    #     if not self.pk:
    #         return
    #     self.payout = self.calculated_payout_from_milestones
    #     self.is_payout_manual = False

    # def recalc_payout(self):
    #     self.payout = self.calculated_payout_from_milestones

    # def save(self, *args, **kwargs):
    #     if self.pk:
    #         # Fetch old instance to check manual changes
    #         try:
    #             old = ProjectPaymentTracking.objects.get(pk=self.pk)
    #             if old.payout != self.payout:
    #                 self.is_payout_manual = True
    #             elif not self.is_payout_manual:
    #                 self.auto_calculate_payout()
    #         except ProjectPaymentTracking.DoesNotExist:
    #             pass

    #     if self.is_payout_manual:
    #         self.validate_budget_limit()

    #     self.budget_exceeded_approved = self.is_budget_exceeded
    #     super().save(*args, **kwargs)
    def set_manual_payout(self, amount):
        """Explicitly set payout manually"""
        amount = Decimal(str(amount))
        self.validate_budget_limit(new_payout=amount)
        self.payout = amount
        self.is_payout_manual = True

    def auto_calculate_payout(self):
        """Auto calculate payout from milestones if not manual"""
        if not self.pk:
            return
        self.payout = self.calculated_payout_from_milestones
        self.is_payout_manual = False

    def recalc_payout(self):
        """Recalculate payout only if automatic"""
        if not self.is_payout_manual:
            self.auto_calculate_payout()

    def save(self, *args, **kwargs):
        if self.pk:
            old = ProjectPaymentTracking.objects.filter(pk=self.pk).first()

            # If payout was changed manually → mark as manual
            if old and old.payout != self.payout:
                self.is_payout_manual = True

            # If not manual → recalc from milestones
            if not self.is_payout_manual:
                self.auto_calculate_payout()
        else:
            # On create: if payout > 0 and no milestones exist, treat as manual
            if self.payout and self.payout > Decimal("0.00"):
                self.is_payout_manual = True

        # Always validate budget
        self.validate_budget_limit()

        # Update budget exceeded flag
        self.budget_exceeded_approved = self.is_budget_exceeded

        super().save(*args, **kwargs)



    # def __str__(self):
    #     return f"{getattr(self.project, 'project_name', self.project_id)} - {self.payment_type} (#{self.id})"

   
    # @property
    # def total_available_budget(self) -> Decimal:
    #     return (self.approved_budget or Decimal("0.00")) + (self.additional_amount or Decimal("0.00"))

    # @property
    # def total_milestones_amount(self) -> Decimal:
    #     if not self.pk:
    #         return Decimal("0.00")
    #     total = self.milestones.aggregate(
    #         total=Coalesce(
    #             Sum("amount"),
    #             Value(Decimal("0.00"), output_field=DecimalField(max_digits=16, decimal_places=2)),
    #             output_field=DecimalField(max_digits=16, decimal_places=2)
    #         )
    #     )["total"]
    #     return Decimal(total or 0)
    # @property
    # def calculated_payout_from_milestones(self) -> Decimal:
    #     """Calculate payout based on completed milestones"""
    #     if not self.pk:
    #         return Decimal("0.00")
    #     try:
    #         total = self.milestones.filter(status="Completed").aggregate(
    #             total=Coalesce(Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField())
    #         )["total"]
    #         return Decimal(total or 0)
    #     except Exception:
    #         return Decimal("0.00")


    # @property
    # def completed_milestones_amount(self) -> Decimal:
    #     if not self.pk:
    #         return Decimal("0.00")
    #     total = self.milestones.filter(status="Completed").aggregate(
    #         total=Coalesce(Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField())
    #     )["total"]
    #     return Decimal(total or 0)

    # @property
    # def total_holds_amount(self) -> Decimal:
    #     if not self.pk:
    #         return Decimal("0.00")
    #     total = self.holds.filter(is_active=True).aggregate(
    #         total=Coalesce(Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField())
    #     )["total"]
    #     return Decimal(total or 0)

    # # @property
    # # def pending(self) -> Decimal:
    # #     return (
    # #         self.total_available_budget
    # #         - (self.payout or Decimal("0.00"))
    # #         - self.total_holds_amount
    # #         - (self.retention_amount or Decimal("0.00"))
    # #         + (self.penalty_amount or Decimal("0.00"))
    # #     )
    # @property
    # def pending(self) -> Decimal:
    #     try:
    #         return (
    #             self.total_available_budget
    #             - (self.payout or Decimal("0.00"))
    #             - self.total_holds_amount
    #             - (self.retention_amount or Decimal("0.00"))
    #             + (self.penalty_amount or Decimal("0.00"))
    #         )
    #     except Exception:
    #         return Decimal("0.00")
        
    # @property
    # def payout_variance(self) -> Decimal:
    #     """Difference between manual payout and calculated payout"""
    #     if not self.is_payout_manual:
    #         return Decimal("0.00")
    #     return (self.payout or Decimal("0.00")) - self.calculated_payout_from_milestones

    # def auto_calculate_payout(self):
    #     """Auto-calculate payout from completed milestones"""
    #     if not self.pk:
    #         return
    #     calculated = self.calculated_payout_from_milestones
    #     self.payout = calculated
    #     self.is_payout_manual = False

    # def set_manual_payout(self, amount):
    #     """Set manual payout amount"""
    #     self.payout = Decimal(str(amount))
    #     self.is_payout_manual = True

    # @property
    # def budget_utilization_percentage(self) -> Decimal:
    #     if self.total_available_budget == Decimal("0.00"):
    #         return Decimal("0.00")
    #     used = (self.payout or Decimal("0.00")) + (self.retention_amount or Decimal("0.00")) + self.total_holds_amount
    #     return (used / self.total_available_budget * Decimal("100.00")).quantize(Decimal("0.01"))

    # @property
    # def is_budget_exceeded(self) -> bool:
    #     if not self.pk:
    #         return False
    #     return self.total_milestones_amount > self.total_available_budget

    # def recalc_payout(self):
    #     if not self.pk:
    #         return
    #     total = self.milestones.filter(status="Completed").aggregate(
    #         total=Coalesce(Sum("amount"), Value(Decimal("0.00")), output_field=DecimalField())
    #     )["total"] or Decimal("0.00")
    #     self.payout = total

    # def save(self, *args, **kwargs):
    #     # recalc payout only if object already has a PK
    #     if self.pk:
    #         try:
    #             self.recalc_payout()
    #         except Exception:
    #             pass
    #         self.budget_exceeded_approved = self.is_budget_exceeded
    #     super().save(*args, **kwargs)
    # def save(self, *args, **kwargs):
    #     # Check if this is an update and payout field was changed
    #     if self.pk:
    #         try:
    #             old_instance = ProjectPaymentTracking.objects.get(pk=self.pk)
                
    #             # If payout was explicitly changed, mark as manual
    #             if old_instance.payout != self.payout:
    #                 self.is_payout_manual = True
                
    #             # Only auto-recalculate if not manually set
    #             elif not self.is_payout_manual:
    #                 self.auto_calculate_payout()
                    
    #             self.budget_exceeded_approved = self.is_budget_exceeded
                
    #         except (ProjectPaymentTracking.DoesNotExist, Exception):
    #             # New instance or error, use current payout
    #             pass
        
    #     super().save(*args, **kwargs)

class ProjectPaymentMilestone(models.Model):
    STATUS_CHOICES = [
        ("Planned", "Planned"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"), 
        ("On Hold", "On Hold"),
        ("Cancelled", "Cancelled"),
    ]

    payment_tracking = models.ForeignKey(ProjectPaymentTracking, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Planned")
    actual_completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="milestone_created")
    modified_by = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name="milestone_modified")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "id"]
        verbose_name = "Payment Milestone"
        verbose_name_plural = "Payment Milestones"

    def __str__(self):
        return f"{self.name} - {self.amount} [{self.status}]"

    # def save(self, *args, **kwargs):
    #     is_new = self.pk is None
    #     old_status = None
    #     if not is_new:
    #         try:
    #             old_status = ProjectPaymentMilestone.objects.get(pk=self.pk).status
    #         except ProjectPaymentMilestone.DoesNotExist:
    #             old_status = None

    #     super().save(*args, **kwargs)

    #     if (is_new and self.status == "Completed") or (old_status != "Completed" and self.status == "Completed"):
    #         tracking = self.payment_tracking
    #         tracking.recalc_payout()
    #         tracking.save()
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = ProjectPaymentMilestone.objects.get(pk=self.pk).status
            except ProjectPaymentMilestone.DoesNotExist:
                old_status = None

        super().save(*args, **kwargs)

        # Recalculate payout if milestone is completed
        if (is_new and self.status == "Completed") or (old_status != "Completed" and self.status == "Completed"):
            tracking = self.payment_tracking
            tracking.recalc_payout()
            tracking.save()



class Hold(models.Model):
    payment_tracking = models.ForeignKey(ProjectPaymentTracking, related_name='holds', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    hold_reason = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.payment_tracking.save()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        payment_tracking = self.payment_tracking
        super().delete(*args, **kwargs)
        try:
            payment_tracking.save()
        except Exception:
            pass

    def __str__(self):
        status = "Active" if self.is_active else "Released"
        return f"Hold {self.amount} ({status}) on PaymentTracking #{self.payment_tracking_id}"


class PaymentTransaction(models.Model):
    """
    Records every payout (partial/full). Business logic that updates parent payout should live in services.
    """
    payment_tracking = models.ForeignKey(ProjectPaymentTracking, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    transaction_date = models.DateTimeField(default=timezone.now) 
    method = models.CharField(max_length=255, blank=True, null=True)  # e.g., Bank Transfer
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transactions_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self):
        return f"TX #{self.id} - PT#{self.payment_tracking_id} - {self.amount}"


class AdditionalBudgetRequest(models.Model):
    """
    Request / approval workflow for adding to additional_amount on parent PaymentTracking.
    Approve() method atomically applies the change.
    """
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_REJECTED = "Rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    payment_tracking = models.ForeignKey(ProjectPaymentTracking, on_delete=models.CASCADE, related_name="budget_requests")
    requested_amount = models.DecimalField(max_digits=16, decimal_places=2)
    reason = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="budget_requests_created")
    created_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="budget_requests_approved")
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Additional Budget Request"
        verbose_name_plural = "Additional Budget Requests"

    def __str__(self):
        return f"AddReq #{self.id} PT#{self.payment_tracking_id} {self.requested_amount} [{self.status}]"

    @transaction.atomic
    def approve(self, approver_user, approval_notes: str = ""):
        if self.status == self.STATUS_APPROVED:
            raise ValidationError("Request already approved.")
        if self.status == self.STATUS_REJECTED:
            raise ValidationError("Request already rejected.")

        # apply to payment tracking atomically
        pt = ProjectPaymentTracking.objects.select_for_update().get(pk=self.payment_tracking_id)
        pt.additional_amount = (pt.additional_amount or Decimal("0.00")) + (self.requested_amount or Decimal("0.00"))
        # If approving budget resolves exceeded budget, keep a flag
        pt.budget_exceeded_approved = pt.is_budget_exceeded or pt.budget_exceeded_approved
        pt.modified_by = approver_user
        pt.save()

        self.status = self.STATUS_APPROVED
        self.approved_by = approver_user
        self.approved_at = timezone.now()
        self.approval_notes = approval_notes
        self.save()
        return self

    @transaction.atomic
    def reject(self, approver_user, notes: str = ""):
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending requests can be rejected.")
        self.status = self.STATUS_REJECTED
        self.approved_by = approver_user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
        return self

class Rule(models.Model):
    """
    Lightweight rules engine configuration.
    type: which metric to evaluate (budget_utilization, pending_percentage, completed_milestones)
    operator: gt, gte, lt, lte
    value: numeric threshold
    """
    TYPE_CHOICES = [
        ("budget_utilization", "Budget Utilization (%)"),
        ("pending_percentage", "Pending Percentage (%)"),
        ("completed_milestones", "Completed Milestones Amount"),
    ]

    OP_CHOICES = [("gt", ">"), ("gte", ">="), ("lt", "<"), ("lte", "<=")]

    type = models.CharField(max_length=64, choices=TYPE_CHOICES)
    operator = models.CharField(max_length=4, choices=OP_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rule {self.type} {self.operator} {self.value}"


class PaymentHistory(models.Model):
    """
    Explicit history entries (alternative/complimentary to AuditLog) for payment changes.
    """
    payment_tracking = models.ForeignKey(ProjectPaymentTracking, on_delete=models.CASCADE, related_name="history")
    field_changed = models.CharField(max_length=255)
    prev_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"History PT#{self.payment_tracking_id} {self.field_changed} @ {self.changed_at}"



class BudgetPolicy(models.Model):
    MODE_STRICT = "STRICT"
    MODE_FLEX = "FLEXIBLE"
    MODE_AUTO = "AUTO_ADJUST"

    MODE_CHOICES = [
        (MODE_STRICT, "Strict - block when exceeding approved estimation"),
        (MODE_FLEX, "Flexible - allow but warn/audit"),
        (MODE_AUTO, "Auto Adjust - trim to remaining budget"),
    ]

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="budget_policy")
    mode = models.CharField(max_length=32, choices=MODE_CHOICES, default=MODE_STRICT)
    warning_threshold_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("80.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{getattr(self.project, 'project_name', self.project_id)} Policy ({self.mode})"

class AuditLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="audit_logs", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def record(cls, project, user, action, payload=None):
        try:
            cls.objects.create(project=project, user=user, action=action, payload=payload or {})
        except Exception:
            pass

    def __str__(self):
        return f"{self.action} @ {self.created_at}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    extra = models.JSONField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification: {self.title} -> {self.user}"



from django.db import models
from django.utils.timezone import now
from decimal import Decimal

class Invoice(models.Model):
    STATUS_CHOICES = [
        ("Unpaid", "Unpaid"),
        ("Paid", "Paid"),
        ("Overdue", "Overdue"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invoices")
    estimation = models.ForeignKey(ProjectEstimation, on_delete=models.CASCADE, related_name="invoices")

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Unpaid")
    notes = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to="invoices/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def mark_paid(self):
        self.status = "Paid"
        self.save()

    def is_overdue(self):
        return self.due_date < now().date() and self.status != "Paid"

    def __str__(self):
        return f"{self.invoice_number} - {self.project.project_name}"
