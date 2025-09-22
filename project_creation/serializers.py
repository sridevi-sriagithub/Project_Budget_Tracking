

from rest_framework import serializers
from .models import Client, Project, ClientPOC
from login.models import User
from masterdata.models import MasterData
from roles.serializers import UserRoleSerializer
from .tasks import send_project_status_email
from .models import ProjectUser
import uuid 
class ClientSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)
 
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by')
 
class ClientPocSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)
 
    class Meta:
        model = ClientPOC
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by')




# class ProjectSerializer(serializers.ModelSerializer):
#     # Read-only display fields
#     organization = serializers.CharField(source='organization.organisation_name', read_only=True)
#     client_company = serializers.CharField(source='client.Client_company', read_only=True)
#     client_name = serializers.CharField(source='client.client_name', read_only=True)
#     poc_name = serializers.CharField(source='poc.name', read_only=True)
#     accountant_name = serializers.CharField(source='accountant.user.username', read_only=True)
#     project_manager_name = serializers.CharField(source='project_manager.user.username', read_only=True)
#     organization_name = serializers.CharField(source='organization.organisation_name', read_only=True)
#     created_by_name = serializers.CharField(source='created_by.username', read_only=True)
#     modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)
#     project_manager = serializers.SerializerMethodField()
#     accountant = serializers.SerializerMethodField()
#     client = serializers.StringRelatedField()


#     class Meta:
#         model = Project
#         fields = (
#             'id', 'project_name', 'summary', 'start_date', 'end_date', 'estimated_date',
#             'priority', 'project_type', 'is_active', 'created_at', 'modified_at',''
#             'client', 'poc', 'accountant', 'project_manager', 'organization',
#             'client_company', 'client_name', 'poc_name',
#             'accountant_name', 'project_manager_name', 'organization_name',
#             'created_by_name', 'modified_by_name','project_code'
#         )
#         read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'project_code')
    
#     def get_project_manager(self, obj):
#         return obj.project_manager.user.username if obj.project_manager else None
    
#     def get_accountant(self, obj):
#         return UserRoleSerializer(obj.accountant).data if obj.accountant else None

#     # Validate summary length and dates
#     def validate_summary(self, value):
#         if len(value) < 10:
#             raise serializers.ValidationError("Summary must be at least 10 characters long.")
#         return value

#     # Validate project_name uniqueness (case-insensitive)
#     def validate_project_name(self, value):
#         value = value.strip()
#         qs = Project.objects.filter(project_name__iexact=value)
#         if self.instance:
#             qs = qs.exclude(pk=self.instance.pk)
#         if qs.exists():
#             raise serializers.ValidationError("Project name already exists.")
#         return value

#     # Validate POC, end_date, estimated_date
#     def validate(self, attrs):
#         start_date = attrs.get('start_date')
#         end_date = attrs.get('end_date')
#         estimated_date = attrs.get('estimated_date')
#         client = attrs.get('client')
#         poc = attrs.get('poc')

#         if poc and client and poc.client != client:
#             raise serializers.ValidationError("POC must belong to the same client as the project.")

#         if end_date and start_date and end_date < start_date:
#             raise serializers.ValidationError("End date cannot be earlier than start date.")

#         if estimated_date and start_date and estimated_date < start_date:
#             raise serializers.ValidationError("Estimated date cannot be before start date.")

#         return attrs
    
#     def update(self, instance, validated_data):
#         old_status = instance.status
#         instance = super().update(instance, validated_data)  # Updates fields

#         # Check if status changed
#         if old_status != instance.status:
#             recipients = []

#             if instance.project_manager and instance.project_manager.user and instance.project_manager.user.email:
#                 recipients.append(instance.project_manager.user.email)

#             admins = User.objects.filter(is_superuser=True).values_list('email', flat=True)
#             recipients.extend(admins)

#             recipients = list(filter(None, set(recipients)))

#             if recipients:
#                 send_project_status_email(
#                     instance.project_name,
#                     old_status,
#                     instance.status,
#                     recipients
#                 )
#         return instance
#     def create(self, validated_data):
#         # Auto-generate project code
#         validated_data['project_code'] = f"PROJ-{uuid.uuid4().hex[:6].upper()}"
#         return super().create(validated_data)

class ProjectSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source='client.client_company', read_only=True)
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    poc_name = serializers.CharField(source='poc.name', read_only=True)
    accountant_name = serializers.CharField(source='accountant.user.username', read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.user.username', read_only=True)
    organization_name = serializers.CharField(source='organization.organisation_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 'project_name', 'summary', 'start_date', 'end_date', 'estimated_date',
            'priority', 'project_type', 'is_active', 'created_at', 'modified_at',
            'client', 'poc', 'accountant', 'project_manager', 'organization',
            'client_company', 'client_name', 'poc_name',
            'accountant_name', 'project_manager_name', 'organization_name',
            'created_by_name', 'modified_by_name', 'project_code'
        )
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'project_code')

    def create(self, validated_data):
        validated_data['project_code'] = f"PROJ-{uuid.uuid4().hex[:6].upper()}"
        return super().create(validated_data)




# class ProjectCreationSerializer(serializers.ModelSerializer):
    
#     # organization = OrganisationSerializer(read_only=True)
#     organization = serializers.CharField(source='organization.organisation_name', read_only=True)
#     accountant = serializers.SerializerMethodField()

#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     client = serializers.StringRelatedField()
#     client_name = serializers.CharField(source="client.name", read_only=True)
    
#     # project_manager_details = UserRoleSerializer(source="project_manager", read_only=True)
#     project_manager = serializers.SerializerMethodField()
#     def get_project_manager(self, obj):
#         return obj.project_manager.user.username if obj.project_manager else None
    
#     def get_accountant(self, obj):
#         return UserRoleSerializer(obj.accountant).data if obj.accountant else None
#     class Meta:
#         model = Project
#         fields = [
#             'id',
#             'project_code',
#             'summary',
#             'client',
#             'client_name',
#             'project_manager',
#             'accountant',
#             'start_date',
#             'end_date',
#             'estimated_date',
#             'priority',
#             'status',
#             'status_display',
#             'organization',
#             'project_type',
#             'is_active',
#             'project_name',
        
#         ]
#     def get_project_manager(self, obj):
#         return obj.project_manager.user.username if obj.project_manager else None
    
#     def get_accountant(self, obj):
#         return UserRoleSerializer(obj.accountant).data if obj.accountant else None
    
#     def update(self, instance, validated_data):
#         old_status = instance.status
#         instance = super().update(instance, validated_data)  # Updates fields

#         # Check if status changed
#         if old_status != instance.status:
#             recipients = []

#             if instance.project_manager and instance.project_manager.user and instance.project_manager.user.email:
#                 recipients.append(instance.project_manager.user.email)

#             admins = User.objects.filter(is_superuser=True).values_list('email', flat=True)
#             recipients.extend(admins)

#             recipients = list(filter(None, set(recipients)))

#             if recipients:
#                 send_project_status_email(
#                     instance.project_name,
#                     old_status,
#                     instance.status,
#                     recipients
#                 )
#         return instance
    


class ProjectUserSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), write_only=True
    )
    project_details = serializers.SerializerMethodField(read_only=True)
    
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    user_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectUser
        fields = ['project', 'user', 'assigned_at', 'project_details', 'user_details']

    def get_project_details(self, obj):
        return {
            "name": obj.project.project_name
        }

    # def get_user_details(self, obj):
    #     module_name = None
    #     try:
    #         master_data = MasterData.objects.filter(name_of_resource=obj.user).first()
    #         module_name = master_data.category.category_name if master_data and master_data.category else None
    #     except Exception:
    #          module_name = None
    #     return {
    #         "username": obj.user.username,
    #         "email": obj.user.email,
    #         "module": module_name
    #     }
    def get_user_details(self, obj):
        try:
            module_name = None
            master_data = MasterData.objects.filter(name_of_resource=obj.user).first()
            if master_data:
                module_name = getattr(getattr(master_data, 'category', None), 'category_name', None)

            return {
                "username": getattr(obj.user, "username", None),
                "email": getattr(obj.user, "email", None),
                "module": module_name
            }
        except Exception as e:
            print("Error in get_user_details:", str(e))
            return {
                "username": getattr(obj.user, "username", None),
                "email": getattr(obj.user, "email", None),
                "module": None
            }


