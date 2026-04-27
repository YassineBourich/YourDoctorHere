from datetime import date

from django import forms

from .models import BlockedDate, MedicalNote, WeeklySlot


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


class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ['date', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date(self):
        blocked_date = self.cleaned_data['date']
        if blocked_date < date.today():
            raise forms.ValidationError("Blocked dates should be today or later.")
        return blocked_date


class DoctorSearchForm(forms.Form):
    specialty = forms.CharField(max_length=200, required=False)
    city = forms.CharField(required=False)
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    min_fee = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=10)
    max_fee = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=10)

    def clean(self):
        cleaned_data = super().clean()
        min_fee = cleaned_data.get('min_fee')
        max_fee = cleaned_data.get('max_fee')

        if min_fee is not None and max_fee is not None and min_fee > max_fee:
            raise forms.ValidationError("Minimum fee cannot be greater than maximum fee.")

        selected_date = cleaned_data.get('date')
        if selected_date and selected_date < date.today():
            raise forms.ValidationError("Search dates should be today or later.")

        return cleaned_data
