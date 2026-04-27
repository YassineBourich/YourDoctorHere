from django import forms
from .models import User, Patient, Doctor

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['email', 'password']

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an update lock the first and last name
        if self.instance and self.instance.pk:
            self.fields['first_name'].disabled = True
            self.fields['last_name'].disabled = True

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['user', 'is_verified']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an update lock the first and last name
        if self.instance and self.instance.pk:
            self.fields['first_name'].disabled = True
            self.fields['last_name'].disabled = True
