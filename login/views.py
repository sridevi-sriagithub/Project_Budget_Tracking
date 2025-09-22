from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from .models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (UserSerializer,RegisterSerializer,LoginSerializer,LogoutSerializer,
                          ForgotPasswordSerializer,ResetPasswordSerializer, NewPassswordSerializer, UserSerializer, ForgotSerializer)
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth import logout
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .tasks import send_registration_email_sync
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated, AllowAny
from roles.models import UserRole

# import logging
import random, string
User = get_user_model()

import logging

logger = logging.getLogger(__name__)


import random
import string

def generate_password(length=6):
    if length < 2:
        raise ValueError("Password length must be at least 2 to include both letter and digit.")

    # Ensure at least one letter and one digit
    letters = random.choice(string.ascii_letters)
    digits = random.choice(string.digits)
    remaining = random.choices(string.ascii_letters + string.digits, k=length - 2)

    # Shuffle all parts to make the position random
    password_list = list(letters + digits + ''.join(remaining))
    random.shuffle(password_list)
    return ''.join(password_list)


class RegisterView(APIView):
    """API view for user registration."""
    # serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users
    authentication_classes = [JWTAuthentication]  # Use JWT for authentication
  

    def post(self, request):
        """Handles user registration."""
        # if request.user.is_authenticated and not getattr(request.user, 'is_admin', False):
        #     return Response({'error': 'Only admins can register new users'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RegisterSerializer(data=request.data)  # ✅ Directly calling RegisterSerializer

        if serializer.is_valid():
            user = serializer.save()
            # raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            raw_password = generate_password()
            user.set_password(raw_password)
            user.save()

            
            send_registration_email_sync(user.id, raw_password)  # ✅ Async email
            logger.info(f"User {user.email} registered successfully, email task queued.")
        

            return Response(
                {"message": "User registered successfully. Check your email for login credentials."},
                status=status.HTTP_201_CREATED,
            )

        logger.error(f"Registration validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def get(self, request, *args, **kwargs):
        # self.permission_required = "create_users"

        if request.user.is_authenticated and not request.user.is_admin:
            return Response({'error': 'Only admins can register new users'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RegisterSerializer(data=request.data)
    
        

        register = User.objects.all()
        serializer = RegisterSerializer(register, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "message": "Login successful",
                "username": user.username,
                "email": user.email,
                "role":UserRole.objects.filter(user=user).values_list('role__name', flat=True)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LogoutView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request) 
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            User = get_user_model()
            user = User.objects.filter(email=email).first()

            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.save()

            # Send OTP Email
            try:
                send_mail(
                    'Your Password Reset OTP',
                    f'Use this OTP to reset your password: {otp}',
                    'noreply@projecttracker.com',
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                return Response({'error': 'Failed to send OTP', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'message': 'OTP sent to email'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            otp = serializer.validated_data.get('otp')

            user = User.objects.filter(email=email).first()

            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            if user.otp_code != otp:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # Clear OTP after verification
            user.otp_code = None
            user.save()

            return Response({'message': 'OTP verified. You can now set a new password.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = ForgotSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            user.password = make_password(new_password)
            user.save()
            return Response({'message': 'Password reset successfully. Redirecting to login...'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
  


class NewPasswordView(APIView):
    def post(self, request):
        serializer = NewPassswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            new_password = serializer.validated_data.get('new_password')

            user = User.objects.filter(email=email).first()

            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            user.set_password(new_password)
            user.save()

            return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class UserManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        print(f"User: {request.user.email}, Is Admin: {request.user.is_admin}")
        if not request.user.is_admin:
            # print(f"User: {request.user.email}, Is Admin: {request.user.is_admin}")
            return Response({'error': 'Only admins can view users'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
 

    def delete(self, request, user_id):
        if not request.user.is_admin:
            return Response({'error': 'Only admins can delete users'}, status=status.HTTP_403_FORBIDDEN)
        user = User.objects.get(id=user_id)
        user.delete()
        return Response({'message': 'User deleted successfully'})


    def put(self, request, user_id):
        if not request.user.is_admin:
            return Response({'error': 'Only admin can update users'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        print(serializer.errors)  # Debug
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    