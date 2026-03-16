from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
"""
class WeeklySlot(models.Model):
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
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"Dr.{self.doctor.last_name} — {self.get_day_of_week_display()} {self.start_time}"
"""

class Appointment(models.Model):
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
        # Core business rule: a doctor can't have two bookings at same time
        unique_together = ('doctor', 'date', 'time_slot')
        ordering = ['-date', '-time_slot']

    def __str__(self):
        return f"{self.patient} → Dr.{self.doctor.last_name} | {self.date} {self.time_slot} [{self.status}]"


class MedicalNote(models.Model):
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
    """
    at = models.DateTimeField(auto_now_add=True)
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
    if instance.status == 'completed':
        PatientHistory.objects.get_or_create(
            appointment=instance,
            defaults={'patient': instance.patient}
        )