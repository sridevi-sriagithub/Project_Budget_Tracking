
from rest_framework import serializers
from .models import Organisation


 
class OrganisationSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='username')
    modified_by = serializers.SlugRelatedField(read_only=True, slug_field='username')
 
    class Meta:
        model = Organisation
        fields = [
            'organisation_id', 'organisation_name', 'organisation_mail', 'is_active',
            'created_at', 'modified_at', 'created_by', 'modified_by'
          
        ]

      
