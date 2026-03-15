from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django_countries.fields import CountryField
import uuid
from django.utils.text import slugify


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

class Gender(models.TextChoices):
    MALE = 'MALE'
    FEMALE = 'FEMALE'

class User(AbstractUser):
    email = models.EmailField(unique=True)
    entity = models.CharField(choices=Entity.choices, default=Entity.PATIENT)
    is_active = models.BooleanField(default=False)

    # Tell Django that 'email' is the new ID for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['entity'] 

    # Connect the Manager to this Model
    objects = UserManager()

class Speciality(models.Model):
    slug = models.SlugField(max_length=200)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class BaseProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    Nationality = CountryField(blank_label='(select country)', default='MA')
    tel = models.CharField(max_length=20)
    address = models.TextField()

    class Meta:
        abstract = True

class Patient(BaseProfile):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient',
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=None)

class Doctor(BaseProfile):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor',
    )
    specialty = models.ForeignKey(Speciality , on_delete=models.PROTECT, related_name='doctors')
    license_number = models.CharField(max_length=50, unique = True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    city = models.CharField(max_length=100)
    bio = models.TextField()
    is_verified = models.BooleanField(default=False)

class DoctorHospitalAssignment(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    
    joined_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'hospital')

class Hospital(BaseProfile):
    name = models.CharField(max_length=50)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='hospital',
    )
    staff_doctors = models.ManyToManyField(Doctor, 
        through=DoctorHospitalAssignment, 
        related_name='hospitals'
    )
    license_number = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True)
    is_emergency_24_7 = models.BooleanField(default=False)
    hospital_type = models.CharField(
        max_length=50, 
        choices=[('PUB', 'Public'), ('PRI', 'Private'), ('CLI', 'Clinic')]
    )

class PatientHistory(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='history'
    )
    #appointment = 