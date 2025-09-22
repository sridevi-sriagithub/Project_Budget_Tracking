


from django.contrib import admin
from django.contrib.auth.models import Permission
from .models import Role, Permission as CustomPermission, RolePermission,UserRole
from django.contrib import admin
from .models import Role

class RoleAdmin(admin.ModelAdmin):
    list_display = ["role_id","name"]# Replace "name" with the correct field name from the Role model
    search_fields = ("name",)  # Adjust as per model fields

admin.site.register(Role, RoleAdmin)



@admin.register(CustomPermission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('permission_id', 'name')



from django.contrib import admin
from .models import RolePermission

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "display_permissions", "created_at", "created_by")
    search_fields = ("role__name", "permission__name")
    filter_horizontal = ("permission",)  # ✅ Allows bulk selection in admin
    actions = ["assign_all_permissions"]

    # ✅ Custom method to display permissions in a readable format
    def display_permissions(self, obj):
        return ", ".join([p.name for p in obj.permission.all()]) if obj.permission.exists() else "No Permissions"

    display_permissions.short_description = "Permissions"  # Column name in admin

    # ✅ Bulk action to assign all permissions to selected roles
    def assign_all_permissions(self, request, queryset):
        from django.contrib.auth.models import Permission
        all_permissions = Permission.objects.all()
        for role_permission in queryset:
            role_permission.permission.set(all_permissions)  # Assign all permissions
        self.message_user(request, "All permissions assigned successfully.")

    assign_all_permissions.short_description = "Assign all permissions to selected roles"

    


from django.contrib import admin
from .models import UserRole

class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role",'user_role_id')  # Ensure these fields exist in your model
    search_fields = ("user__username", "role__name")  # Use correct relationships
    list_filter = ("role",)  

admin.site.register(UserRole, UserRoleAdmin)
