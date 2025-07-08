from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # Incident Reporting
    documents,
    incident_reporting_system,
    incident_report_list,
    incident_report_detail,
    IncidentReportWizard,
    incident_report_success,
    incident_report_pdf,

    # SOPs and Documents
    sop_list,
    sop_upload,
    general_document_list,
    upload_general_document,

    # Equipment
    equipment_list,
    equipment_create,
    equipment_edit,
    equipment_delete,

    # Drones
    drone_portal,
    drone_list,
    drone_detail,
    drone_create,
    drone_edit,
    drone_delete,
    drone_detail_pdf,

    # Flight Logs
    flightlog_list,
    flightlog_detail,
    upload_flightlog_csv,
    flightlog_edit,
    flightlog_delete,
    flightlog_pdf,
)

from .forms import (
    EventDetailsForm,
    GeneralInfoForm,
    EquipmentDetailsForm,
    EnvironmentalConditionsForm,
    WitnessForm,
    ActionTakenForm,
    FollowUpForm,
)

# Incident report wizard steps
wizard_forms = [
    ("event", EventDetailsForm),
    ("general", GeneralInfoForm),
    ("equipment", EquipmentDetailsForm),
    ("environment", EnvironmentalConditionsForm),
    ("witness", WitnessForm),
    ("action", ActionTakenForm),
    ("followup", FollowUpForm),
]

urlpatterns = [
    # Incident Reporting
    path('docs', documents, name='documents'),
    path('drone-portal/', drone_portal, name='drone_portal'),
    
    path('incident-reporting', incident_reporting_system, name='incident_reporting_system'),
    path('incidents/', incident_report_list, name='incident_report_list'),
    path('incidents/<int:pk>/', incident_report_detail, name='incident_detail'),
    path('report/new/', IncidentReportWizard.as_view(wizard_forms), name='submit_incident_report'),
    path('report/success/', incident_report_success, name='incident_report_success'),
    path('report/pdf/<int:pk>/', incident_report_pdf, name='incident_report_pdf'),

    # SOPs and General Documents
    path('sops/', sop_list, name='sop_list'),
    path('sops/upload/', sop_upload, name='sop_upload'),
    path('documents/', general_document_list, name='general_document_list'),
    path('documents/upload/', upload_general_document, name='upload_general_document'),

    # Equipment
    path('equipment/', equipment_list, name='equipment_list'),
    path('equipment/create/', equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/edit/', equipment_edit, name='equipment_edit'),
    path('equipment/<int:pk>/delete/', equipment_delete, name='equipment_delete'),

    # Drones
    path('drones/', drone_list, name='drone_list'),
    path('drones/create/', drone_create, name='drone_create'),
    path('drones/<int:pk>/edit/', drone_edit, name='drone_edit'),
    path('drones/<int:pk>/delete/', drone_delete, name='drone_delete'),
    path('drones/<int:pk>/pdf/', drone_detail_pdf, name='drone_detail_pdf'),
    path('drones/<int:pk>/', drone_detail, name='drone_detail'),

    # Flight Logs
    path('flightlogs/', flightlog_list, name='flightlog_list'),
    path('flight-upload/', upload_flightlog_csv, name='flightlog_upload'),
    path('flightlogs/<int:pk>/', flightlog_detail, name='flightlog_detail'),
    path('flightlogs/<int:pk>/edit/', flightlog_edit, name='flightlog_edit'),
    path('flightlogs/<int:pk>/delete/', flightlog_delete, name='flightlog_delete'),
    path('flightlogs/<int:pk>/pdf/', flightlog_pdf, name='flightlog_pdf'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
