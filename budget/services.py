from django.utils import timezone
from .tasks import send_email_async, send_html_email_async
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError
from .models import ProjectPaymentMilestone, ProjectPaymentTracking, PaymentTransaction, AdditionalBudgetRequest,ProjectEstimation, Notification, Rule,BudgetPolicy, AuditLog, ChangeRequest
from django.db import transaction
from .exceptions import ObjectNotFound
from django.db.models import Sum,F,Value,ExpressionWrapper
from decimal import Decimal
from .models import Rule, Notification
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce




def _listify(recipients):
    # allow single string or list
    if not recipients:
        return []
    return recipients if isinstance(recipients, (list, tuple)) else [recipients]


def notify_budget_request(request_obj):
    """Notify finance head for approval request"""
    subject = f"Approval Required: Additional Budget for {request_obj.payment_tracking.project.project_name}"
    message = f"""
A request for an additional budget has been raised.

Project: {request_obj.payment_tracking.project.project_name}
Requested Amount: {request_obj.requested_amount}
Reason: {request_obj.reason or 'N/A'}
Requested By: {request_obj.created_by}
Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}
    """

    recipients = ["finance-head@company.com"]  # fetch dynamically in real apps
    send_email_async.delay(subject, message, recipients)


def notify_budget_approval(request_obj):
    subject = f"Budget Request Approved - {request_obj.payment_tracking.project.project_name}"
    message = f"""
Your budget request has been approved.

Project: {request_obj.payment_tracking.project.project_name}
Approved Amount: {request_obj.requested_amount}
Approved By: {request_obj.approved_by}
Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}
    """
    recipients = [request_obj.created_by.email]
    send_email_async.delay(subject, message, recipients)


def notify_budget_rejection(request_obj):
    subject = f"Budget Request Rejected - {request_obj.payment_tracking.project.project_name}"
    message = f"""
Your budget request has been rejected.

Project: {request_obj.payment_tracking.project.project_name}
Requested Amount: {request_obj.requested_amount}
Reviewed By: {request_obj.approved_by}
Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}
    """
    recipients = [request_obj.created_by.email]
    send_email_async.delay(subject, message, recipients)

def notify_budget_breach(payment_obj):
    subject = f"⚠️ Budget Breach Alert - {payment_obj.project.project_name}"
    message = f"""
Warning: The budget has been exceeded!

Project: {payment_obj.project.project_name}
Approved + Additional Budget: {payment_obj.total_available_budget}
Total Milestones: {payment_obj.total_milestones_amount}
Payout: {payment_obj.payout}
Pending: {payment_obj.pending}
    """
    recipients = ["cfo@company.com", "finance@company.com"]
    send_email_async.delay(subject, message, recipients)



def notify_budget_breach(payment, recipients):
    subject = f"Budget Exceeded: {payment.project.project_name}"
    context = {"payment": payment}
    body = render_to_string("finance/emails/budget_breach.txt", context)
    html = render_to_string("finance/emails/budget_breach.html", context)
    send_html_email_async.delay(subject, body, html, _listify(recipients))




def get_payment(payment_id):
    try:
        return ProjectPaymentTracking.objects.get(pk=payment_id)
    except ProjectPaymentTracking.DoesNotExist:
        raise ObjectNotFound(f"Payment tracking {payment_id} not found")

def create_payment(validated_data, user):
    validated_data["created_by"] = user
    validated_data["modified_by"] = user
    return ProjectPaymentTracking.objects.create(**validated_data)

def update_payment(payment_id, validated_data, user):
    payment = get_payment(payment_id)
    # Basic check: payout cannot exceed total_available_budget if provided
    if "payout" in validated_data:
        new_payout = validated_data.get("payout")
        total_available = payment.total_available_budget
        if new_payout > total_available:
            raise ValidationError({"payout": f"Payout ({new_payout}) cannot exceed total available budget ({total_available})."})
        # Also check payout <= completed milestones - enforced elsewhere for transactions.
    for k, v in validated_data.items():
        setattr(payment, k, v)
    payment.modified_by = user
    payment.save()
    return payment

