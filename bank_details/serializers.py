


from rest_framework import serializers
from .models import BankDetails
from organization.models import Organisation
from project_creation.models import Client
from masterdata.models import MasterData


# class BankDetailsSerializer(serializers.ModelSerializer):
#     organisation = serializers.SlugRelatedField(
#         slug_field="organisation_name", queryset=Organisation.objects.all(), required=False, allow_null=True
#     )
#     client = serializers.SlugRelatedField(
#         slug_field="Client_company", queryset=Client.objects.all(), required=False, allow_null=True
#     )
#     resource = serializers.SlugRelatedField(
#         slug_field="name_of_resource", queryset=MasterData.objects.all(), required=False, allow_null=True
#     )
#     created_by = serializers.ReadOnlyField(source='created_by.username')
#     modified_by = serializers.ReadOnlyField(source='modified_by.username')

#     class Meta:
#         model = BankDetails
#         fields = "__all__"
#         read_only_fields = ["created_by", "modified_by"]

#     def validate(self, data):
#         owners = [bool(data.get("organisation")), bool(data.get("client")), bool(data.get("resource"))]
#         if owners.count(True) != 1:
#             raise serializers.ValidationError("BankDetails must belong to exactly one of: Organisation, Client, or Resource.")
#         return data
class BankDetailsSerializer(serializers.ModelSerializer):
    organisation = serializers.SlugRelatedField(
        slug_field="organisation_name",
        queryset=Organisation.objects.all(),
        required=False, allow_null=True
    )
    client = serializers.SlugRelatedField(
        slug_field="Client_company",
        queryset=Client.objects.all(),
        required=False, allow_null=True
    )
    # resource = serializers.SlugRelatedField(
    #     slug_field="name_of_resource",
    #     queryset=MasterData.objects.all(),
    #     required=False, allow_null=True
    # )
    created_by = serializers.ReadOnlyField(source='created_by.username')
    modified_by = serializers.ReadOnlyField(source='modified_by.username')

    class Meta:
        model = BankDetails
        fields = "__all__"
        read_only_fields = ["created_by", "modified_by"]

    # def validate(self, data):
    #     owners = [bool(data.get("organisation")), bool(data.get("client"))]
    #     if owners.count(True) != 1:
    #         raise serializers.ValidationError(
    #             "BankDetails must belong to exactly one of: Organisation, Client."
    #         )
    #     return data
