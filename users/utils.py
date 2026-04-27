from .models import Patient, Doctor, User
from . import entities
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags
<<<<<<< HEAD
from django.db import transaction
=======
from django.shortcuts import redirect
from django.http import Http404
>>>>>>> origin/main

# Function to get user by uuid
def get_user_by_uuid_or_404(uuid):
    # Check for the uuid within patients
    patient = Patient.objects.filter(uuid=uuid).first()
    if patient:
        return patient.user
    # Check for uuid within doctors
    doctor = Doctor.objects.filter(uuid=uuid).first()
    if doctor:
        return doctor.user
    
    raise Http404("No user matches the provided UUID")

# Function to get profile by uuid
def get_profile_by_uuid_or_404(uuid):
    # Check for the uuid within patients
    patient = Patient.objects.filter(uuid=uuid).first()
    if patient:
        return patient
    # Check for uuid within doctors
    doctor = Doctor.objects.filter(uuid=uuid).first()
    if doctor:
        return doctor
    
    raise Http404("No user matches the provided UUID")

#Function to get profile of a user
def get_profile_of_user_or_404(user):
    if user.entity == entities.PATIENT:
        profile = Patient.objects.filter(user = user).first()
    elif user.entity == entities.DOCTOR:
        profile = Doctor.objects.filter(user = user).first()
    if profile:
        return profile
    raise Http404("No profile matches the provided user")

# Function to register a user with his profile form
def register_user_profile(request, user_form, profile_form, entity):
    if user_form.is_valid() and profile_form.is_valid():
<<<<<<< HEAD
        with transaction.atomic():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])   # Hash password
            user.entity = entity
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

=======
        user = user_form.save(commit=False)
        user.set_password(user_form.cleaned_data['password'])   # Hash password
        user.entity = entity
        user.save()
>>>>>>> origin/main
        send_verification_email(request, user)
        return profile.uuid, True

    return None, False

# Function to send email to a user
def send_email(request, user, URI, subject, template):
    # generate token
    token = default_token_generator.make_token(user)
    # encode user id
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # resolve website domain
    domain = get_current_site(request).domain

    activation_url = f"http://{domain}/{URI}/{uid}/{token}/"

    # email data
    from_email = 'noreply@yourdoctorhere.com'
    to = user.email

    # email body with alternative HTML design
    context = {'user': user, 'activation_url': activation_url}
    html_content = render_to_string(template, context)
    text_content = strip_tags(html_content)

    # Email composition and sending
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
<<<<<<< HEAD
=======

# Function to send verification email
def send_verification_email(request, user):
    subject = 'Verify your YourDoctorHere Account'
    template = 'users/emails/email_verification_template.html'
    send_email(request, user, 'activate', subject, template)

# Function to send email and redirect
def send_email_and_redirect(request, user, uuid):
    send_verification_email(request, user)
    return redirect("wait_for_activation", uuid)

# Function to send password reset link
def send_password_reset_email(request, user):
    subject = 'Reset your password'
    template = 'users/emails/password_reset_template.html'
    send_email(request, user, 'reset-password', subject, template)
>>>>>>> origin/main
