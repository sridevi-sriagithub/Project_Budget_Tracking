from django.db import models
from login.models import User
from django.utils import timezone
# Create your models here.
class Category(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_name = models.CharField(max_length=255, unique=True)
    category_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name
    

class MasterData(models.Model):
    RESOURCE_TYPE_CHOICES = [
    ('Freelance', 'Freelance'),                
    ('Full Time', 'Full Time'),                
    ('Part Time', 'Part Time'),                 
    ('Contract', 'Contract'),                  
    ('Intern', 'Intern'),                      
    ('Consultant', 'Consultant'),               
    ('Temporary', 'Temporary'),                 
    ('Vendor', 'Vendor'),                       
    ('Outsourced', 'Outsourced'),               
    ('Apprentice', 'Apprentice'),               
    ('Other', 'Other'),                    
]
    
    WORK_TYPE_CHOICES = [
    ("On-site", "On-site"),                
    ("Remote", "Remote"),                   
    ("Hybrid", "Hybrid"),                   
    ("Shift-based", "Shift-based"),         
    ("Field Work", "Field Work"),           
    ("Project-based", "Project-based"),     # Works only for the duration of a project
    ("On-call", "On-call"),                 # Works when needed, flexible hours
    ("Travel-intensive", "Travel-intensive"),
    ("Flexible Hours", "Flexible Hours"),  
    ("Training", "Training"),              
]

    
    # module = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='master_data')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    name_of_resource = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_data', null=True, blank=True)
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category", null=True, blank=True)
    
    type_of_resource = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES) 
    contact_details = models.CharField(max_length=100, blank=True, null=True)
    pan = models.CharField(max_length=15, blank=True, null=True)
    gst = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    work_location = models.CharField(max_length=100, blank=True, null=True)
    work_type = models.CharField(max_length=50, choices=WORK_TYPE_CHOICES)
    experience = models.CharField(max_length=50, blank=True, null=True)
    skill_set = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="masterdata",
        null=True,        # allow null for existing rows
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_masterdata')
    is_active = models.BooleanField(default=True)

    # def __str__(self):
    #     return f"{self.name_of_resource} - {self.category.category_name}"