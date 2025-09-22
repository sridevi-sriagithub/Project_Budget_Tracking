from django.urls import path
from .views import (ClientListCreateAPIView, ClientDetailAPIView,ProjectListCreateAPIView,
                    ProjectDetailAPIView,ClientPocCreateAPIView, ClientPocDetailAPIView,
                    StatusChoicesView, ProjectUserAssignView, ProjectRelatedTasksView)

urlpatterns = [
  
    path('clients/', ClientListCreateAPIView.as_view(), name='client-list-create'),
    path('clients/<int:pk>/', ClientDetailAPIView.as_view(), name='client-detail'),
    path('clients/poc/', ClientPocCreateAPIView.as_view(), name='client-poc-list-create'),
    path('clients/poc/<int:pk>/', ClientPocDetailAPIView.as_view(), name='client-poc-detail'),
    path('projects/', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('project_pt/', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('project_pt/<int:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('status-choices/', StatusChoicesView.as_view(), name='status-choices'),
    # path('projects/assign-user/', ProjectUserAssignView.as_view(), name='assign-user'),
    path('projects/<int:project_id>/assign-user/', ProjectUserAssignView.as_view(), name='assign-user-detail'),
    path('projects/tasks/', ProjectRelatedTasksView.as_view(), name='project-tasks'),
]
   

 
