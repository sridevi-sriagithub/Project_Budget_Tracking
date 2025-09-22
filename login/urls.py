from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView, NewPasswordView, UserManagementView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('create-new-password/', NewPasswordView.as_view(), name='create_new_password'),
    path('users/', UserManagementView.as_view(), name='user-list'),  
    path('users/<int:user_id>/', UserManagementView.as_view(), name='user-detail'),                 
                  

]
