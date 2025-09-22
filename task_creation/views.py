from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Task
from .serializers import TaskSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .tasks import send_task_assignment_email , send_overdue_task_emails
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from project_creation.models import Project 
# from task_creation .models import get_status_choices, get_priority_choices


class TaskListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    """
    GET: List all tasks
    POST: Create a new task
    """
    def get(self, request):

        my_tasks = request.query_params.get('my_tasks')
    
        if my_tasks == 'true':
            tasks = Task.objects.filter(assigned_to=request.user)
        else:
            tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def post(self, request):
    #     serializer = TaskSerializer(data=request.data)
    #     if serializer.is_valid():
    #         # Save task and get the created instance
    #         task = serializer.save(created_by=request.user)  

    #         # Check if assigned_to exists and send email
    #         if task.assigned_to and task.assigned_to.email:
    #             subject = f"New Task Assigned: {task.title}"
    #             message = (
    #                 f"Hi {task.assigned_to.username},\n\n"
    #                 f"You have been assigned a new task:\n"
    #                 f"Title: {task.title}\n"
    #                 f"Description: {task.description or 'No description'}\n"
    #                 f"Due Date: {task.due_date or 'Not set'}\n\n"
    #                 f"Please check your dashboard for more details."
    #             )
    #             # Send email using Celery task
    #             send_task_assignment_email(subject, message, task.assigned_to.email)

    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # views.py


    # views.py
# from datetime import timedelta

    # def post(self, request):
    #     serializer = TaskSerializer(data=request.data)
    #     if serializer.is_valid():
    #         # Save the new task
    #         task = serializer.save(created_by=request.user)

    #         # ✅ Call task assignment email if assigned_to exists
    #         if task.assigned_to and task.assigned_to:
    #             send_task_assignment_email(task.title, task.description, task.assigned_to)

    #         # ✅ Call overdue email check (if due_date exists)
    #         if task.due_date:
    #             send_overdue_task_emails()

    #         return Response(serializer.data, status=status.HTTP_201_CREATED)

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # class TaskCreateAPIView(APIView):
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)
            send_task_assignment_email(task.task_id)

            # ✅ Use Celery task instead of hardcoding send_mail
            
        
        
            #     subject=f"New Task Assigned: {task.title}",
            #     message=f"You have been assigned a new task: {task.title}",
            #     recipient_email=task.assigned_to.email
            # )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def my_tasks(request):
    email = request.query_params.get('assigned_to')
    tasks = Task.objects.all()

    if email:
        tasks = tasks.filter(assigned_to__email__iexact=email)
    else:
        tasks = tasks.filter(assigned_to=request.user)

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)
class TaskDetailAPIView(APIView):
    """
    GET: Retrieve a task
    PUT/PATCH: Update a task
    DELETE: Delete a task
    """
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def put(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)  # track modifier
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.delete()
        return Response({"message": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



class ProjectTasksView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        tasks = Task.objects.filter(project=project)  # ✅ FIXED
        serializer = TaskSerializer(tasks, many=True)
        return Response({
            "project": project.project_name,
            "tasks": serializer.data
        }, status=status.HTTP_200_OK)
    

from .utils import get_status_choices, get_priority_choices


class TaskStatusChoicesView(APIView):
    def get(self, request):
        return Response({"status_choices": get_status_choices()})


class TaskPriorityChoicesView(APIView):
    def get(self, request):
        return Response({"priority_choices": get_priority_choices()})