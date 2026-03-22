from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('registration/', views.registration_view, name="registration"),
    path('send-verification-email/<uuid:uuid>/', views.send_verification_email_view, name="send_verification_email"),
    path('account-activation/<uuid:uuid>/', views.wait_for_activation_view, name="wait_for_activation"),
    path('check-account-activation/<uuid:uuid>/', views.check_email_verification, name="check_activation"),
    path('login/', views.login_view, name="login"),
    path('activate/<str:uidb64>/<str:token>/', views.verify_email_view, name="email_verificaton"),
    path('doctors/<uuid:id>/', views.doctor_profile_view, name="doctor_profile"),
    path('doctors/edit/', views.profile_edit_view, name="doctor_profile_edit"),
    path('doctors/delete/', views.profile_delete_view, name="doctor_profile_delete"),
    path('doctors/change-password/', views.change_password_view, name="doctors_change_password"),
    path('patients/<uuid:id>/', views.patient_profile_view, name="patient_profile"),
    path('patients/edit/', views.profile_edit_view, name="patient_profile_edit"),
    path('patients/delete/', views.profile_delete_view, name="patient_profile_delete"),
    path('patients/change-password/', views.change_password_view, name="patients_change_password"),
]

"""path('doctor_validation/', None, name=""),
    path('doctors/', None, name=""),
    """

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)