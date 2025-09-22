
from django.db import models
from django.core.exceptions import ValidationError


class Organisation(models.Model):
    organisation_id = models.BigAutoField(primary_key=True) 
    organisation_name = models.CharField(max_length=255,unique=True)  # Ensuring unique organisation name
    organisation_mail = models.EmailField(unique=True)  # Ensuring unique email
    is_active = models.BooleanField(default=True)  # Soft deletion flag
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'login.User', on_delete=models.SET_NULL, null=True, related_name='organisations_created_by'
    )
    modified_by = models.ForeignKey(
        'login.User', on_delete=models.SET_NULL, null=True, related_name='organisations_modified_by'
    )

    class Meta:
        unique_together = ('organisation_name', 'organisation_mail')

    def __str__(self):
        return self.organisation_name
  