def delete_payment(payment_id):
    p = get_payment(payment_id)
    p.delete()
    return True




def create_milestone(validated_data, user, enforce_budget=True):
    payment = validated_data["payment_tracking"]
    amount = validated_data["amount"]
    if amount <= Decimal("0.00"):
        raise ValidationError({"amount": "Milestone amount must be positive."})

    if enforce_budget:
        existing_total = payment.total_milestones_amount
        projected = existing_total + amount
        available = payment.total_available_budget
        if projected > available and not payment.budget_exceeded_approved:
            raise ValidationError({"__all__": f"Total milestones ({projected}) cannot exceed available budget ({available})."})

    m = ProjectPaymentMilestone.objects.create(
        payment_tracking=payment,
        name=validated_data["name"],
        amount=amount,
        due_date=validated_data.get("due_date"),
        status=validated_data.get("status", "Planned"),
        notes=validated_data.get("notes"),
        created_by=user,
        modified_by=user
    )
    return m



def notify_milestone_update(milestone_obj, extra_emails=None):
    subject = f"Milestone Update - {milestone_obj.payment_tracking.project.project_name}"
    message = f"""
Milestone '{milestone_obj.name}' has been updated.

Status: {milestone_obj.status}
Amount: {milestone_obj.amount}
Due Date: {milestone_obj.due_date}
Notes: {milestone_obj.notes or 'N/A'}
    """
    # default recipients
    recipients = ["project-owner@company.com", "finance@company.com"]
    
    # add extra emails if provided
    if extra_emails:
        recipients.extend(extra_emails)

    # send the email asynchronously
    send_email_async.delay(subject, message, recipients)



def notify_budget_breach(payment_obj):
    subject = f"⚠️ Budget Breach Alert - {payment_obj.project.project_name}"
    message = f"""
Warning: The budget has been exceeded!

Project: {payment_obj.project.project_name}
Approved + Additional Budget: {payment_obj.total_available_budget}
Total Milestones: {payment_obj.total_milestones_amount}
Payout: {payment_obj.payout}
Pending: {payment_obj.pending}
    """
    recipients = ["cfo@company.com", "finance@company.com"]
    send_email_async.delay(subject, message, recipients)

def delete_milestone(milestone_id):
    try:
        m = ProjectPaymentMilestone.objects.get(pk=milestone_id)
    except ProjectPaymentMilestone.DoesNotExist:
        raise ObjectNotFound(f"Milestone {milestone_id} not found")
    m.delete()
    return True



def create_transaction(payment_id, amount, user, method=None, notes=None):
    payment = ProjectPaymentTracking.objects.get(pk=payment_id)
    if amount <= Decimal("0.00"):
        raise ValidationError({"amount": "Transaction must be positive."})

    completed_total = payment.completed_milestones_amount
    # Payout after transaction should not exceed completed milestones nor total_available_budget
    if (payment.payout + amount) > completed_total:
        raise ValidationError({"amount": f"Payout after this transaction ({payment.payout + amount}) cannot exceed completed milestones total ({completed_total})."})

    if (payment.payout + amount) > payment.total_available_budget:
        raise ValidationError({"amount": f"Payout after this transaction ({payment.payout + amount}) cannot exceed total available budget ({payment.total_available_budget})."})

    with transaction.atomic():
        payment = ProjectPaymentTracking.objects.select_for_update().get(pk=payment_id)
        payment.payout = (payment.payout or Decimal("0.00")) + amount
        payment.modified_by = user
        payment.save()

        tx = PaymentTransaction.objects.create(
            payment_tracking=payment, amount=amount, method=method, notes=notes, created_by=user
        )
    return tx




def request_additional(payment_id, amount, reason, user):
    payment = ProjectPaymentTracking.objects.get(pk=payment_id)
    req = AdditionalBudgetRequest.objects.create(payment_tracking=payment, requested_amount=amount, reason=reason, created_by=user)
    return req

