from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, PatientForm, DoctorForm, HospitalForm
from . import entities
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import User

# Create your views here.
def home(request):
    return render(request, "home.html", {})

def register(request):
    patient_profile_form = PatientForm()
    doctor_profile_form = DoctorForm()
    hospital_profile_form = HospitalForm()
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        entity = request.POST.get('entity')
        if entity == entities.PATIENT:
            patient_profile_form = PatientForm(request.POST, request.FILES)
            _, ok = register_user_profile(request, user_form, patient_profile_form)
            if ok:
                return redirect("home")
            
        elif entity == entities.DOCTOR:
            doctor_profile_form = DoctorForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, doctor_profile_form)
            if ok:
                return redirect("doctor_profile", uuid)
            
        elif entity == entities.HOSPITAL:
            hospital_profile_form = HospitalForm(request.POST, request.FILES)
            uuid, ok = register_user_profile(request, user_form, hospital_profile_form)
            if ok:
                return redirect("hospital_profile", uuid)
        
        else:
            pass

    else:
        user_form = UserRegistrationForm()
        
    context = {
        'user_form': user_form, 
        'patient_profile_form': patient_profile_form, 
        'doctor_profile_form': doctor_profile_form, 
        'hospital_profile_form': hospital_profile_form,
        'PATIENT': entities.PATIENT,
        'DOCTOR': entities.DOCTOR,
        'HOSPITAL': entities.HOSPITAL,
    }
    return render(request, 'users/registration/registration.html', context)

def register_user_profile(request, user_form, profile_form):
    if user_form.is_valid() and profile_form.is_valid():
        user = user_form.save(commit=False)
        user.entity = entities.PATIENT
        user.save()
        send_verification_email(request, user)
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()
        return profile.uuid, True

    return None, False

def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain
    
    activation_url = f"http://{domain}/activate/{uid}/{token}/"

    subject = 'Verify your YourDoctorHere Account'
    from_email = 'noreply@yourdoctorhere.com'
    to = user.email

    context = {'user': user, 'activation_url': activation_url}
    html_content = render_to_string('users/emails/email_verification_template.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()

def login(request):
    if request.method == 'POST':
        user_form = AuthenticationForm(request, data=request.POST)
        if user_form.is_valid():
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

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('home')
    else:
        return render(request, 'activation_invalid.html')

def doctor_profile(request, id):
    return render(request, "users/profiles/doctor_profile.html", {})


def hospital_profile(request, id):
    return render(request, "users/profiles/hospital_profile.html", {})