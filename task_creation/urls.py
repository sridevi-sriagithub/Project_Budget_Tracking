from django.urls import path
from .views import (TaskListCreateAPIView, TaskDetailAPIView,
                     my_tasks, ProjectTasksView,
                    TaskStatusChoicesView, TaskPriorityChoicesView)

urlpatterns = [
    path("tasks/", TaskListCreateAPIView.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetailAPIView.as_view(), name="task-detail"),
    path("my-task/", my_tasks, name="my-tasks"),
    path("project-tasks/<int:project_id>/", ProjectTasksView.as_view(), name="project-tasks"),
    path('tasks/status-choices/', TaskStatusChoicesView.as_view(), name='task-status-choices'),
    path('tasks/priority-choices/', TaskPriorityChoicesView.as_view(), name='task-priority-choices'),
]
