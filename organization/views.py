
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organisation
from .serializers import OrganisationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from roles.permissions import HasRolePermission



import logging

logger = logging.getLogger(__name__)

class OrganisationAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
   
    
    def get(self, request, organisation_id=None):
        # self.permission_required = "view_organization"
    
        # if not HasRolePermission().has_permission(request, self.permission_required):
        #  return Response({'error': 'Permission denied.'}, status=403)
        print("done")

        logger.info("OrganizationList view was called")
       
        if organisation_id:
            try:
                organisation = Organisation.objects.get(organisation_id=organisation_id)
                serializer = OrganisationSerializer(organisation)
                return Response(serializer.data)
            except Organisation.DoesNotExist:
                return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            organisations = Organisation.objects.all()
            serializer = OrganisationSerializer(organisations, many=True)
            return Response(serializer.data)
        
    
    

    # POST: Create a new organisation 
    def post(self, request):
        # self.permission_required = "create_organization"
    
        # if not HasRolePermission().has_permission(request, self.permission_required):
        #  return Response({'error': 'Permission denied.'}, status=403)

       
        serializer = OrganisationSerializer(data=request.data)
        if serializer.is_valid():
            organisation = serializer.save(created_by=request.user)
            # send_organisation_creation_email.delay(
            #     organisation.organisation_name,
            #     organisation.organisation_mail
            # )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT: Update an existing organisation
    def put(self, request, organisation_id=None):
        # self.permission_required = "update_organization"
    
        # if not HasRolePermission().has_permission(request, self.permission_required):
        #  return Response({'error': 'Permission denied.'}, status=403)
        try:
            organisation = Organisation.objects.get(organisation_id=organisation_id)
        except Organisation.DoesNotExist:


            
            return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrganisationSerializer(organisation, data=request.data)
        if serializer.is_valid():
            organisation = serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Delete an organisation
    def delete(self, request, organisation_id=None):
        # self.permission_required = "delete_organization"
    
        # if not HasRolePermission().has_permission(request, self.permission_required):
        #  return Response({'error': 'Permission denied.'}, status=403)
        try:
            organisation = Organisation.objects.get(organisation_id=organisation_id)
            organisation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Organisation.DoesNotExist:
            return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
        
