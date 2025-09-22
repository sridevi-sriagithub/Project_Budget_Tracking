from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password

User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Linking to your User model
        fields = ['id', 'username', 'email', 'is_admin', 'first_name', 'last_name']
        read_only_fields = ['id', 'email'] 

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email','id']
       
 
    def validate_email(self, value):
        """Ensure email format is correct."""
        import re
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid email format. Please enter a valid email.")
        return value
 
    def create(self, validated_data):
        """Create and return a new user instance."""
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"]
        )
        return user 

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'Invalid email'})
        

        if not check_password(password, user.password):
            raise serializers.ValidationError({'password': 'Invalid password'})
 
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        data['user'] = user
        return data     

class LogoutSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        User = get_user_model()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()  # No UniqueValidator here
    otp = serializers.CharField(max_length=6)
    # new_password = serializers.CharField(write_only=True, min_length=6)
class ForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Custom validation to check if passwords match
        """
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data
class NewPassswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
