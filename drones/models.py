from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator



DRONE_MODEL_CHOICES = [
    ('Air 3S', 'Air 3s'),
    ('Avata 2', 'Avata 2'),
    ('Mavic 3 Pro', 'Mavic 3 Pro'),
    ('Mavic 3 Classic', 'Mavic 3 Classic'),
    ('Air 2S', 'Air 2S'),
    ('Mini 3 Pro', 'Mini 3 Pro'),
    ('Inspire 2', 'Inspire 2'),
    ('Other', 'Other'),
]

class Drone(models.Model):
    model            = models.CharField(max_length=100, choices=DRONE_MODEL_CHOICES, default='Other')
    nickname         = models.CharField(max_length=50, unique=True, blank=True)
    serial_number    = models.CharField(max_length=50, unique=True, blank=True)
    faa_number       = models.CharField(max_length=50, unique=True, blank=True)
    faa_certificate = models.FileField(
        upload_to='registrations/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True,
        null=True,
    )

    faa_experiation  = models.DateTimeField()
    date_purchased   = models.DateTimeField()

    def __str__(self):
        return self.model or f"{self.model} ({self.nickname}) ({self.faa_experiation})"



class Equipment(models.Model):
    name             = models.CharField(max_length=100)
    brand            = models.CharField(max_length=100)
    model            = models.CharField(max_length=100)
    serial_number    = models.CharField(max_length=100)
    date_purchased   = models.DateField()
    cost             = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.brand} {self.model}"

    

class DroneIncidentReport(models.Model):
    report_date = models.DateField()
    reported_by = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    role = models.CharField(max_length=100)

    event_date = models.DateField()
    event_time = models.TimeField()
    location = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20)
    description = models.TextField()
    injuries = models.BooleanField(default=False)
    injury_details = models.TextField(blank=True)
    damage = models.BooleanField(default=False)
    damage_cost = models.CharField(max_length=100, blank=True)
    damage_desc = models.TextField(blank=True)

    drone_model = models.CharField(max_length=100)
    registration = models.CharField(max_length=100)
    controller = models.CharField(max_length=100)
    payload = models.CharField(max_length=100)
    battery = models.CharField(max_length=50)
    firmware = models.CharField(max_length=100)

    weather = models.CharField(max_length=100)
    wind = models.CharField(max_length=50)
    temperature = models.CharField(max_length=50)
    lighting = models.CharField(max_length=100)

    witnesses = models.BooleanField(default=False)
    witness_details = models.TextField(blank=True)

    emergency = models.BooleanField(default=False)
    agency_response = models.TextField(blank=True)
    scene_action = models.TextField(blank=True)
    faa_report = models.BooleanField(default=False)
    faa_ref = models.CharField(max_length=100, blank=True)

    cause = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    signature = models.CharField(max_length=100)
    sign_date = models.DateField()

    def __str__(self):
        return f"{self.report_date} - {self.reported_by}"


class SOPDocument(models.Model):
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file        = models.FileField(upload_to='sop_docs/')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class GeneralDocument(models.Model):
    CATEGORY_CHOICES = [
        ('Insurance', 'Insurance'),
        ('FAA', 'FAA Waivers'),
        ('Registrations', 'Drone Registrations'),
        ('Event', 'Event Instructions'),
        ('Policies', 'Policies'),
        ('Compliance', 'Compliance'),
        ('Legal', 'Legal'),
        ('Other', 'Other'),
    ]

    title       = models.CharField(max_length=255)
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    file        = models.FileField(upload_to='general_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"




class FlightLog(models.Model):
    flight_date = models.DateField()
    flight_title = models.CharField(max_length=200, blank=True)
    flight_description = models.TextField(blank=True)
    pilot_in_command = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    takeoff_latlong = models.CharField(max_length=100, blank=True)
    takeoff_address = models.CharField(max_length=255, blank=True)
    landing_time = models.TimeField(null=True, blank=True)
    air_time = models.DurationField(null=True, blank=True)
    above_sea_level_ft = models.FloatField(null=True, blank=True)
    drone_name = models.CharField(max_length=100, blank=True)
    drone_type = models.CharField(max_length=100, blank=True)
    drone_serial = models.CharField(max_length=100, blank=True)
    drone_reg_number = models.CharField(max_length=100, blank=True)
    flight_app = models.CharField(max_length=100, blank=True)
    remote_id = models.CharField(max_length=100, blank=True)
    battery_name = models.CharField(max_length=100, blank=True)
    battery_serial_printed = models.CharField(max_length=100, blank=True)
    battery_serial_internal = models.CharField(max_length=100, blank=True)
    takeoff_battery_pct = models.IntegerField(null=True, blank=True)
    takeoff_mah = models.IntegerField(null=True, blank=True)
    takeoff_volts = models.FloatField(null=True, blank=True)
    landing_battery_pct = models.IntegerField(null=True, blank=True)
    landing_mah = models.IntegerField(null=True, blank=True)
    landing_volts = models.FloatField(null=True, blank=True)
    max_altitude_ft = models.FloatField(null=True, blank=True)
    max_distance_ft = models.FloatField(null=True, blank=True)
    max_battery_temp_f = models.FloatField(null=True, blank=True)
    max_speed_mph = models.FloatField(null=True, blank=True)
    total_mileage_ft = models.FloatField(null=True, blank=True)
    signal_score = models.FloatField(null=True, blank=True)
    max_compass_rate = models.FloatField(null=True, blank=True)
    avg_wind = models.FloatField(null=True, blank=True)
    max_gust = models.FloatField(null=True, blank=True)
    signal_losses = models.IntegerField(null=True, blank=True)
    ground_weather_summary = models.CharField(max_length=255, blank=True)
    ground_temp_f = models.FloatField(null=True, blank=True)
    visibility_miles = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.CharField(max_length=50, blank=True)
    cloud_cover = models.CharField(max_length=100, blank=True)
    humidity_pct = models.IntegerField(null=True, blank=True)
    dew_point_f = models.FloatField(null=True, blank=True)
    pressure_inhg = models.FloatField(null=True, blank=True)
    rain_rate = models.CharField(max_length=50, blank=True)
    rain_chance = models.CharField(max_length=50, blank=True)
    sunrise = models.CharField(max_length=50, blank=True)
    sunset = models.CharField(max_length=50, blank=True)
    moon_phase = models.CharField(max_length=50, blank=True)
    moon_visibility = models.CharField(max_length=50, blank=True)
    photos = models.IntegerField(null=True, blank=True)
    videos = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.flight_title or 'Flight'} on {self.flight_date}"