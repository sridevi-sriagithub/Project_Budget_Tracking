from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __Str__(self):
        return self.email
      


# Create your models here.
class BaseModel(models.Model):
    """Abstract base with common audit fields and soft-delete support."""
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='%(class)s_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='%(class)s_modified')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self, by_user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if by_user:
            self.modified_by = by_user
        self.save()