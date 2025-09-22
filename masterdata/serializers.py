from .models import Category, MasterData
from rest_framework import serializers
from roles.models import UserRole
from login.models import User
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'category_name', 'category_description', 'created_at', 'modified_at']




class MasterDataSerializer(serializers.ModelSerializer):
    user_role_name = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.category_name', read_only=True)
    name_of_resource = serializers.CharField(source='name_of_resource.username', read_only=True)
    class Meta:
        model = MasterData
        fields = '__all__'
        extra_kwargs = {
            'category': {'required': True, 'allow_null': False},
            'name_of_resource': {'required': True, 'allow_null': False},
            'type_of_resource': {'required': True, 'allow_blank': False},
            'contact_details': {'required': True, 'allow_blank': False},
            'pan': {'required': True, 'allow_blank': False},
            'gst': {'required': True, 'allow_blank': False},
            'address': {'required': True, 'allow_blank': False},
            'work_location': {'required': True, 'allow_blank': False},
            'work_type': {'required': True, 'allow_blank': False},
            'experience': {'required': True, 'allow_blank': False},
            'skill_set': {'required': True, 'allow_blank': False},
            
        }
    def get_user_role_name(self, obj):
        user_role = UserRole.objects.filter(user=obj.name_of_resource).first()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            
        ]
        read_only_fields = ['id', 'username', 'email']