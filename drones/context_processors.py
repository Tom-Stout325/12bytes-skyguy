from django.urls import reverse_lazy

def navigation(request):
    return {
        'drone_navigation': { 
            'home': reverse_lazy('drone_portal'),
            'profile': reverse_lazy('profile'),
            'flightlogs': reverse_lazy('flightlog_list'),
            'documents': reverse_lazy('general_document_list'),
            'incidents': reverse_lazy('incident_reporting_system'),
            'sop': reverse_lazy('sop_list'),
            'equipment': reverse_lazy('equipment_list'),
            'drones': reverse_lazy('drone_list'),
        }
    }