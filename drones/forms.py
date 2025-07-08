from django import forms
from .models import DroneIncidentReport
from .models import *


#<---------------------------------------- INCIDENT REPORT FORM ---------------------------------------->

class GeneralInfoForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['report_date', 'reported_by', 'contact', 'role']
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
        }

class EventDetailsForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['event_date', 'event_time', 'location', 'event_type', 'description',
                  'injuries', 'injury_details', 'damage', 'damage_cost', 'damage_desc']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class EquipmentDetailsForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['drone_model', 'registration', 'controller', 'payload', 'battery', 'firmware']

class EnvironmentalConditionsForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['weather', 'wind', 'temperature', 'lighting']

class WitnessForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['witnesses', 'witness_details']

class ActionTakenForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['emergency', 'agency_response', 'scene_action', 'faa_report', 'faa_ref']

class FollowUpForm(forms.ModelForm):
    class Meta:
        model = DroneIncidentReport
        fields = ['cause', 'notes', 'signature', 'sign_date']
        widgets = {
            'sign_date': forms.DateInput(attrs={'type': 'date'}),
        }



#<---------------------------------------- GENERAL DOCs/SOP FORMS / SOPs ---------------------------------------->

class SOPDocumentForm(forms.ModelForm):
    class Meta:
        model = SOPDocument
        fields = ['title', 'description', 'file']


class GeneralDocumentForm(forms.ModelForm):
    class Meta:
        model = GeneralDocument
        fields = ['title', 'category', 'description', 'file']




#<---------------------------------------- FLIGHT LOG FORMS ---------------------------------------->


class FlightLogCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Flight Log CSV", widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))



#<---------------------------------------- EQUIPMENT FORMS ---------------------------------------->

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'brand', 'model', 'serial_number', 'date_purchased', 'cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_purchased': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }


#<---------------------------------------- DRONE FORMS ---------------------------------------->


class DroneForm(forms.ModelForm):
    class Meta:
        model = Drone
        fields = [
            'model',
            'nickname',
            'serial_number',
            'faa_number',
            'faa_certificate',
            'faa_experiation',
            'date_purchased'
        ]
        widgets = {
            'faa_experiation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_purchased': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'model': 'Drone Model',
            'nickname': 'Nickname',
            'serial_number': 'Serial Number',
            'faa_number': 'FAA Registration Number',
            'faa_certificate': 'FAA Registration Certificate (PDF/Image)',
            'faa_experiation': 'FAA Certificate Expiration',
            'date_purchased': 'Date Purchased',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
