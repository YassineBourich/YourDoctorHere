from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registration/', views.registration_view, name="registration"),
    path('send-verification-email/<uuid:uuid>/', views.send_verification_email_view, name="send_verification_email"),
    path('account-activation/<uuid:uuid>/', views.wait_for_activation_view, name="wait_for_activation"),
    path('check-account-activation/<uuid:uuid>/', views.check_email_verification, name="check_activation"),
    path('login/', views.login_view, name="login"),
    path('activate/<str:uidb64>/<str:token>/', views.verify_email_view, name="email_verificaton"),
    path('doctors/<uuid:id>/', views.doctor_profile_view, name="doctor_profile"),
    path('patients/<uuid:id>/', views.patient_profile_view, name="patient_profile"),
]

"""path('doctor_validation/', None, name=""),
    path('doctors/', None, name=""),
    path('doctors/<uuid:id>/edit/', views.doctor_profile, name="doctor_profile"),
    path('doctors/<uuid:id>/delete/', views.doctor_profile, name="doctor_profile"),
    path('patients/<uuid:id>/edit/', None, name=""),
    path('patients/<uuid:id>/delete/', None, name=""),
    path('patients/<uuid:id>/history/', None, name=""),
    """