from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registration/', None, name=""),
    path('login/', None, name=""),
    path('email_verification/', None, name=""),
    path('doctor_validation/', None, name=""),
    path('patients_history/', None, name=""),
    path('doctor_validation/', None, name=""),
    path('doctors/', None, name=""),
    path('doctors/<uuid: id>/', None, name=""),
    path('doctors/<uuid: id>/slot', None, name=""),
    path('patients/me/', None, name=""),
    path('patients/me/history/', None, name=""),
    path('patients/<uuid: id>/', None, name=""),
    path('patients/<uuid: id>/history/', None, name=""),
    path('hospitals/', None, name=""),
    path('hospitals/<uuid: id>/', None, name=""),
    path('hospitals/<uuid: id>/doctors/', None, name=""),
]