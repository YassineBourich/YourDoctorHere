from datetime import date, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BlockedDateForm, MedicalNoteForm, WeeklySlotForm
from .models import Appointment, BlockedDate, PatientHistory, WeeklySlot
from users import entities
from users.models import Doctor, Patient


def _current_patient(user):
    return Patient.objects.filter(user=user).first()


def _current_doctor(user):
    return Doctor.objects.filter(user=user).first()


@login_required
def appointment_detail(request, appointment_uuid):
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)
    patient = _current_patient(request.user)
    doctor = _current_doctor(request.user)

    is_the_patient = patient and appointment.patient == patient
    is_the_doctor = doctor and appointment.doctor == doctor

    if not (is_the_patient or is_the_doctor):
        messages.error(request, "You don't have access to this appointment.")
        return redirect('home')

    note = getattr(appointment, 'note', None)
    return render(request, 'medical/appointment_detail.html', {
        'appointment': appointment,
        'note': note,
        'is_the_patient': is_the_patient,
        'is_the_doctor': is_the_doctor,
        'can_confirm': is_the_doctor and appointment.status == 'requested',
        'can_complete': is_the_doctor and appointment.status == 'confirmed',
        'can_cancel': (is_the_patient or is_the_doctor) and appointment.status in ['requested', 'confirmed'],
        'can_add_note': is_the_doctor and appointment.status == 'completed',
    })


@login_required
def confirm_appointment(request, appointment_uuid):
    if request.method != 'POST':
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can confirm appointments.")
        return redirect('home')

    doctor = _current_doctor(request.user)
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid, doctor=doctor)

    if appointment.status != 'requested':
        messages.error(request, "Only requested appointments can be confirmed.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    appointment.status = 'confirmed'
    appointment.save()
    messages.success(request, "Appointment confirmed.")
    return redirect('appointment_detail', appointment_uuid=appointment_uuid)


@login_required
def complete_appointment(request, appointment_uuid):
    if request.method != 'POST':
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can complete appointments.")
        return redirect('home')

    doctor = _current_doctor(request.user)
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid, doctor=doctor)

    if appointment.status != 'confirmed':
        messages.error(request, "Only confirmed appointments can be completed.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    appointment.status = 'completed'
    appointment.save()
    messages.success(request, "Appointment marked as completed. You can now add the consultation note.")
    return redirect('add_note', appointment_uuid=appointment_uuid)


@login_required
def cancel_appointment(request, appointment_uuid):
    if request.method != 'POST':
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    appointment = get_object_or_404(Appointment, uuid=appointment_uuid)
    patient = _current_patient(request.user)
    doctor = _current_doctor(request.user)

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


@login_required
def doctor_slots(request, doctor_uuid):
    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can view slots.")
        return redirect('home')

    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)
    slots = WeeklySlot.objects.filter(
        doctor=doctor,
        is_active=True
    ).order_by('day_of_week', 'start_time')
    blocked_dates = doctor.blocked_dates.filter(date__gte=date.today()).order_by('date')

    return render(request, 'medical/doctor_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'blocked_dates': blocked_dates,
    })


@login_required
def slot_detail(request, doctor_uuid, slot_id):
    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can view slots.")
        return redirect('home')

    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)
    slot = get_object_or_404(WeeklySlot, id=slot_id, doctor=doctor, is_active=True)

    selected_date_str = request.GET.get('date')
    selected_date = None
    is_available = None

    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)

            if selected_date < date.today():
                messages.error(request, "Please choose a future date.")
                selected_date = None
                is_available = None
            elif BlockedDate.objects.filter(doctor=doctor, date=selected_date).exists():
                messages.error(request, "This doctor is unavailable on the selected date.")
                is_available = False
            elif selected_date.weekday() != slot.day_of_week:
                messages.error(request, f"This slot is only available on {slot.get_day_of_week_display()}s.")
                selected_date = None
                is_available = None
            else:
                is_available = not Appointment.objects.filter(
                    doctor=doctor,
                    date=selected_date,
                    time_slot=slot.start_time,
                ).exclude(status='cancelled').exists()
        except ValueError:
            messages.error(request, "Invalid date.")

    return render(request, 'medical/slot_detail.html', {
        'doctor': doctor,
        'slot': slot,
        'selected_date': selected_date,
        'is_available': is_available,
    })


