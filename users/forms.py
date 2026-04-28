from django import forms
from .models import User, Patient, Doctor
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            raise forms.ValidationError(list(e.messages))
        return password

    def clean(self):
        # This function checks if the two passwords match
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            # If they don't match, we add an error to the 'password' field
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data

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
