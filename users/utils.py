from .models import Patient, Doctor, User
from . import entities
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags
from django.db import transaction

# Function to get user by uuid
def get_user_by_uuid(uuid):
    # Check for the uuid within patients
    patient = Patient.objects.filter(uuid=uuid).first()
    if patient:
        return patient.user
    # Check for uuid within doctors
    doctor = Doctor.objects.filter(uuid=uuid).first()
    if doctor:
        return doctor.user
    
    return None

# Function to register a user with his profile form
def register_user_profile(request, user_form, profile_form, entity):
    if user_form.is_valid() and profile_form.is_valid():
        with transaction.atomic():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])   # Hash password
            user.entity = entity
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

        send_verification_email(request, user)
        return profile.uuid, True

    return None, False

# Function to send verification email
def send_verification_email(request, user):
    # generate token
    token = default_token_generator.make_token(user)
    # encode user id
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # resolve website domain
    domain = get_current_site(request).domain

    activation_url = f"http://{domain}/activate/{uid}/{token}/"

    # email data
    subject = 'Verify your YourDoctorHere Account'
    from_email = 'noreply@yourdoctorhere.com'
    to = user.email

    # email body with alternative HTML design
    context = {'user': user, 'activation_url': activation_url}
    html_content = render_to_string('users/emails/email_verification_template.html', context)
    text_content = strip_tags(html_content)

    # Email composition and sending
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
