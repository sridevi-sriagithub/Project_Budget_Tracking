from django.urls import path
from .views import OrganisationAPI

urlpatterns = [
  

    path('organisation/', OrganisationAPI.as_view(), name='organisation-list'),
    path('organisation/<int:organisation_id>/', OrganisationAPI.as_view(), name='organisation-detail'),
 
]