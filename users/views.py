from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, PatientForm, DoctorForm
from . import entities
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.db.models import Q
from .utils import get_user_by_uuid, register_user_profile, send_verification_email
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    return render(request, "home.html", {})

# Registration View
def registration_view(request):
    # Initializing profile forms
    patient_profile_form = PatientForm()
    doctor_profile_form = DoctorForm()
    # Conditionning on methods
    if request.method == 'POST':
        # Fill the User registration form with the request data
        user_form = UserRegistrationForm(request.POST)
        # Retrieve the entity type
        entity = request.POST.get('entity')
        # Register the user with profile according to entity type
        # If ok, wait for email activation
        if entity == entities.PATIENT:
            patient_profile_form = PatientForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, patient_profile_form)
            if ok:
                return redirect("wait_for_activation", uuid)
            
        elif entity == entities.DOCTOR:
            doctor_profile_form = DoctorForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, doctor_profile_form)
            if ok:
                return redirect("wait_for_activation", uuid)
        
        else:
            pass

    else:
        # If the method is not POST, create and send empty form
        user_form = UserRegistrationForm()
        
    context = {
        'user_form': user_form, 
        'patient_profile_form': patient_profile_form, 
        'doctor_profile_form': doctor_profile_form, 
        'PATIENT': entities.PATIENT,
        'DOCTOR': entities.DOCTOR,
    }
    return render(request, 'users/registration/registration.html', context)

# Send Email Verification View
def send_verification_email_view(request, uuid):
    user = get_user_by_uuid(uuid)
    send_verification_email(request, user)
    return redirect("wait_for_activation", uuid)

# Wait for Activation View
def wait_for_activation_view(request, uuid):
    return render(request, "users/emails/wait_for_activation.html", {'user_uuid': uuid})

# Login View
def login_view(request):
    # If method is not POST, return an empty AuthenticationForm
    if request.method == 'POST':
        # Fill the form with the POST data
        user_form = AuthenticationForm(request, data=request.POST)
        # Validate the form
        if user_form.is_valid():
            # Authenticate user and login
            user = user_form.get_user()
            login(request, user)
            
            messages.success(request, f"Welcome back, {user.email}!")
            return redirect('home')
    else:
        user_form = AuthenticationForm()
        
    context = {
        'user_form': user_form,
    }
    return render(request, 'users/registration/login.html', context)

# Email Verification View
def verify_email_view(request, uidb64, token):
    try:
        # Decode the uid and resolve the user
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # If user exists and tken is valid then activate account
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('home')
    else:
        # Otherwise return activation invalid page
        return render(request, 'users/emails/activation_invalid.html')

@login_required
def doctor_profile(request, id):
    return render(request, "users/profiles/doctor_profile.html", {})

@login_required
def hospital_profile(request, id):
    return render(request, "users/profiles/hospital_profile.html", {})