@transaction.atomic
def approve_request(req_id, approver_user, notes=""):
    try:
        req = AdditionalBudgetRequest.objects.select_for_update().get(pk=req_id)
    except AdditionalBudgetRequest.DoesNotExist:
        raise ObjectNotFound(f"AdditionalBudgetRequest {req_id} not found")

    if req.status == AdditionalBudgetRequest.STATUS_APPROVED:
        raise ValidationError("Already approved")

    if req.status == AdditionalBudgetRequest.STATUS_REJECTED:
        raise ValidationError("Already rejected")

    pt = ProjectPaymentTracking.objects.select_for_update().get(pk=req.payment_tracking_id)
    pt.additional_amount = (pt.additional_amount or 0) + (req.requested_amount or 0)
    pt.budget_exceeded_approved = pt.is_budget_exceeded or pt.budget_exceeded_approved
    pt.modified_by = approver_user
    pt.save()

    req.status = AdditionalBudgetRequest.STATUS_APPROVED
    req.approved_by = approver_user
    req.approved_at = timezone.now()
    req.approval_notes = notes
    req.save()
    return req

@transaction.atomic
def reject_request(req_id, approver_user, notes=""):
    try:
        req = AdditionalBudgetRequest.objects.select_for_update().get(pk=req_id)
    except AdditionalBudgetRequest.DoesNotExist:
        raise ObjectNotFound(f"AdditionalBudgetRequest {req_id} not found")

    if req.status != AdditionalBudgetRequest.STATUS_PENDING:
        raise ValidationError("Only pending requests can be rejected")

    req.status = AdditionalBudgetRequest.STATUS_REJECTED
    req.approved_by = approver_user
    req.approved_at = timezone.now()
    req.approval_notes = notes
    req.save()
    return req


def evaluate_rule(rule, payment):
    val = None
    if rule.type == "budget_utilization":
        val = payment.budget_utilization_percentage
    elif rule.type == "pending_percentage":
        total = payment.total_available_budget
        if total == Decimal("0.00"):
            return False
        val = (payment.pending / total) * Decimal("100.00")
    elif rule.type == "completed_milestones":
        val = payment.completed_milestones_amount
    else:
        return False

    op = rule.operator
    if op == "gt":
        return val > rule.value
    if op == "gte":
        return val >= rule.value
    if op == "lt":
        return val < rule.value
    if op == "lte":
        return val <= rule.value
    return False

def evaluate_and_notify(payment):
    rules = Rule.objects.filter(is_enabled=True)
    for r in rules:
        try:
            if evaluate_rule(r, payment):
                # notify project owner (if exists) as example
                if payment.created_by:
                    Notification.objects.create(
                        recipient=payment.created_by,
                        title=f"Rule triggered: {r}",
                        message=f"Rule {r} triggered for payment {payment.id}",
                        data={"payment_id": payment.id, "rule_id": r.id}
                    )
        except Exception:
            continue

from django.db.models import Sum, Q

