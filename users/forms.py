from django import forms
from .models import User, Patient, Doctor, Hospital

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['email', 'password']

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = ['user']

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['user', 'specialty', 'is_verified']

class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        exclude = ['user', 'staff_doctors']