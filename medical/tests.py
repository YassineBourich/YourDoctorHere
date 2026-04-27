from datetime import date, time, timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from medical.models import Appointment, BlockedDate, PatientHistory, WeeklySlot
from users.models import Doctor, Patient, Speciality, User


class MedicalWorkflowTests(TestCase):
    def setUp(self):
        self.speciality = Speciality.objects.create(
            name='Cardiology',
            description='Heart care',
        )
        self.patient_user = User.objects.create_user(
            email='patient@example.com',
            password='testpass123',
            entity='Patient',
            is_active=True,
        )
        self.doctor_user = User.objects.create_user(
            email='doctor@example.com',
            password='testpass123',
            entity='Doctor',
            is_active=True,
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            first_name='Sara',
            last_name='Patient',
            tel='0600000000',
            address='Patient Address',
            gender='FEMALE',
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Adam',
            last_name='Doctor',
            tel='0611111111',
            address='Doctor Address',
            specialty=self.speciality,
            license_number='DOC-001',
            consultation_fee='300.00',
            city='Casablanca',
            bio='Experienced specialist',
        )

    def test_completed_appointment_creates_history(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date.today() + timedelta(days=7),
            time_slot=time(10, 0),
            status='confirmed',
        )

        appointment.status = 'completed'
        appointment.save()

        self.assertTrue(PatientHistory.objects.filter(appointment=appointment).exists())

    def test_cancelled_appointment_does_not_block_rebooking_same_slot(self):
        appointment_date = date.today() + timedelta(days=7)
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=appointment_date,
            time_slot=time(11, 0),
            status='cancelled',
        )

        replacement = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=appointment_date,
            time_slot=time(11, 0),
            status='requested',
        )

        self.assertEqual(replacement.status, 'requested')

    def test_patient_can_search_doctors_in_medical_directory(self):
        self.client.force_login(self.patient_user)
        target_date = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)
        WeeklySlot.objects.create(
            doctor=self.doctor,
            day_of_week=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True,
        )

        response = self.client.get(reverse('medical_doctor_directory'), {
            'city': 'Casa',
            'date': target_date.isoformat(),
            'max_fee': '400.00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Adam Doctor')

    def test_patient_search_hides_doctor_when_selected_date_is_blocked(self):
        self.client.force_login(self.patient_user)
        target_date = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)
        WeeklySlot.objects.create(
            doctor=self.doctor,
            day_of_week=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True,
        )
        BlockedDate.objects.create(
            doctor=self.doctor,
            date=target_date,
            reason='Conference',
        )

        response = self.client.get(reverse('medical_doctor_directory'), {
            'date': target_date.isoformat(),
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Dr. Adam Doctor')

    def test_patient_dashboard_shows_requested_appointments(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date.today() + timedelta(days=5),
            time_slot=time(12, 0),
            status='requested',
        )
        self.client.force_login(self.patient_user)

        response = self.client.get(reverse('my_appointments'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Adam Doctor')
        self.assertContains(response, 'Requested')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ReminderCommandTests(TestCase):
    def setUp(self):
        speciality = Speciality.objects.create(
            name='Dermatology',
            description='Skin care',
        )
        self.patient_user = User.objects.create_user(
            email='patient-reminder@example.com',
            password='testpass123',
            entity='Patient',
            is_active=True,
        )
        self.doctor_user = User.objects.create_user(
            email='doctor-reminder@example.com',
            password='testpass123',
            entity='Doctor',
            is_active=True,
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            first_name='Nora',
            last_name='Patient',
            tel='0600000001',
            address='Reminder Patient Address',
            gender='FEMALE',
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Yassine',
            last_name='Doctor',
            tel='0611111112',
            address='Reminder Doctor Address',
            specialty=speciality,
            license_number='DOC-REM-001',
            consultation_fee='350.00',
            city='Rabat',
            bio='Reminder doctor',
        )

    def test_reminder_command_sends_email_for_upcoming_confirmed_appointment(self):
        appointment_at = timezone.localtime() + timedelta(hours=2)
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=appointment_at.date(),
            time_slot=appointment_at.time().replace(microsecond=0),
            status='confirmed',
        )
        stdout = StringIO()

        call_command('remind_upcoming_appointments', stdout=stdout)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Processed 1 upcoming confirmed appointment(s).', stdout.getvalue())
