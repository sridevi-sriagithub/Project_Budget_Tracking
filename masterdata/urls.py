from django.urls import path
from .views import CategoryView, MasterDataView, ProfileAPIView, ResourceTypeAPIView, WorkTypeAPIView, ModuleUsersView, ALLAPIView
urlpatterns = [
    path('category/', CategoryView.as_view(), name='module-list'),
    path('category/<int:category_id>/', CategoryView.as_view(), name='module-detail'),
    path('create/', MasterDataView.as_view(), name='masterdata-list'),
    path('all/', ALLAPIView.as_view(), name='masterdata-all'),
    path('profile/<int:pk>/', MasterDataView.as_view(), name='masterdata-detail'),
    path('category/<int:category_id>/users/', ModuleUsersView.as_view(), name='module-users'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('resource-types/', ResourceTypeAPIView.as_view(), name='resource-types'),
    path('work-types/', WorkTypeAPIView.as_view(), name='work-types'),
]