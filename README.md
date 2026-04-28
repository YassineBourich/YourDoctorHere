# YourDoctorHere

**Repository:** https://github.com/YassineBourich/YourDoctorHere

A Django-based healthcare appointment management platform that connects patients with doctors. Patients can search for doctors, view availability, and book appointments. Doctors can manage their weekly schedule, confirm bookings, and log medical notes.

---

## Features

### For Patients
- Register and verify account via email
- Search doctors by specialty, city, and consultation fee
- View a doctor's weekly availability and book a time slot
- Manage appointments (view, cancel)
- Access immutable consultation history

### For Doctors
- Define weekly recurring availability slots
- Block specific dates (vacations, sick days)
- Confirm or complete appointment requests
- Add medical notes to completed consultations
- View full patient consultation history

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5.2 |
| Database | SQLite (development) |
| API | Django REST Framework |
| Image Handling | Pillow |
| Country Fields | django-countries |
| Frontend | HTML/CSS/JS + Material Icons + Google Fonts |

---

## Project Structure

```
YourDoctorHere/
├── YourDoctorHere/         # Project settings and root URLs
│   ├── settings.py
│   └── urls.py
├── users/                  # Authentication, profiles (Patient & Doctor)
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── migrations/
│   ├── static/users/js/
│   │   ├── activation_pending.js
│   │   ├── profile.js
│   │   └── registration.js
│   └── templates/users/
│        ├──registration/
│        │  ├──login.html
│        │  └──register.html
│        ├──profiles/
│        │  ├──profile.html
│        │  ├──profile_edit.html
│        │  └──profile_delete.html
│        ├──password_reset/
│        │  ├──password_reset_confirm.html
│        │  └──password_reset_demand.html
│        ├──emails/
│        │  ├──activation_invalid.html
│        │  ├──email_verification_template.html
│        │  ├──password_reset_invalid.html
│        │  ├──password_reset_template.html
│        │  └──wait_for_activation.html
│        └──change_password.html
├── medical/                # Appointments, slots, history, medical notes
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── management/commands/remind_patient_appointment.py
│   └── templates/medical/
│       ├── add_note.html
│       ├── appointment_detail.html
│       ├── doctor_detail.html
│       ├── doctor_directory.html
│       ├── doctor_slots.html
│       ├── my_appointments.html
│       ├── my_history.html
│       ├── my_slots.html
│       └── slot_detail.html
├── templates/
│   ├── base.html
│   └── home.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── default_avatar.jpg
├── manage.py
└── requirements.txt
```

---

## Installation

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YassineBourich/YourDoctorHere
cd YourDoctorHere

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. (Optional) Create a superuser for admin access
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

---

## Configuration

Key settings in `YourDoctorHere/settings.py`:

| Setting | Default | Notes |
|---------|---------|-------|
| `DATABASE` | SQLite (`db.sqlite3`) | Replace with PostgreSQL for production |
| `EMAIL_BACKEND` | Console backend | Emails are printed to terminal; configure SMTP for production |
| `MEDIA_ROOT` | Project root | Where uploaded avatars are stored |
| `REST_FRAMEWORK` | JSON + Browsable API, pagination 10/page | Adjust as needed |

---

## Usage

### As a Patient

1. Register at `/registration/` — select "Patient" as your entity type.
2. Check your terminal (console email backend) for the verification link and activate your account.
3. Log in at `/login/`.
4. Go to **Find Doctors** (`/medical/doctors/`) to search and filter doctors.
5. Click a doctor to view their profile and available slots.
6. Select a slot and date, then confirm your booking.
7. Track your appointments under **My Appointments** (`/medical/appointments/mine/`).
8. View completed consultations under **History** (`/medical/patients/me/history/`).

### As a Doctor

1. Register at `/registration/` — select "Doctor" as your entity type.
2. Verify your account via the link in the terminal.
3. Log in and go to **My Slots** (`/medical/slots/`) to define your weekly availability.
4. Optionally block specific dates at `/medical/blocked-dates/add/`.
5. Review incoming appointment requests under **My Appointments**.
6. Confirm requests, then mark them as completed after the consultation.
7. Add medical notes to completed appointments.

---

## API Endpoints

Base path: no prefix (root-level)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login/` | Obtain auth token |
| GET | `/api/profile/me/` | Get current user profile |
| GET | `/api/profile/me/history/` | Get current user's consultation history |
| GET | `/api/doctors/` | List all doctors |

Authentication: Token-based (`Authorization: Token <token>`).

---

## Appointment Lifecycle

```
requested → confirmed → completed
     ↓           ↓
  cancelled   cancelled
```

- **requested**: Patient books a slot.
- **confirmed**: Doctor accepts the request.
- **completed**: Doctor marks the visit as done (can add medical notes).
- **cancelled**: Either party cancels before completion.

Completed appointments are automatically recorded in the immutable `PatientHistory` ledger via a Django signal.

---

## Data Models

### Users App
- **User**: Custom model using email as the login identifier; entity field is `Patient` or `Doctor`.
- **Patient**: Profile with birth date, gender; linked 1:1 to User.
- **Doctor**: Profile with specialty, license number, consultation fee, city, bio; linked 1:1 to User.

### Medical App
- **WeeklySlot**: Recurring availability template per day of week.
- **BlockedDate**: Date-specific exceptions to weekly slots.
- **Appointment**: Core booking record with status tracking.
- **MedicalNote**: Doctor's diagnosis/prescription linked to a completed appointment.
- **PatientHistory**: Immutable record created automatically on appointment completion.

---

## Security Notes

- UUIDs used for profile and appointment URLs to prevent enumeration.
- Atomic transactions prevent double-booking race conditions.
- Email verification required before first login.
- Session invalidated on password change.
- DB-level `UniqueConstraint` enforces slot exclusivity.

---

## Dependencies Guide

All dependencies are listed in `requirements.txt`. Below is a breakdown of each package and its role:

| Package | Version | Purpose |
|---------|---------|---------|
| `Django` | 5.2 | Core web framework — handles routing, ORM, templating, auth |
| `djangorestframework` | — | REST API support (token auth, serializers, viewsets) |
| `django-countries` | 8.2.0 | Provides a `CountryField` for storing nationalities on user profiles |
| `Pillow` | 12.1.1 | Image processing — required for handling avatar uploads (`ImageField`) |
| `asgiref` | 3.11.1 | ASGI support, required by Django internals |
| `sqlparse` | 0.5.5 | SQL query formatting, used internally by Django |
| `typing_extensions` | 4.15.0 | Backports of newer Python typing features, used by Django and DRF |
| `tzdata` | 2025.3 | Timezone data for accurate datetime handling across regions |

### Installing dependencies

```bash
pip install -r requirements.txt
```
