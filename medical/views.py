from django.shortcuts import render, get_object_or_404, redirect
from .models import Appointment, MedicalNote, PatientHistory
from django.contrib import messages



# helper functions to to extract from the User object whether it is a patient or a doctor.
def get_patient(user):
    try:
        return user.patient  # works if user is a patient
    except Exception:
        return None          # returns None if they're not a patient
def get_doctor(user):
    try:
        return user.doctor  
    except Exception:
        return None          


def appointment_detail(request, appointment_uuid):
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)
    patient = get_patient(request.user)
    doctor = get_doctor(request.user)

    is_the_patient = patient and appointment.patient == patient
    is_the_doctor = doctor and appointment.doctor == doctor

    if not (is_the_patient or is_the_doctor): # the logged in user is neither a patient nor a doctor
        messages.error(request, "You don't have access to this appointment.")
        return redirect('home')

    note = getattr(appointment, 'note', None)  

    # still have to create the template medical/appointement_detail.html
    return render(request, 'medical/appointment_detail.html', {
        'appointment': appointment, 
        'note': note,
        'is_the_patient': is_the_patient,
        'is_the_doctor': is_the_doctor,
    })


def confirm_appointment(request, appointment_uuid):
    pass 


    
     
    


    





