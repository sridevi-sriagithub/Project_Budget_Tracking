# utils.py
def get_status_choices():
    from .models import Task
    return [key for key, _ in Task.STATUS_CHOICES]

def get_priority_choices():
    from .models import Task
    return [key for key, _ in Task.PRIORITY_CHOICES]
