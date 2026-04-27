from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django_countries.fields import CountryField
import uuid
from django.utils.text import slugify
from . import entities


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required for healthcare accounts")
        
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        
        user.set_password(password) # Scrambles the password
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Entity(models.TextChoices):
    PATIENT = entities.PATIENT
    DOCTOR = entities.DOCTOR

class Gender(models.TextChoices):
    MALE = 'MALE'
    FEMALE = 'FEMALE'

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    entity = models.CharField(choices=Entity.choices, default=Entity.PATIENT)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)

    # Tell Django that 'email' is the new ID for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['entity'] 

    # Connect the Manager to this Model
    objects = UserManager()

class BaseProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.ImageField(upload_to='avatars/%Y/%m', null=True, blank=True)
    Nationality = CountryField(blank_label='(select country)', default='MA')
    tel = models.CharField(max_length=20)
    address = models.TextField()

    @property
    def avatar_url(self):
        if self.avater and hasattr(self.avater, 'url'):
            return self.avater.url
        return '/static/images/default_avatar.jpg'

    class Meta:
        abstract = True

class Patient(BaseProfile):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient',
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=None)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class Doctor(BaseProfile):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor',
    )
    specialty = models.CharField(max_length=200, null=True, blank=True)
    license_number = models.CharField(max_length=50, unique = True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    city = models.CharField(max_length=100)
    bio = models.TextField()
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}".strip()


"""
    Moved here from users app to avoid circular Foreign Key: 
    PatientHistory living in the users app creates a circular dependency problem: it needs
    to reference Appointment from your medical app, but medical already references users.
    """
"""
class PatientHistory(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='history'
    )
    #appointment = 

"""
