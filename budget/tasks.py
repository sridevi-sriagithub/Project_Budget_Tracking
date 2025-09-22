from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from decimal import Decimal
from .models import Project, ProjectEstimation, ProjectPaymentTracking

@shared_task(bind=True, max_retries=3)
def send_email_async(self, subject, message, recipients, from_email=None):
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        if isinstance(recipients, str):
            recipients = [recipients]
        # simple text email
        EmailMultiAlternatives(subject, message, from_email, recipients).send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)

@shared_task(bind=True, max_retries=3)
def send_html_email_async(self, subject, text_body, html_body, recipients, from_email=None):
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        if isinstance(recipients, str):
            recipients = [recipients]
        msg = EmailMultiAlternatives(subject, text_body, from_email, recipients)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task
def recalculate_project_finances(project_id):
    try:
        project = Project.objects.get(id=project_id)
        estimation = ProjectEstimation.objects.filter(project=project).last()
        payments = ProjectPaymentTracking.objects.filter(project=project)

        approved_budget = getattr(estimation, "total_amount", Decimal("0.00"))
        actuals = sum(Decimal(p.approved_budget or 0) for p in payments)
        payout = sum(Decimal(p.payout or 0) for p in payments)
        pending = approved_budget - payout

        profit_loss = payout - actuals

        project.last_recalculated_at = now()
        project.profit_loss = profit_loss
        project.pending_amount = pending
        project.save(update_fields=["last_recalculated_at", "profit_loss", "pending_amount"])

        return f"Project {project.id} recalculated successfully."
    except Project.DoesNotExist:
        return f"Project {project_id} does not exist."
    except Exception as e:
        return f"Error in recalculate_project_finances: {e}"

@shared_task
def send_budget_alerts(project_id):
    try:
        project = Project.objects.get(id=project_id)
        estimation = ProjectEstimation.objects.filter(project=project).last()
        payments = ProjectPaymentTracking.objects.filter(project=project)

        if not estimation:
            return f"No estimation found for project {project_id}"

        approved_budget = getattr(estimation, "total_amount", Decimal("0.00"))
        actuals = sum(Decimal(p.approved_budget or 0) for p in payments)

        message = None
        if actuals >= approved_budget * Decimal("0.9") and actuals < approved_budget:
            message = f"⚠️ Warning: Project {project.project_name} has reached 90% of approved budget."
        elif actuals >= approved_budget:
            message = f"🚨 Alert: Project {project.project_name} has EXCEEDED the approved budget!"

        if message:
            try:
                send_mail(
                    subject=f"Budget Alert for Project {project.project_name}",
                    message=message,
                    from_email="noreply@yourapp.com",
                    recipient_list=["finance-team@yourcompany.com"],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Email send failed: {e}")
            return message
        return f"Project {project_id} is within budget."
    except Project.DoesNotExist:
        return f"Project {project_id} does not exist."
    except Exception as e:
        return f"Error in send_budget_alerts: {e}"
