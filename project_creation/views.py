from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED,HTTP_400_BAD_REQUEST
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Client, Project,ClientPOC
from .serializers import ClientSerializer, ProjectSerializer, ClientPocSerializer
from django.db import IntegrityError
# Create your views here.

class ClientListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        serializer = ClientSerializer(client)
        return Response(serializer.data)

    def put(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        serializer = ClientSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.delete()
        return Response({"message": "Client deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    

class ClientPocCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        clients = ClientPOC.objects.all()
        serializer = ClientPocSerializer(clients, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClientPocSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientPocDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, pk):
        client = get_object_or_404(ClientPOC, pk=pk)
        serializer = ClientPocSerializer(client)
        return Response(serializer.data)

    def put(self, request, pk):
        client = get_object_or_404(ClientPOC, pk=pk)
        serializer = ClientPocSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        client = get_object_or_404(ClientPOC, pk=pk)
        client.delete()
        return Response({"message": "Client deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


from django.db.models import Max

class ProjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

   
 
    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Auto-generate project_code
                last_id = Project.objects.aggregate(last_id=Max('id'))['last_id'] or 0
                project_code = f"PRJ_{last_id + 1}"

                serializer.save(created_by=request.user, project_code=project_code)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response({"error": "Project name already exists."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def put(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.delete()
        return Response({"message": "Project deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



"""from tracking"""


class ProjectListCreateAPIView(APIView):
    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, Update, Delete Single Project
class ProjectDetailAPIView(APIView):
    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def put(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


from .models import Project, ProjectUser
from .utils import increment_id
from .serializers import ProjectUserSerializer
from .serializers import ProjectSerializer
class ProjectIDAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    

    def get(self, request):
        try:
            data = dict(request.GET)
            prefix = data['id'][0]   # e.g., "SRIA"
        except:
            prefix = "PR"

        # fetch all project codes
        projects = Project.objects.values_list("project_code", flat=True)

        # filter by prefix
        filtered_ids = [code for code in projects if code.startswith(prefix)]

        if not filtered_ids:
            filtered_ids.append(f"{prefix}00000")  # first project id

        last_id = sorted(filtered_ids)[-1]
        new_id = increment_id(last_id)

        return Response({"new_project_id": new_id})
    


class StatusChoicesView(APIView):
    def get(self, request):
        """
        Return a list of all status choices with their value and label.
        """
        choices = [{"value": choice.value, "label": choice.label} for choice in Project.StatusChoices]
        return Response(choices, status=status.HTTP_200_OK)

from login.models import User  
class ProjectUserAssignView(APIView):
    

    def get(self, request, project_id, *args, **kwargs):
        """Get all users assigned to a specific project"""
        project_users = ProjectUser.objects.filter(project_id=project_id)
        serializer = ProjectUserSerializer(project_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def post(self, request, project_id, *args, **kwargs):
    #     """Assign a user to a specific project"""
    #     data = request.data.copy()
    #     data["project"] = project_id
    #     serializer = ProjectUserSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # def post(self, request, project_id, *args, **kwargs):
    #     """Assign a user to a specific project"""
    #     data = request.data.copy()
    #     data["project"] = project_id
    #     serializer = ProjectUserSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save(created_by = request.user)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     print(serializer.errors)  # ✅ Add this to see why validation failed
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, project_id, *args, **kwargs):
        print("Received request data:", request.data)

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            print("Project not found with id:", project_id)
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get("user")
        if not user_id:
            print("User id not provided in request")
            return Response({"error": "User field is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print("User not found with id:", user_id)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if ProjectUser.objects.filter(project=project, user=user).exists():
            print(f"Assignment already exists: project {project.id}, user {user.id}")
            return Response({"error": "User already assigned to this project"}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "project": project.id,
            "user": user.id,
        }

        serializer = ProjectUserSerializer(data=data)
        print("Serializer is valid?", serializer.is_valid())
        print("Validation errors:", serializer.errors)

        if serializer.is_valid():
            try:
                serializer.save()
                print("Assignment saved successfully")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print("Save error:", str(e))
                return Response({"error": f"Save failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from task_creation.models import Task
from task_creation.serializers import TaskSerializer
class ProjectRelatedTasksView(APIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        queryset = Task.objects.all()
        project_id = request.query_params.get('project_id')
        status = request.query_params.get('status')
        assigned_to = request.query_params.get('assigned_to')

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if status:
            queryset = queryset.filter(status=status)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        serializer = TaskSerializer(queryset, many=True)
        return Response(serializer.data)

