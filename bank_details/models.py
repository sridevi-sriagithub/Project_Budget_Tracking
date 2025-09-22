from django.db import models
from django.core.exceptions import ValidationError
from organization.models import Organisation
from project_creation.models import Client
from masterdata.models import MasterData
from login.models import BaseModel
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from login.models import User
# Create your models here.
class BankDetails(BaseModel):
    account_holder = models.CharField(max_length=255)
    account_number = models.CharField(max_length=30, unique=True)
    ifsc_code = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

        # Owner (must be exactly ONE)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=True, related_name="bank_accounts"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, blank=True, related_name="bank_accounts"
    )
    # resource = models.ForeignKey( 
    #     MasterData, on_delete=models.CASCADE, null=True, blank=True, related_name="bank_accounts"
    # )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_bankdetails'
    )
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='modified_bankdetails'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # def clean(self):
    #     """Ensure bank account belongs to exactly ONE owner type."""
    #     owners = [bool(self.organisation), bool(self.client), bool(self.resource)]
    #     if owners.count(True) != 1:
    #         raise ValidationError("BankDetails must belong to exactly one of: Organisation, Client, or Resource.")

    # def __str__(self):
    #     owner = self.organisation or self.client or self.resource
    #     return f"{self.account_holder} - {self.bank_name} ({owner})"

