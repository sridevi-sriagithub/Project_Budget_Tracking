from django.contrib import admin
from .models import Category, MasterData

@admin.register(Category)
# @admin.register(MasterData)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'category_name', 'category_description', 'created_at', 'modified_at')
    search_fields = ('category_name',)
    list_filter = ('created_at', 'modified_at')

@admin.register(MasterData)
class MasterDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'category', 'name_of_resource', 
        'type_of_resource', 'contact_details', 'pan', 
        'gst', 'address', 'work_location', 'work_type', 
        'experience', 'skill_set'
    )
    search_fields = ('name_of_resource__email', 'category__category_name')
    list_filter = ('type_of_resource', 'category', 'work_location')