from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
 
class Command(BaseCommand):
    help = "Create a superuser if none exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "sridevi@sriainfotech.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin@123")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created ✅"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists"))