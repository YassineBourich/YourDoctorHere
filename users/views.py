from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import UserRegistrationForm, PatientForm, DoctorForm
from . import entities
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from .models import User
from django.db.models import Q
from .utils import (
    get_user_by_uuid_or_404, 
    register_user_profile, 
    send_verification_email, 
    send_email_and_redirect,
    get_profile_of_user_or_404,
    send_password_reset_email,
)
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from .models import Patient, Doctor
from medical.models import PatientHistory

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status

from .serializers import *


def home(request):
    """
    Renders the landing page.
    Logic for routing authenticated users to their respective dashboards is handled
    within the home template itself to reduce backend redirection overhead.
    """
    profile = None
    if request.user.is_authenticated:
        profile = get_profile_of_user_or_404(request.user)
        
    return render(request, "home.html", {'profile': profile})


def registration_view(request):
    """
    Handles user registration for both patients and doctors.
    
    Why we process entity types manually:
    We use a single registration view with a hidden 'entity' field instead of separate URLs
    to simplify the frontend (one unified form with tabs). The backend parses this entity
    to instantiate either a Patient or Doctor profile alongside the base User model.
    This guarantees that every active user has an associated profile immediately upon creation.
    """
    patient_profile_form = PatientForm()
    doctor_profile_form = DoctorForm()
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        entity = request.POST.get('entity')
        
        # We delegate the atomic transaction of creating the User + Profile to register_user_profile
        # to ensure we don't end up with orphaned User records if profile creation fails.
        if entity == entities.PATIENT:
            patient_profile_form = PatientForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, patient_profile_form, entity)

            if ok:
                return redirect("wait_for_activation", uuid)
            
        elif entity == entities.DOCTOR:
            doctor_profile_form = DoctorForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, doctor_profile_form, entity)
            if ok:
                return redirect("wait_for_activation", uuid)
        else:
            messages.error(request, "Please choose a valid account type.")
    else:
        user_form = UserRegistrationForm()
        
    context = {
        'user_form': user_form, 
        'patient_profile_form': patient_profile_form, 
        'doctor_profile_form': doctor_profile_form, 
        'PATIENT': entities.PATIENT,
        'DOCTOR': entities.DOCTOR,
    }
    return render(request, 'users/registration/registration.html', context)


def send_verification_email_view(request, uuid):
    """
    Triggers the dispatch of an activation email.
    
    Why this is a dedicated view:
    Separating this from registration allows users who lost their initial email or had it
    bounce to request a new verification link without having to re-register.
    """
    user = get_user_by_uuid_or_404(uuid)
    if user.is_email_verified:
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return redirect('login')
    return send_email_and_redirect(request, user, uuid)


def wait_for_activation_view(request, uuid):
    user = get_user_by_uuid_or_404(uuid)
    return render(request, "users/emails/wait_for_activation.html", {'user_uuid': uuid, 'user': user})


def login_view(request):
    """
    Authenticates the user and initiates their session.
    
    Why we check email verification during login:
    Django's default authenticate() doesn't enforce custom verification states. We explicitly
    check `is_email_verified` *after* a successful password check to prevent unverified
    accounts from accessing the platform, while still providing a clear path to resend
    the verification email if they try to log in.
    """
    if request.method == 'POST':
        user_form = AuthenticationForm(request, data=request.POST)
        if user_form.is_valid():
            user = user_form.get_user()
            
            # Guard clause against unverified emails
            if user.is_email_verified:
                login(request, user)
                messages.success(request, f"Welcome back, {user.email}!")
                return redirect('home')
            else:
                send_verification_email(request, user)
                return redirect('send_verification_email', get_profile_of_user_or_404(user).uuid)
    else:
        user_form = AuthenticationForm()
        
    context = {
        'user_form': user_form,
    }
    return render(request, 'users/registration/login.html', context)


