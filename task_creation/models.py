from django.db import models
from django.conf import settings
from login.models import User




class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        # ('blocked', 'Blocked'),
        ('in_review', 'In Review'),
        ('on_hold', 'On Hold'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    task_id = models.AutoField(primary_key=True)
    project = models.ForeignKey("project_creation.Project", on_delete=models.SET_NULL, related_name="tasks", null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey("login.User", on_delete=models.SET_NULL, null=True, related_name="assigned_tasks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    # Add other fields...
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey("login.User", on_delete=models.SET_NULL, null=True, related_name="created_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


# def get_status_choices():
#     return TaskStatus.choices

# def get_priority_choices():
#     return TaskPriority.choices