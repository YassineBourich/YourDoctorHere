from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registration/', views.register, name="registration"),
    path('login/', views.login, name="login"),
    path('email_verification/', views.verify_email, name="email_verificaton"),
    path('doctors/<uuid:id>/', views.doctor_profile, name="doctor_profile"),
    path('hospitals/<uuid:id>/', views.hospital_profile, name="hospital_profile"),
]

"""path('doctor_validation/', None, name=""),
    path('doctors/', None, name=""),
    path('doctors/<uuid:id>/slot', None, name=""),
    path('patients/me/', None, name=""),
    path('patients/me/history/', None, name=""),
    path('patients/<uuid:id>/', None, name=""),
    path('patients/<uuid:id>/history/', None, name=""),
    path('hospitals/', None, name=""),
    path('hospitals/<uuid:id>/doctors/', None, name=""),"""