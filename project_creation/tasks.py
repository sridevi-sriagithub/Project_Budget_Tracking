# project/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_project_status_email(project_name, old_status, new_status, recipients):
    subject = f'Project "{project_name}" Status Updated'
    message = f'The project "{project_name}" status has changed from "{old_status}" to "{new_status}".'
    send_mail(
        subject,
        message,
        from_email=settings.EMAIL_HOST_USER, # Replace with your email
        recipient_list=recipients,
        fail_silently=False,
    )
