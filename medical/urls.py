from django.urls import path
from . import views

urlpatterns = [
    # WeeklySlot management (doctor only)
    path('slots/', views.my_slots, name='my_slots'),
    path('slots/add/', views.add_slot, name='add_slot'),
    path('slots/<int:slot_id>/delete/', views.delete_slot, name='delete_slot'),
    path('blocked-dates/add/', views.add_blocked_date, name='add_blocked_date'),
    path('blocked-dates/<int:blocked_date_id>/delete/', views.delete_blocked_date, name='delete_blocked_date'),

    # Booking (patient only) — two stage
    path('doctors/<uuid:doctor_uuid>/slots/', views.doctor_slots, name='doctor_slots'),
    path('doctors/<uuid:doctor_uuid>/slots/<int:slot_id>/', views.slot_detail, name='slot_detail'),
    path('doctors/<uuid:doctor_uuid>/book/', views.book_appointment, name='book_appointment'),

    # Appointment management
    path('appointments/<uuid:appointment_uuid>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<uuid:appointment_uuid>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<uuid:appointment_uuid>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointments/<uuid:appointment_uuid>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<uuid:appointment_uuid>/notes/', views.add_note, name='add_note'),

    # Patient history
    path('patients/me/history/', views.my_history, name='my_history'),
]


""""
/doctors/<uuid>/slots/
→ sees all weekly slots (Monday 10:00, Wednesday 14:00...)
→ clicks on Monday 10:00
        ↓
/doctors/<uuid>/slots/3/
→ sees a date picker
→ picks 2026-03-23 (a Monday)
        ↓
/doctors/<uuid>/slots/3/?date=2026-03-23
→ is_available = True  → shows book button
→ is_available = False → shows "already taken"
        ↓
patient clicks book → POST to /doctors/<uuid>/book/
"""
