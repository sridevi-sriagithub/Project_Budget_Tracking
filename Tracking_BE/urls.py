"""
URL configuration for Tracking_BE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
def home(request):
    return HttpResponse("django backend is live on server")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('login.urls')), 
    path('organization/', include('organization.urls')),  
    path('project/', include('project_creation.urls')),  
    # path('user_profile/', include('user_profile.urls')),  
    path('budget/', include('budget.urls')),     
    path('roles/', include('roles.urls')), 
    path('data/',include('masterdata.urls')), 
    path('bankdetails/',include('bank_details.urls')),
    path('tasks/',include('task_creation.urls')),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


