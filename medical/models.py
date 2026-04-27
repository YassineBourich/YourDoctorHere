from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class WeeklySlot(models.Model):
    """
    Represents a doctor's generic availability for a given day of the week.
    This acts as a template for generating specific date-time slots, avoiding the need 
    to create thousands of individual slot records for every day in the year.
    """
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    doctor = models.ForeignKey(
        'users.Doctor',
        on_delete=models.CASCADE,
        related_name='weekly_slots'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # is_active allows doctors to temporarily disable a slot without deleting the record,
    # preserving historical context if needed later.
    is_active = models.BooleanField(default=True)

    class Meta:
        # A doctor cannot have duplicate overlapping slots starting at the same time on the same day.
        unique_together = ('doctor', 'day_of_week', 'start_time')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"Dr.{self.doctor.last_name} — {self.get_day_of_week_display()} {self.start_time}"


class BlockedDate(models.Model):
    """
    Allows doctors to handle exceptions to their WeeklySlots (e.g., holidays, sick leaves).
    Instead of deleting and recreating weekly slots, the system checks this table
    to block specific dates dynamically.
    """
    doctor = models.ForeignKey(
        'users.Doctor',
        on_delete=models.CASCADE,
        related_name='blocked_dates'
    )
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        # A doctor only needs to block a specific date once.
        unique_together = ('doctor', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.doctor} unavailable on {self.date}"


class Appointment(models.Model):
    """
    The core transactional record linking a Patient, a Doctor, and a specific time.
    """
    # UUID is used for URLs instead of sequential IDs to prevent users from guessing
    # and enumerating other patients' appointments (security by obscurity).
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # ghi bach nchre7, i identify the appointment by the patient and the doctor, that's why i have both Foreign Keys here.
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'users.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='requested'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time_slot']
        constraints = [
            # This constraint enforces data integrity at the database level.
            # It prevents the race condition where two patients try to book the same doctor
            # for the same date and time simultaneously. We ignore cancelled appointments
            # so the slot can be reused if an appointment is cancelled.
            models.UniqueConstraint(
                fields=['doctor', 'date', 'time_slot'],
                condition=~Q(status='cancelled'),
                name='unique_active_appointment_per_doctor_slot',
            ),
        ]

    def __str__(self):
        return f"{self.patient} → Dr.{self.doctor.last_name} | {self.date} {self.time_slot} [{self.status}]"


class MedicalNote(models.Model):
    """
    Isolates private medical data (diagnosis, prescriptions) from the scheduling metadata.
    This structure makes it easier to enforce stricter access controls on medical records later.
    """
    # OneToOne ensures an appointment can only have exactly one final medical note.
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='note'
    )
    diagnosis = models.TextField()
    prescription = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note — {self.appointment}"


class PatientHistory(models.Model):
    """
    Moved here from users app to avoid circular Foreign Key: 
    PatientHistory living in the users app creates a circular dependency problem: it needs
    to reference Appointment from your medical app, but medical already references users.
    
    This model acts as an immutable ledger of past consultations, maintaining history
    even if underlying models change, ensuring compliance with medical record keeping.
    """
    at = models.DateTimeField(auto_now_add=True)
    
    # PROTECT prevents accidental deletion of a patient if they have historical records,
    # ensuring medical history is preserved.
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.PROTECT,
        related_name='history'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name='history_entry'
    )

    class Meta:
        ordering = ['-at']

    def __str__(self):
        return f"History: {self.patient} @ {self.at:%Y-%m-%d}"



@receiver(post_save, sender=Appointment)
def create_history_on_completion(sender, instance, **kwargs):
    """
    Signal automating the archival process. When a doctor marks an appointment as completed,
    this automatically creates the corresponding PatientHistory record, ensuring
    the history log remains perfectly in sync with appointment statuses without
    relying on developers remembering to create it in the views.
    """
    if instance.status == 'completed':
        PatientHistory.objects.get_or_create(
            appointment=instance,
            defaults={'patient': instance.patient}
        )
