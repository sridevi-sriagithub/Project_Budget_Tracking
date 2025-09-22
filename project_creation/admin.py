from django.contrib import admin
# Register your models here.
from .models import Client, Project, ClientPOC
admin.site.register(Client)
admin.site.register(Project)
admin.site.register(ClientPOC)

# admin.site.register(ID)
# admin.site.register(IDPattern)