from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from medical.models import Appointment


class Command(BaseCommand):
    help = "Send reminders for confirmed appointments happening in the next 24 hours."

    def handle(self, *args, **options):
        now = timezone.localtime()
        tomorrow = now + timedelta(days=1)

        upcoming_appointments = Appointment.objects.filter(
            status='confirmed',
            date__gte=now.date(),
            date__lte=tomorrow.date(),
        ).select_related('patient__user', 'doctor__user')

        reminder_count = 0
        for appointment in upcoming_appointments:
            appointment_at = timezone.make_aware(
                datetime.combine(appointment.date, appointment.time_slot),
                timezone.get_current_timezone(),
            )
            if not (now <= appointment_at <= tomorrow):
                continue

            reminder_count += 1
            subject = f"Upcoming appointment reminder: {appointment.date} {appointment.time_slot}"
            message = (
                f"Reminder for appointment on {appointment.date} at {appointment.time_slot} "
                f"between {appointment.patient} and {appointment.doctor}."
            )

            recipients = [
                appointment.patient.user.email,
                appointment.doctor.user.email,
            ]
            send_mail(
                subject,
                message,
                'noreply@yourdoctorhere.com',
                recipients,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reminder sent for appointment {appointment.uuid} to {', '.join(recipients)}"
                )
            )

        self.stdout.write(f"Processed {reminder_count} upcoming confirmed appointment(s).")