@login_required
def book_appointment(request, doctor_uuid):
    if request.user.entity != entities.PATIENT:
        messages.error(request, "Only patients can book appointments.")
        return redirect('home')

    patient = _current_patient(request.user)
    doctor = get_object_or_404(Doctor, uuid=doctor_uuid)

    if request.method != 'POST':
        return redirect('doctor_slots', doctor_uuid=doctor_uuid)

    date_str = request.POST.get('date', '').strip()
    reason = request.POST.get('reason', '').strip()
    slot_id = request.POST.get('slot_id')
    time_slot_str = request.POST.get('time_slot', '').strip()

    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        messages.error(request, "Please provide a valid appointment date.")
        return redirect('doctor_slots', doctor_uuid=doctor_uuid)

    if selected_date < date.today():
        messages.error(request, "Appointments must be booked for a future date.")
        return redirect('doctor_slots', doctor_uuid=doctor_uuid)

    if BlockedDate.objects.filter(doctor=doctor, date=selected_date).exists():
        messages.error(request, "This doctor is unavailable on the selected date.")
        return redirect('doctor_slots', doctor_uuid=doctor_uuid)

    slot = None
    if slot_id:
        slot = get_object_or_404(
            WeeklySlot,
            id=slot_id,
            doctor=doctor,
            is_active=True,
        )
    elif time_slot_str:
        try:
            selected_time = time.fromisoformat(time_slot_str)
        except ValueError:
            messages.error(request, "Please choose a valid weekly slot.")
            return redirect('doctor_slots', doctor_uuid=doctor_uuid)

        slot = WeeklySlot.objects.filter(
            doctor=doctor,
            day_of_week=selected_date.weekday(),
            start_time=selected_time,
            is_active=True,
        ).first()

        if slot is None:
            messages.error(request, "That time does not match one of the doctor's active weekly slots.")
            return redirect('doctor_slots', doctor_uuid=doctor_uuid)
    else:
        messages.error(request, "Please choose a slot before booking.")
        return redirect('doctor_slots', doctor_uuid=doctor_uuid)

    if selected_date.weekday() != slot.day_of_week:
        messages.error(request, f"This slot is only available on {slot.get_day_of_week_display()}s.")
        return redirect('slot_detail', doctor_uuid=doctor_uuid, slot_id=slot.id)

    if Appointment.objects.filter(
        doctor=doctor,
        date=selected_date,
        time_slot=slot.start_time,
    ).exclude(status='cancelled').exists():
        messages.error(request, "This slot is no longer available.")
        return redirect('slot_detail', doctor_uuid=doctor_uuid, slot_id=slot.id)

    try:
        with transaction.atomic():
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=selected_date,
                time_slot=slot.start_time,
                reason=reason,
            )
    except IntegrityError:
        messages.error(request, "This slot was just taken. Please choose another.")
        return redirect('slot_detail', doctor_uuid=doctor_uuid, slot_id=slot.id)

    messages.success(request, "Appointment request sent successfully.")
    return redirect('appointment_detail', appointment_uuid=appointment.uuid)