def calculate_project_profit_loss(project_id):
    # ✅ Estimations
    est_aggs = ProjectEstimation.objects.filter(project_id=project_id).aggregate(
        estimated_submitted=Coalesce(Sum("initial_amount"), Decimal("0.00")),
        estimated_approved=Coalesce(
            Sum(
                "total_amount",
                filter=Q(is_approved=True) | Q(purchase_order_status="Approved")
            ),
            Decimal("0.00")
        ),
    )

    # ✅ Payments
    pay_aggs = ProjectPaymentTracking.objects.filter(project_id=project_id).aggregate(
        project_cost_approved_budget=Coalesce(Sum("approved_budget"), Decimal("0.00")),
        payout=Coalesce(Sum("payout"), Decimal("0.00")),
        retention=Coalesce(Sum("retention_amount"), Decimal("0.00")),
        penalty=Coalesce(Sum("penalty_amount"), Decimal("0.00")),
    )

    # Actuals = payout + retention - penalty
    project_cost_actuals = (
        pay_aggs["payout"] + pay_aggs["retention"] - pay_aggs["penalty"]
    )

    # Pending
    pending = est_aggs["estimated_approved"] - project_cost_actuals

    # Profit / Loss
    if pending >= 0:
        profit = pending
        loss = Decimal("0.00")
    else:
        profit = Decimal("0.00")
        loss = abs(pending)

    # Warning
    warning = None
    if project_cost_actuals > est_aggs["estimated_approved"]:
        warning = (
            f"Project cost exceeds approved estimate by "
            f"{project_cost_actuals - est_aggs['estimated_approved']:.2f}. "
            f"Consider a ChangeRequest."
        )

    return {
        "estimated_submitted": f"{est_aggs['estimated_submitted']:.2f}",
        "estimated_approved": f"{est_aggs['estimated_approved']:.2f}",
        "project_cost_approved_budget": f"{pay_aggs['project_cost_approved_budget']:.2f}",
        "project_cost_actuals": f"{project_cost_actuals:.2f}",
        "payout": f"{pay_aggs['payout']:.2f}",
        "pending": f"{pending:.2f}",
        "profit": float(profit),
        "loss": float(loss),
        "warning": warning,
    }
