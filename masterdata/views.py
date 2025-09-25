from django.shortcuts import render

# Create your views here.
from .serializers import ModuleSerializer, MasterDataSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, MasterData
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated 
from login.models import User
from roles.models import UserRole
    
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
    


 # Disable authentication for this view
 

    # def get(self, request, pk=None):
    #     user = request.user
    #     if pk:
    #         try:
    #             resource = MasterData.objects.get(id=pk, created_by=user)
    #             serializer = MasterDataSerializer(resource)
    #             return Response(serializer.data)
    #         except MasterData.DoesNotExist:
    #             return Response({"error": "Resource not found"}, status=404)
    #     else:
    #         resources = MasterData.objects.filter(created_by=user)
    #         serializer = MasterDataSerializer(resources, many=True)
    #         return Response(serializer.data)
    # def get(self, request, pk=None, user_id=None):
    #     """
    #     - If `pk` is passed -> return single master data record.
    #     - If `user_id` is passed -> return all master data of that user.
    #     - Else -> return logged-in user's master data.
    #     """
    #     logged_in_user = request.user

    #     if pk:  # Fetch single record of logged-in user
    #         try:
    #             resource = MasterData.objects.get(id=pk, created_by=logged_in_user)
    #             serializer = MasterDataSerializer(resource)
    #             return Response(serializer.data)
    #         except MasterData.DoesNotExist:
    #             return Response({"error": "Resource not found"}, status=404)

    #     if user_id:  # Fetch another user's master data
    #         try:
    #             target_user = User.objects.get(id=user_id)
    #         except User.DoesNotExist:
    #             return Response({"error": "User not found"}, status=404)

    #         resources = MasterData.objects.filter(created_by=target_user)
    #         serializer = MasterDataSerializer(resources, many=True)
    #         return Response(serializer.data)

    #     # Default -> show logged-in user's master data
    #     resources = MasterData.objects.filter(created_by=logged_in_user)
    #     serializer = MasterDataSerializer(resources, many=True)
    #     return Response(serializer.data)
   # utils.py or in the same views.py
# adjust import path if needed
def is_admin_user(user):
    """Check if user is superuser or has 'Admin' role."""
    if user.is_superuser:
        return True
    return UserRole.objects.filter(user=user, role__name="Admin", is_active=True).exists()


class MasterDataView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk=None, user_id=None):
        """
        - If `pk` is passed -> return single master data record.
        - If `user_id` is passed -> return all master data of that user.
        - If logged-in user is superuser or Admin role -> return all master data.
        - Else -> return logged-in user's master data.
        """
        logged_in_user = request.user

        # If pk is passed (fetch single record)
        if pk:
            try:
                if is_admin_user(logged_in_user):
                    resource = MasterData.objects.get(id=pk)
                else:
                    resource = MasterData.objects.get(id=pk, created_by=logged_in_user)

                serializer = MasterDataSerializer(resource)
                return Response(serializer.data)
            except MasterData.DoesNotExist:
                return Response({"error": "Resource not found"}, status=404)

        # If user_id is passed (fetch specific user’s records)
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)

            # Admins can view any user's data
            if is_admin_user(logged_in_user):
                resources = MasterData.objects.filter(created_by=target_user)
            else:
                # Normal users can only see their own
                if target_user != logged_in_user:
                    return Response({"error": "Not authorized"}, status=403)
                resources = MasterData.objects.filter(created_by=logged_in_user)

            serializer = MasterDataSerializer(resources, many=True)
            return Response(serializer.data)

        # If admin (superuser or role=Admin) -> return all records
        if is_admin_user(logged_in_user):
            resources = MasterData.objects.all()
            serializer = MasterDataSerializer(resources, many=True)
            return Response(serializer.data)

        # Default -> return only logged-in user’s records
        resources = MasterData.objects.filter(created_by=logged_in_user)
        serializer = MasterDataSerializer(resources, many=True)
        return Response(serializer.data)


            

    def post(self, request):
        try:
            data = request.data.copy()
            data['name_of_resource'] = request.user.id  # Assign logged-in user
            
            serializer = MasterDataSerializer(data=data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating MasterData: {str(e)}")
            
            return Response({
                'error': 'Internal server error',
                'message': str(e)  # Remove this in production
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    # def post(self, request):
    #     serializer = MasterDataSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save(created_by=request.user)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request, pk=None):
    #     user = request.user  # logged-in user
    #     if pk:
    #         try:
    #             resource = MasterData.objects.get(id=pk, created_by=user)
    #             serializer = MasterDataSerializer(resource)
    #             return Response(serializer.data)
    #         except MasterData.DoesNotExist:
    #             return Response({"error": "Resource not found"}, status=404)
    #     else:
    #         resources = MasterData.objects.filter(created_by=user)
    #         serializer = MasterDataSerializer(resources, many=True)
    #         return Response(serializer.data)
   
        
    # def post(self, request):
    #     serializer = MasterDataSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save(created_by=request.user)  # save with current user
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
            
class ALLAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Allow unrestricted access    
    authentication_classes = [JWTAuthentication]  # Disable authentication for this view
    def get(self, request):
        resources = MasterData.objects.all()
        serializer = MasterDataSerializer(resources, many=True)
        return Response(serializer.data)
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