@login_required
def add_note(request, appointment_uuid):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can add consultation notes.")
        return redirect('home')

    doctor = _current_doctor(request.user)
    appointment = get_object_or_404(Appointment, uuid=appointment_uuid, doctor=doctor)

    if appointment.status != 'completed':
        messages.error(request, "You can only add notes to completed appointments.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    note = getattr(appointment, 'note', None)
    form = MedicalNoteForm(request.POST or None, instance=note)

    if request.method == 'POST' and form.is_valid():
        medical_note = form.save(commit=False)
        medical_note.appointment = appointment
        medical_note.save()
        messages.success(request, "Medical note saved.")
        return redirect('appointment_detail', appointment_uuid=appointment_uuid)

    return render(request, 'medical/add_note.html', {
        'appointment': appointment,
        'form': form,
        'note': note,
    })


@login_required
def my_history(request):
    history_entries = PatientHistory.objects.select_related(
        'patient',
        'appointment',
        'appointment__doctor',
        'appointment__note',
    )

    if request.user.entity == entities.PATIENT:
        patient = _current_patient(request.user)
        history_entries = history_entries.filter(patient=patient)
    elif request.user.entity == entities.DOCTOR:
        doctor = _current_doctor(request.user)
        history_entries = history_entries.filter(appointment__doctor=doctor)
    else:
        messages.error(request, "This account cannot access consultation history.")
        return redirect('home')

    return render(request, 'medical/my_history.html', {
        'history_entries': history_entries,
    })


@login_required
def my_slots(request):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can manage weekly slots.")
        return redirect('home')

    doctor = _current_doctor(request.user)
    slots = WeeklySlot.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    blocked_dates = BlockedDate.objects.filter(doctor=doctor).order_by('date')

    return render(request, 'medical/my_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'blocked_dates': blocked_dates,
        'form': WeeklySlotForm(),
        'blocked_date_form': BlockedDateForm(),
    })


@login_required
def add_slot(request):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can add weekly slots.")
        return redirect('home')

    if request.method != 'POST':
        return redirect('my_slots')

    doctor = _current_doctor(request.user)
    form = WeeklySlotForm(request.POST)

    if form.is_valid():
        new_slot = form.save(commit=False)
        new_slot.doctor = doctor

        overlap_exists = WeeklySlot.objects.filter(
            doctor=doctor,
            day_of_week=new_slot.day_of_week,
        ).filter(
            start_time__lt=new_slot.end_time,
            end_time__gt=new_slot.start_time,
        ).exists()

        if overlap_exists:
            messages.error(request, "This slot overlaps with an existing weekly slot.")
        else:
            new_slot.save()
            messages.success(request, "Weekly slot added.")
            return redirect('my_slots')

    slots = WeeklySlot.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    blocked_dates = BlockedDate.objects.filter(doctor=doctor).order_by('date')
    return render(request, 'medical/my_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'blocked_dates': blocked_dates,
        'form': form,
        'blocked_date_form': BlockedDateForm(),
    })


@login_required
def add_blocked_date(request):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can add blocked dates.")
        return redirect('home')

    if request.method != 'POST':
        return redirect('my_slots')

    doctor = _current_doctor(request.user)
    form = BlockedDateForm(request.POST)

    if form.is_valid():
        blocked_date = form.save(commit=False)
        blocked_date.doctor = doctor
        try:
            blocked_date.save()
            messages.success(request, "Blocked date added.")
            return redirect('my_slots')
        except IntegrityError:
            messages.error(request, "That date is already blocked.")

    slots = WeeklySlot.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    blocked_dates = BlockedDate.objects.filter(doctor=doctor).order_by('date')
    return render(request, 'medical/my_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'blocked_dates': blocked_dates,
        'form': WeeklySlotForm(),
        'blocked_date_form': form,
    })


@login_required
def delete_slot(request, slot_id):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can delete weekly slots.")
        return redirect('home')

    if request.method != 'POST':
        return redirect('my_slots')

    doctor = _current_doctor(request.user)
    slot = get_object_or_404(WeeklySlot, id=slot_id, doctor=doctor)
    slot.delete()
    messages.success(request, "Weekly slot deleted.")
    return redirect('my_slots')


@login_required
def delete_blocked_date(request, blocked_date_id):
    if request.user.entity != entities.DOCTOR:
        messages.error(request, "Only doctors can delete blocked dates.")
        return redirect('home')

    if request.method != 'POST':
        return redirect('my_slots')

    doctor = _current_doctor(request.user)
    blocked_date = get_object_or_404(BlockedDate, id=blocked_date_id, doctor=doctor)
    blocked_date.delete()
    messages.success(request, "Blocked date removed.")
    return redirect('my_slots')
