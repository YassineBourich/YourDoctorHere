from django import forms

from .models import MedicalNote, WeeklySlot


class WeeklySlotForm(forms.ModelForm):
    class Meta:
        model = WeeklySlot
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class MedicalNoteForm(forms.ModelForm):
    class Meta:
        model = MedicalNote
        fields = ['diagnosis', 'prescription']
