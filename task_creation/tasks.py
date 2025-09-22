# tasks/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings  # ✅ Import settings to use EMAIL_HOST_USER
from .models import Task
from django.utils.timezone import now
# @shared_task
# def send_task_assignment_email(subject, message, recipient_email):
#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.EMAIL_HOST_USER,  # 🔥 Use email from settings
#         recipient_list=[recipient_email],
#         fail_silently=False,
#     )
@shared_task
def send_task_assignment_email(task_id):
   
    task = Task.objects.get(pk=task_id)

    subject = f"Task Assigned: {task.title}"
    message = f"""
    Hello {task.assigned_to.username},

    A new task has been created and assigned to you.

    Task Details:
    - Title: {task.title}
    - Description: {task.description}
    - Due Date: {task.due_date}

    Please login to the system to view more details.
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[task.assigned_to.email],
        fail_silently=False,
    )


# @shared_task
# def send_overdue_task_emails():
   
#     overdue_tasks = Task.objects.filter(due_date__lt=now().date()).exclude(status="done")

#     for task in overdue_tasks:
#         if task.assigned_to and task.assigned_to.email:  # ✅ Check if assigned_to exists
#             send_mail(
#                 subject=f'Task Overdue: {task.title}',
#                 message=f'The task "{task.title}" is overdue. Please take action.',
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=[task.assigned_to.email],
#                 fail_silently=False,
#             )

# tasks.py
from celery import shared_task
from django.utils.timezone import now
from django.core.mail import send_mail
from .models import Task

# @shared_task
# def send_overdue_task_emails():
#     overdue_tasks = Task.objects.filter(due_date__lt=now(), status__in=["In Progress"])
#     for task in overdue_tasks:
#         send_mail(
#             subject=f"Overdue Task: {task.title}",
#             message=f"The task '{task.title}' is overdue. Please check.",
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[task.assigned_to.email],
#         )


@shared_task
def send_overdue_task_emails():
    print("✅ Running overdue task email job...")

    overdue_tasks = Task.objects.filter(due_date__lt=now(), status__in=["in_progress", "in_review"])
    print(f"🔍 Found {overdue_tasks.count()} overdue tasks")

    if not overdue_tasks.exists():
        print("ℹ️ No overdue tasks found.")
        return

    for task in overdue_tasks:
        recipient = getattr(task.assigned_to, "email", None)
        if not recipient:
            print(f"⚠️ No email for assigned user of task: {task.title}")
            continue

        try:
            send_mail(
                subject=f"Overdue Task: {task.title}",
                message=f"The task '{task.title}' is overdue. Please check.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient],
                fail_silently=False
            )
            print(f"✅ Email sent to {recipient} for task: {task.title}")
        except Exception as e:
            print(f"❌ Failed to send email for task {task.title}: {e}")