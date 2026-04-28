from django.contrib import admin
from .models import *

# Register your models here.


admin.site.register(Appointment)
admin.site.register(PatientHistory)
admin.site.register(WeeklySlot)
admin.site.register(MedicalNote)
admin.site.register(BlockedDate)
