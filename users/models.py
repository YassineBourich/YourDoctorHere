from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required for healthcare accounts")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        # This is the most important security step:
        user.set_password(password) # Scrambles the password
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Entity(models.TextChoices):
    PATIENT = 'Patient'
    DOCTOR = 'Doctor'
    HOSPITAL = 'Hospital'

class User(AbstractUser):
    email = models.EmailField(unique=True)
    entity = models.CharField(choices=Entity.choices, default=Entity.PATIENT)

    # Tell Django that 'email' is the new ID for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['entity'] 

    # Connect the Manager to this Model
    objects = UserManager()

class Patient(models.Model):
    