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
            uuid, ok = register_user_profile(request, user_form, patient_profile_form, entity)
            if ok:
                return redirect("wait_for_activation", uuid)
            
        elif entity == entities.DOCTOR:
            doctor_profile_form = DoctorForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, doctor_profile_form, entity)
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
    user = get_user_by_uuid_or_404(uuid)
    if user.is_email_verified:
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return redirect('login')
    return send_email_and_redirect(request, user, uuid)

# Wait for Activation View
def wait_for_activation_view(request, uuid):
    user = get_user_by_uuid_or_404(uuid)
    return render(request, "users/emails/wait_for_activation.html", {'user_uuid': uuid, 'user': user})

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
            # If the user is not active, send activation email
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
        user.is_email_verified = True
        user.save()
        return redirect('login')
    else:
        # Otherwise return activation invalid page
        return render(request, 'users/emails/activation_invalid.html')
    
def check_email_verification(request, uuid):
    user = get_user_by_uuid_or_404(uuid)
    return JsonResponse({'is_email_verified': user.is_email_verified})

def password_reset_demand_view(request):
    if request.method == "POST":
        email = str(request.POST.get('email'))
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(request, user)
            messages.success(request, 'An email was sent to you email address.')
        except:
            messages.error(request, 'Invalide email address.')
    
def reset_password_view(request, uidb64, token):
    try:
        # Decode the uid and resolve the user
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # If user exists and token is valid then show the reset password form
    if user is not None and default_token_generator.check_token(user, token):
        return password_reset_confirm(request, user)
    else:
        # Otherwise return to forgot_password page
        return redirect('forgot_password')

def password_reset_confirm(request, user):
    # 'user' is the object found via the token
    if request.method == 'POST':
        # Use SetPasswordForm (not PasswordChangeForm)
        form = SetPasswordForm(user, request.POST)
        
        if form.is_valid():
            # Save the new password
            form.save()
            
            messages.success(request, "Your password has been set. You are now logged in.")
            return redirect('login') 
    else:
        # Initialize the form for the GET request
        form = SetPasswordForm(user)
        
    return render(request, 'users/password_reset/password_reset_confirm.html', {'form': form})

@login_required
def patient_profile_view(request, id):
    user = get_user_by_uuid_or_404(id)
    profile = get_object_or_404(Patient, uuid=id)
    history = PatientHistory.objects.filter(patient=profile).order_by('-at')[:5]
    is_me = False
    if get_profile_of_user_or_404(request.user).uuid == id:
        is_me = True
    return render(request, "users/profiles/profile.html", {'user': user, 'profile': profile, 'history': history, 'is_me': is_me, 'entities': {'PATIENT': entities.PATIENT, 'DOCTOR': entities.DOCTOR}})

@login_required
def doctor_profile_view(request, id):
    user = get_user_by_uuid_or_404(id)
    profile = get_object_or_404(Doctor, uuid=id)
    is_me = False
    if get_profile_of_user_or_404(request.user).uuid == id:
        is_me = True
    return render(request, "users/profiles/profile.html", {'user': user, 'profile': profile, 'history': None, 'is_me': is_me, 'entities': {'PATIENT': entities.PATIENT, 'DOCTOR': entities.DOCTOR}})

@login_required
def profile_edit_view(request):
    profile = get_profile_of_user_or_404(request.user)
    entity = request.user.entity

    if request.method == 'POST':
        if entity == entities.PATIENT:
            edit_form = PatientForm(request.POST, request.FILES, instance=profile)
        if entity == entities.DOCTOR:
            edit_form = DoctorForm(request.POST, request.FILES, instance=profile)
        else:
            pass
            
        if edit_form.is_valid():
            edit_form.save()
            if entity == entities.PATIENT:
                return redirect('patient_profile', profile.uuid)
            elif entity == entities.DOCTOR:
                return redirect('doctor_profile', profile.uuid)
            else:
                pass
    else:
        if entity == entities.PATIENT:
            edit_form = PatientForm(instance=profile)
        elif entity == entities.DOCTOR:
            edit_form = DoctorForm(instance=profile)
        else:
            pass
    
    return render(request, 'users/profiles/profile_edit.html', {'edit_form': edit_form})
@login_required
def profile_delete_view(request):
    if request.method == "POST":
        conf_password = request.POST.get('confirmation_password')
        if request.user.check_password(conf_password):
            user = request.user
            profile = get_profile_of_user_or_404(user)
            user.delete()
            profile.delete()
            logout(request)
            return redirect('home')
        else:
            messages.error(request, "Incorrect password. Deletion canceled.")

    return render(request, "users/profiles/profile_delete.html")

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            profile = get_profile_of_user_or_404(user)
        
            # When you change a password, Django's session hash changes. 
            # This function updates the session so the user isn't kicked out.
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password was successfully updated!')
            if user.entity == entities.PATIENT:
                return redirect('patient_profile', profile.uuid)
            elif user.entity == entities.DOCTOR:
                return redirect('doctor_profile', profile.uuid)
            else:
                pass
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'users/change_password.html', {'form': form})

# Login API
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api_view(request):
    input_serializer = LoginSerializer(data=request.data)

    # Checking the validity of email and password
    if not input_serializer.is_valid():
        return Response(
            input_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Retreiving email and password from request's body
    email = request.data.get('email')
    password = request.data.get('password')

    # Authentication of the user
    user = authenticate(username=email, password=password)
    if user is not None:
        # If the user is authenticated, created a token and return it
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
