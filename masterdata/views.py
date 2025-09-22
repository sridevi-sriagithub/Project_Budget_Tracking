from django.shortcuts import render

# Create your views here.
from .serializers import ModuleSerializer, MasterDataSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, MasterData
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated 

    
class CategoryView(APIView):
    permission_classes = [IsAuthenticated]  # Allow unrestricted access
    authentication_classes = [JWTAuthentication]  # Disable authentication for this view
    def get(self, request, category_id=None):
        if category_id:
            try:
                module = Category.objects.get(category_id=category_id)
                serializer = ModuleSerializer(module)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Category.DoesNotExist:
                return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            modules = Category.objects.all()
            serializer = ModuleSerializer(modules, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    
    def post(self, request):
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, category_id):
        try:
            module = Category.objects.get(category_id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModuleSerializer(module, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, category_id):
        try:
            module = Category.objects.get(category_id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

        module.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class MasterDataView(APIView):
    permission_classes = [IsAuthenticated]  # Allow unrestricted access    
    authentication_classes = [JWTAuthentication]  # Disable authentication for this view
    # def get(self,request, pk=None):
    #     if pk:
    #         try:
    #             resource = MasterData.objects.get(id=pk)
    #             serializer = MasterDataSerializer(resource)
    #             return Response(serializer.data)
    #         except MasterData.DoesNotExist:
    #             return Response({"error": "Resource not found"}, status=404)
    #     else:
    #         resources = MasterData.objects.all()
    #         serializer = MasterDataSerializer(resources, many=True)
    #         return Response(serializer.data)
    # def get(self, request, pk=None):
    #     if pk:
    #         try:
    #             resource = MasterData.objects.get(id=pk, created_by=request.user)
    #             serializer = MasterDataSerializer(resource)
    #             return Response(serializer.data)
    #         except MasterData.DoesNotExist:
    #             return Response({"error": "Resource not found"}, status=404)
    #     else:
    #         resources = MasterData.objects.filter(created_by=request.user)
    #         serializer = MasterDataSerializer(resources, many=True)
    #         return Response(serializer.data)
    def get(self, request, pk=None):
        user = request.user  # logged-in user
        if pk:
            try:
                resource = MasterData.objects.get(id=pk, created_by=user)
                serializer = MasterDataSerializer(resource)
                return Response(serializer.data)
            except MasterData.DoesNotExist:
                return Response({"error": "Resource not found"}, status=404)
        else:
            resources = MasterData.objects.filter(created_by=user)
            serializer = MasterDataSerializer(resources, many=True)
            return Response(serializer.data)
        
    def post(self, request):
        serializer = MasterDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # save with current user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk): 
        try:
            resource = MasterData.objects.get(id=pk)
        except MasterData.DoesNotExist:
            return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MasterDataSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            resource = MasterData.objects.get(id=pk)
        except MasterData.DoesNotExist:
            return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
from login.serializers import UserSerializer
class ModuleUsersView(APIView):
    def get(self, request, category_id):
        master_records = MasterData.objects.filter(category_id=category_id).select_related("name_of_resource")
        users = [record.name_of_resource for record in master_records if record.name_of_resource]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
from .serializers import ProfileSerializer
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes  = [JWTAuthentication]
    # permission_classes = [AllowAny]

    def get(self, request):
        """Get logged-in user's profile"""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class ResourceTypeAPIView(APIView):
    def get(self, request):
        values = [value for key, value in MasterData.RESOURCE_TYPE_CHOICES]
        return Response(values)

class WorkTypeAPIView(APIView):
    def get(self, request):
        values = [value for key, value in MasterData.WORK_TYPE_CHOICES]
        return Response(values)