def verify_email_view(request, uidb64, token):
    """
    Verifies the email based on the token clicked in the email link.
    We use uidb64 and token to ensure the link cannot be easily forged.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'users/emails/activation_invalid.html')
    

def check_email_verification(request, uuid):
    user = get_user_by_uuid_or_404(uuid)
    return JsonResponse({'is_email_verified': user.is_email_verified})


def password_reset_demand_view(request):
    """
    Handles the request to reset a password.
    We wrap the user lookup in a try/except but always show a success/neutral message
    (if we want to prevent email enumeration) or specific errors depending on security policy.
    """
    if request.method == "POST":
        email = str(request.POST.get('email')).strip().lower()
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(request, user)
            messages.success(request, 'An email was sent to you email address.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalide email address.')
            return render(request, 'users/password_reset/password_reset_demand.html')
        except Exception:
            messages.error(request, 'Failed to send password reset email.')
            return render(request, 'users/password_reset/password_reset_demand.html')

    return render(request, 'users/password_reset/password_reset_demand.html')
    
def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        return password_reset_confirm(request, user)
    else:
        return redirect('forgot_password')


def password_reset_confirm(request, user):
    """
    Final step in password reset flow.
    We use SetPasswordForm instead of PasswordChangeForm because the user is not
    logged in and therefore doesn't know their old password.
    """
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been set. You are now logged in.")
            return redirect('login') 
    else:
        form = SetPasswordForm(user)
        
    return render(request, 'users/password_reset/password_reset_confirm.html', {'form': form})


@login_required
def patient_profile_view(request, id):
    """
    Displays patient profile.
    Why we check `is_me`:
    We allow users to view other profiles (like doctors viewing patients they have appointments with),
    but we use `is_me` to conditionally render private actions like 'Edit' or 'Delete' in the template.
    """
    user = get_user_by_uuid_or_404(id)
    profile = get_object_or_404(Patient, uuid=id)
    history = PatientHistory.objects.filter(patient=profile).order_by('-at')[:5]
    
    is_me = get_profile_of_user_or_404(request.user).uuid == id
        
    return render(request, "users/profiles/profile.html", {'user': user, 'profile': profile, 'history': history, 'is_me': is_me, 'entities': {'PATIENT': entities.PATIENT, 'DOCTOR': entities.DOCTOR}})


@login_required
def doctor_profile_view(request, id):
    user = get_user_by_uuid_or_404(id)
    profile = get_object_or_404(Doctor, uuid=id)
    
    is_me = get_profile_of_user_or_404(request.user).uuid == id
        
    return render(request, "users/profiles/profile.html", {'user': user, 'profile': profile, 'history': None, 'is_me': is_me, 'entities': {'PATIENT': entities.PATIENT, 'DOCTOR': entities.DOCTOR}})


@login_required
def profile_edit_view(request):
    """
    Handles editing of both patient and doctor profiles.
    We dynamically swap the ModelForm based on the user's entity to keep the edit route unified.
    """
    profile = get_profile_of_user_or_404(request.user)
    entity = request.user.entity

    if request.method == 'POST':
        if entity == entities.PATIENT:
            edit_form = PatientForm(request.POST, request.FILES, instance=profile)
        elif entity == entities.DOCTOR:
            edit_form = DoctorForm(request.POST, request.FILES, instance=profile)
            
        if edit_form.is_valid():
            edit_form.save()
            if entity == entities.PATIENT:
                return redirect('patient_profile', profile.uuid)
            elif entity == entities.DOCTOR:
                return redirect('doctor_profile', profile.uuid)
    else:
        if entity == entities.PATIENT:
            edit_form = PatientForm(instance=profile)
        elif entity == entities.DOCTOR:
            edit_form = DoctorForm(instance=profile)
    
    return render(request, 'users/profiles/profile_edit.html', {'edit_form': edit_form})


@login_required
def profile_delete_view(request):
    """
    Handles account deletion.
    Why we ask for the password:
    Deletion is a destructive action. Asking for a password prevents a scenario where a user
    leaves their session open and a malicious actor deletes their account.
    """
    if request.method == "POST":
        conf_password = request.POST.get('confirmation_password')
        if request.user.check_password(conf_password):
            user = request.user
            profile = get_profile_of_user_or_404(user)
            # Both models are cascading/linked, but we explicitly delete to trigger any signals if needed
            user.delete()
            profile.delete()
            logout(request)
            return redirect('home')
        else:
            messages.error(request, "Incorrect password. Deletion canceled.")

    return render(request, "users/profiles/profile_delete.html")


@login_required
def change_password_view(request):
    """
    Allows a logged-in user to change their password securely.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            profile = get_profile_of_user_or_404(user)
        
            # Why we call update_session_auth_hash:
            # When a password changes, Django invalidates the current session hash for security.
            # Calling this function re-authenticates the current session with the new hash 
            # so the user isn't abruptly logged out.
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password was successfully updated!')
            if user.entity == entities.PATIENT:
                return redirect('patient_profile', profile.uuid)
            elif user.entity == entities.DOCTOR:
                return redirect('doctor_profile', profile.uuid)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'users/change_password.html', {'form': form})


@login_required
def logout_view(request):
    """
    Terminates the user session.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ----------------- APIs ----------------- #

# Login API
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api_view(request):
    """
    Token-based authentication for external clients.
    """
    input_serializer = LoginSerializer(data=request.data)

    if not input_serializer.is_valid():
        return Response(
            input_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key,},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"error": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
# Profile API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile_api_view(request):
    user = request.user
    profile = get_profile_of_user_or_404(user)

    if user.entity == entities.PATIENT:
        serializer = PatientSerializer(profile, context={'request': request})
    elif user.entity == entities.DOCTOR:
        serializer = DoctorSerializer(profile, context={'request': request})
    else:
        pass
    return Response(serializer.data)

# History API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_history_api_view(request):
    user = request.user
    profile = get_object_or_404(PatientHistory, patient=user.patient)

    serializer = PatientHistorySerializer(profile, context={'request': request})
    return Response(serializer.data)

# Doctors API
@api_view(['GET'])
@permission_classes([AllowAny])
def doctors_api_view(request):
    doctors = Doctor.objects.all()

    serializer = DoctorSerializer(doctors, context={'request': request}, many=True)
    return Response(serializer.data)
