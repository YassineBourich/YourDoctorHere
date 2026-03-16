from django.urls import path
from . import views

urlpatterns = [
    # Appointment booking flow
    path('doctors/<uuid:doctor_uuid>/slots/', views.doctor_slots, name='doctor_slots'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/<uuid:appointment_uuid>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<uuid:appointment_uuid>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<uuid:appointment_uuid>/cancel/', views.cancel_appointment, name='cancel_appointment'),

    # Medical notes (doctor only)
    path('appointments/<uuid:appointment_uuid>/notes/', views.add_note, name='add_note'),

    # Patient history
    path('patients/me/history/', views.my_history, name='my_history'),
]