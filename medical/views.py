from django.shortcuts import render, get_object_or_404, redirect
from urllib3 import request
from .models import Appointment, MedicalNote, PatientHistory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# using login_required to make sure only logged in users can access otherwise you redirct to longin page



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

@login_required
def appointment_detail(request, appointment_uuid):
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)
    entity = request.user.entity
    doctor = request.user.entity

    if entity == 'Patient':
        pass

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

@login_required
def confirm_appointment(request, appointment_uuid):
    """doctor confirms a requested appointment"""
    doctor = get_doctor(request.user)
    if not doctor:
        messages.error(request, "Only doctors can confirm appointments.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid, doctor=doctor)
    if appointment.status != 'requested':
        messages.error(request, "Only requested appointments can be confirmed.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)
    
    appointment.status = 'confirmed'
    appointment.save()
    messages.success(request, "Appointment confirmed.")
    return redirect('appointment_detail', appointment_uuid=appointment_uuid)


# same logic as confirm_appointment but for completing an appointment
@login_required
def complete_appointment(request, appointment_uuid):
    """doctor marks an appointment as completed and can add a medical note"""
    doctor = get_doctor(request.user)
    if not doctor:
        messages.error(request, "Only doctors can complete appointments.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid, doctor=doctor)
    if appointment.status != 'confirmed':
        messages.error(request, "Only confirmed appointments can be completed.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)
    
    appointment.status = 'completed'
    appointment.save()
    messages.success(request, "Appointment marked as completed.")
    return redirect('appointment_detail', appointment_uuid=appointment_uuid)

@login_required
def cancel_appointment(request, appointment_uuid):
    """patient or doctor can cancel an appointment"""
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)

    patient = get_patient(request.user)
    doctor = get_doctor(request.user)

    is_the_patient = patient and appointment.patient == patient # again this is to make sure that the logged in user is the patient of this appointment
    is_the_doctor = doctor and appointment.doctor == doctor

    if not (is_the_patient or is_the_doctor):
        messages.error(request, "You don't have access to this appointment.")
        return redirect('home')

    if appointment.status in ['completed', 'cancelled']:
        messages.error(request, "This appointment cannot be cancelled.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, "Appointment cancelled.")
    return redirect('appointment_detail', appointment_uuid=appointment_uuid)
    



    
     
    


    





