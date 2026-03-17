from django.shortcuts import render, get_object_or_404, redirect
from urllib3 import request
from .models import Appointment, MedicalNote, PatientHistory, WeeklySlot
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users import entities
from users.models import Patient, Doctor
from datetime import date


# using login_required to make sure only logged in users can access otherwise you redirct to longin page
@login_required
def appointment_detail(request, appointment_uuid):
    patient = None
    doctor = None

    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)
    entity = request.user.entity

    if entity == entities.PATIENT:
        patient = Patient.objects.filter(user = request.user).first()
        
    
    elif entity == entities.DOCTOR:
        doctor = Doctor.objects.filter(user = request.user).first()


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

# same logic as confirm_appointment but for completing an appointment
@login_required
def complete_appointment(request, appointment_uuid):
    """doctor marks an appointment as completed and can add a medical note"""
    doctor  = None
    entity = request.user.entity
    
    if entity == entities.DOCTOR:
        doctor = Doctor.objects.filter(user = request.user).first()

    else: 
        messages.error(request, "Only doctors can confirm appointments.")
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

    patient = None
    doctor = None
    entity = request.user.entity

    if entity == entities.PATIENT:
        patient = Patient.objects.filter(user = request.user).first()
        
    
    elif entity == entities.DOCTOR:
        doctor = Doctor.objects.filter(user = request.user).first()


    is_the_patient = patient and appointment.patient == patient
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


# this view func will allow the doctor to publish his weekly slots.
@login_required
def doctor_slots(request, doctor_uuid):
    """Patient views a doctor's full weekly schedule."""
    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can view slots.")
        return redirect('home')

    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)

    # all recurring slots for this doctor, ordered by day and time
    slots = WeeklySlot.objects.filter(
        doctor=doctor,
        is_active=True
    ).order_by('day_of_week', 'start_time')

    return render(request, 'medical/doctor_slots.html', {
        'doctor': doctor,
        'slots': slots,
    })


@login_required
def slot_detail(request, doctor_uuid, slot_id):
    """
    Patient picks a date for a specific weekly slot
    and sees if it's available on that date.
    """
    from users.models import Doctor

    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can view slots.")
        return redirect('home')

    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)
    slot = get_object_or_404(WeeklySlot, id=slot_id, doctor=doctor)

    # get date from query param
    selected_date_str = request.GET.get('date')
    selected_date = None
    is_available = None

    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)

            # check the selected date actually falls on the right day of week
            if selected_date.weekday() != slot.day_of_week:
                messages.error(request, f"This slot is only available on {slot.get_day_of_week_display()}s.")
                selected_date = None
                is_available = None
            else:
                # check if already booked on that date
                is_available = not Appointment.objects.filter(
                    doctor=doctor,
                    date=selected_date,
                    time_slot=slot.start_time,
                    status='confirmed'
                ).exists()

        except ValueError:
            messages.error(request, "Invalid date.")

    return render(request, 'medical/slot_detail.html', {
        'doctor': doctor,
        'slot': slot,
        'selected_date': selected_date,
        'is_available': is_available,
    })


# this view func will allow the patinen to book an appointment with the doctor by lokcing a free weekly slot with him.
# patient enter the doctor's booking page, where he has also access to the doc's weekly free slots, he picks one and confirms the booking, then the system creates an appointment with status "confirmed" and the patient receives a confirmation message.
@login_required
def book_appointment(request, doctor_uuid):
    """
    When a patient is on the doctor_slots page, they see a list of available slots. They click one — that click should send a 
    POST request to book_appointment with the date and time of that slot.
    So book_appointment only needs to handle POST — no form page, no GET. The patient already made their choice on the slots page.
    """
    # only patients can book
    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can book appointments.")
        return redirect('home')

    patient = Patient.objects.filter(user=request.user).first()
    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)

    if request.method == 'POST':
        date = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        reason = request.POST.get('reason', '')

        # double check the slot isn't already taken
        # (two patients could try to book the same slot at the same time)
        already_booked = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            time_slot=time_slot,
            status='confirmed'
        ).exists()

        if already_booked:
            messages.error(request, "This slot was just taken. Please choose another.")
            return redirect('doctor_slots', doctor_uuid=doctor_uuid)

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date,
            time_slot=time_slot,
            reason=reason,
        )

        messages.success(request, "Appointment booked successfully.")
        return redirect('appointment_detail', appointment_uuid=appointment.uuid)

    # if someone hits this URL without POST, send them back to slots
    return redirect('doctor_slots', doctor_uuid=doctor_uuid)

@login_required
def add_note(request, appointment_uuid):
    pass


# for a doctor (i may add also provilege for patient)
@login_required
def my_history():
    pass    

# doctor specific views. i added them to handle adding, deleting a time slot by a Doctor.
@login_required
def my_slots():
    pass

@login_required
def add_slot():
    pass

@login_required
def delete_slot():
    pass




    
     


# I no longer need to confirm an appointemnt because I confirm it immediately after booking, but I'm keeping the code here in case I want to change this logic later.
"""
@login_required
def confirm_appointment(request, appointment_uuid):
    #doctor confirms a requested appointment 
    doctor  = None
    entity = request.user.entity

    if entity == entities.DOCTOR:
        doctor = Doctor.objects.filter(user = request.user).first()

    else: 
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

"""
    


    





