from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

def send_registration_email_sync(user_id, raw_password):
    """Send registration email synchronously (fallback if Celery fails)."""
    try:
        user = User.objects.get(id=user_id)
        subject = "Welcome to Project Tracker!"
        message = (
            f"Hello {user.username},\n\n"
            f"Your account has been created.\nEmail: {user.email}\n"
            f"Password: {raw_password}\n\n"
            "Please log in and change your password."
        )

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        logger.info(f"Synchronous email sent successfully to {user.email}")

    except Exception as e:
        logger.error(f"Sync fallback email failed: {e}")