class BudgetMonitorService:
    WARNING_THRESHOLD = Decimal("0.80")  # 80%
    ESCALATION_THRESHOLD = Decimal("1.00")  # 100%

    @classmethod
    def _sum_estimations(cls, project):
        """Sum approved estimations using total_amount."""
        estimations = ProjectEstimation.objects.filter(project=project, is_approved=True)
        total = Decimal("0.00")
        for e in estimations:
            total += (e.total_amount or Decimal("0.00"))
        return total

    @classmethod
    def monitor_project(cls, project):
        """
        Aggregate actuals, holds, retention, penalties and compare with estimations.
        Create CRs if needed and send notifications.
        Returns summary dict.
        """
        # ✅ baseline estimation
        total_est_approved = cls._sum_estimations(project)

        payments_qs = ProjectPaymentTracking.objects.filter(project=project)

        # ✅ Safe expression for available budget
        budget_expr = ExpressionWrapper(
            F("approved_budget") + F("additional_amount"),
            output_field=DecimalField(max_digits=15, decimal_places=2),
        )

        aggs = payments_qs.aggregate(
            total_payout=Coalesce(
                Sum("payout", output_field=DecimalField(max_digits=15, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
            total_retention=Coalesce(
                Sum("retention_amount", output_field=DecimalField(max_digits=15, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
            total_penalty=Coalesce(
                Sum("penalty_amount", output_field=DecimalField(max_digits=15, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
            total_available_budget=Coalesce(
                Sum(budget_expr, output_field=DecimalField(max_digits=15, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
        )

        total_payout = aggs.get("total_payout") or Decimal("0.00")
        total_retention = aggs.get("total_retention") or Decimal("0.00")
        total_penalty = aggs.get("total_penalty") or Decimal("0.00")
        total_available_budget = aggs.get("total_available_budget") or Decimal("0.00")

        # ✅ Holds
        total_holds = payments_qs.aggregate(
            total=Coalesce(
                Sum("holds__amount", output_field=DecimalField(max_digits=15, decimal_places=2)),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=15, decimal_places=2)),
            )
        ).get("total") or Decimal("0.00")

        total_actuals = (total_payout + total_retention + total_holds - total_penalty)

        # ✅ Baseline: prefer approved estimation, else fallback
        baseline = total_est_approved if total_est_approved > Decimal("0.00") else total_available_budget

        if baseline == Decimal("0.00"):
            AuditLog.record(project, None, "monitor.no_baseline", {"available_budget": str(total_available_budget)})
            return {"status": "NoBaseline", "total_actuals": str(total_actuals), "baseline": str(baseline)}

        usage_ratio = (total_actuals / baseline) if baseline else Decimal("0.00")

        status = "Normal"
        if usage_ratio >= cls.ESCALATION_THRESHOLD:
            status = "Over Budget"
        elif usage_ratio >= cls.WARNING_THRESHOLD:
            status = "At Risk"

        AuditLog.record(project, None, "monitor.status", {"status": status, "ratio": str(usage_ratio)})

        # ✅ Auto-create CR if Over Budget
        if status == "Over Budget":
            try:
                suggested_amount = (total_actuals - baseline).quantize(Decimal("0.01"))
                if suggested_amount > Decimal("0.00"):
                    pending_exists = ChangeRequest.objects.filter(
                        project=project,
                        status=ChangeRequest.STATUS_PENDING
                    ).exists()
                    if not pending_exists:
                        cr = ChangeRequest.objects.create(
                            project=project,
                            requested_amount=suggested_amount,
                            reason="Auto-suggested budget increase due to actuals exceeding estimation",
                            requested_by=None,
                        )
                        AuditLog.record(
                            project, None, "change_request.auto_created",
                            {"cr_id": cr.id, "requested_amount": str(suggested_amount)}
                        )
                        cls._notify_stakeholders(
                            project,
                            f"Auto CR created: {suggested_amount}",
                            f"Suggested CR #{cr.id} for project {getattr(project, 'project_name', str(project.id))}"
                        )
            except Exception as e:
                AuditLog.record(project, None, "monitor.error", {"error": str(e)})

        if status == "At Risk":
            cls._notify_stakeholders(
                project,
                "Budget Warning",
                f"Project near budget threshold ({(usage_ratio * Decimal('100')).quantize(Decimal('0.01'))}%)"
            )

        return {
            "status": status,
            "usage_ratio": str(usage_ratio),
            "total_actuals": str(total_actuals),
            "baseline": str(baseline),
        }

    @classmethod
    def _notify_stakeholders(cls, project, title, body):
        recipients = []
        pm = getattr(project, "project_manager", None)
        acct = getattr(project, "accountant", None)
        if pm and getattr(pm, "user", None):
            recipients.append(pm.user)
        if acct and getattr(acct, "user", None):
            recipients.append(acct.user)

        if not recipients:
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            recipients = list(UserModel.objects.filter(is_staff=True)[:5])

        for user in recipients:
            try:
                Notification.objects.create(user=user, project=project, title=title, body=body)
            except Exception as e:
                AuditLog.record(project, None, "notify.error", {"error": str(e)})



def validate_payment_against_policy(project, approved_budget, user=None):
    """
    Validate if a new payment can be created for the project
    based on existing payouts, milestones, and company rules.
    """

    # Query all payments for this project
    payments_qs = project.payments.all()

    # ✅ Calculate total payout safely with Decimal
    total_payout = payments_qs.aggregate(
        total=Coalesce(Sum("payout"), Value(Decimal("0.00")), output_field=DecimalField())
    )["total"] or Decimal("0.00")

    # ✅ Calculate total approved budget safely with Decimal
    total_approved_budget = payments_qs.aggregate(
        total=Coalesce(Sum("approved_budget"), Value(Decimal("0.00")), output_field=DecimalField())
    )["total"] or Decimal("0.00")

    # Validation logic
    max_allowed_budget = Decimal("1000000.00")  # Example company rule
    adjusted_amount = min(Decimal(approved_budget), max_allowed_budget - total_approved_budget)

    allowed = adjusted_amount > 0

    if not allowed:
        message = "Cannot approve payment: exceeds allowed project budget."
    elif adjusted_amount < Decimal(approved_budget):
        message = f"Approved amount adjusted to {adjusted_amount} due to project limits."
    else:
        message = "Payment allowed."

    return {
        "allowed": allowed,
        "adjusted_amount": adjusted_amount,
        "message": message,
        "total_payout": total_payout,
        "total_approved_budget": total_approved_budget,
    }
