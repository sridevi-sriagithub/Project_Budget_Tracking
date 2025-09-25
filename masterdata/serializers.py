from .models import Category, MasterData
from rest_framework import serializers
from roles.models import UserRole
from login.models import User
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'category_name', 'category_description', 'created_at', 'modified_at']

# class MasterDataSerializer(serializers.ModelSerializer):
#     user_role_name = serializers.SerializerMethodField()
#     category_name = serializers.SerializerMethodField()
#     resource_username = serializers.SerializerMethodField()

#     class Meta:
#         model = MasterData
#         fields = [
#             'id',
#             'user_role_name',
#             'first_name',
#             'last_name',
#             'name_of_resource',
#             'resource_username',
#             'category',    # new field for user.username
#             'category_name',         # new field for category.category_name
#             'type_of_resource',
#             'contact_details',
#             'pan',
#             'gst',
#             'address',
#             'work_location',
#             'work_type',
#             'experience',
#             'skill_set',
#             'created_at',
#             'modified_at',
#             'is_active',
#             'created_by',
#             'modified_by',
#         ]
#         extra_kwargs = {
#             'type_of_resource': {'required': True, 'allow_blank': False},
#             'contact_details': {'required': True, 'allow_blank': False},
#             'pan': {'required': True, 'allow_blank': False},
#             'gst': {'required': True, 'allow_blank': False},
#             'address': {'required': True, 'allow_blank': False},
#             'work_location': {'required': True, 'allow_blank': False},
#             'work_type': {'required': True, 'allow_blank': False},
#             'experience': {'required': True, 'allow_blank': False},
#             'skill_set': {'required': True, 'allow_blank': False},
#         }

#     def get_user_role_name(self, obj):
#         user_role = UserRole.objects.filter(user=obj.name_of_resource).first()
#         return user_role.role_name if user_role else None
    
 

#     def get_resource_username(self, obj):
#         if obj.name_of_resource:
#             return getattr(obj.name_of_resource, 'username', None)
#         return None

#     def get_category_name(self, obj):
#         if obj.category:
#             return getattr(obj.category, 'category_name', None)
#         return None

from rest_framework import serializers
from .models import MasterData, Category
from login.models import User
from bank_details.serializers import BankDetailsSerializer
from bank_details.models import BankDetails
class MasterDataSerializer(serializers.ModelSerializer):
    user_role_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    resource_username = serializers.SerializerMethodField()
    bank_accounts = serializers.SerializerMethodField()

    class Meta:
        model = MasterData
        fields = [
            'id',
            'user_role_name',
            'first_name',
            'last_name',
            'name_of_resource',    # FK ID
            'resource_username',   # username of the user
            'category',            # FK ID
            'category_name',       # category name
            'type_of_resource',
            'contact_details',
            'pan',
            'gst',
            'address',
            'work_location',
            'work_type',
            'experience',
            'skill_set',
            'created_at',
            'modified_at',
            'is_active',
            'created_by',
            'modified_by',
            'bank_accounts',
        ]

    def get_user_role_name(self, obj):
        if obj.name_of_resource:
            user_role = UserRole.objects.filter(user=obj.name_of_resource, is_active=True).first()
            return user_role.role.name if user_role else None
        return None

    def get_category_name(self, obj):
        return obj.category.category_name if obj.category else None

    def get_resource_username(self, obj):
        # Fixed: use name_of_resource instead of user
        return obj.name_of_resource.username if obj.name_of_resource else None
    
    def get_bank_accounts(self, obj):
       
        # filter bank accounts created by the same user as resource
        bank_accounts = BankDetails.objects.filter(created_by=obj.name_of_resource, is_active=True)
        return BankDetailsSerializer(bank_accounts, many=True).data



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            
        ]
        read_only_fields = ['id', 'username', 'email']