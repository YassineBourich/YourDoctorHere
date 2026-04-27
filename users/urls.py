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
    path('forgot-password/', views.password_reset_demand_view, name="forgot_password"),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_view, name="password-reset"),
    path('doctors/<uuid:id>/', views.doctor_profile_view, name="doctor_profile"),
    path('doctors/edit/', views.profile_edit_view, name="doctor_profile_edit"),
    path('doctors/delete/', views.profile_delete_view, name="doctor_profile_delete"),
    path('doctors/change-password/', views.change_password_view, name="doctors_change_password"),
    path('patients/<uuid:id>/', views.patient_profile_view, name="patient_profile"),
    path('patients/edit/', views.profile_edit_view, name="patient_profile_edit"),
    path('patients/delete/', views.profile_delete_view, name="patient_profile_delete"),
    path('patients/change-password/', views.change_password_view, name="patients_change_password"),

    # API endpoint
    path('api/login/', views.login_api_view, name='login_api'),
    path('api/profile/me/', views.my_profile_api_view, name='my_profile_api'),
    path('api/profile/me/history/', views.my_history_api_view, name='my_history_api'),
    path('api/doctors/', views.doctors_api_view, name='doctors_api'),
    path('logout/', views.logout_view, name="logout"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
