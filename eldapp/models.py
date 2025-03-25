from django.db import models


class Trip(models.Model):
    """
    Trip Model:
    Represents a trip taken by a driver from a current location to a drop-off location with a specified pickup location.
    Includes fields for tracking the trip's progress, distance, duration, and necessary fuel stops.
    """
    current_location = models.CharField(max_length=255, help_text="Starting location of the trip.")
    pickup_location = models.CharField(max_length=255, help_text="Location where the cargo is picked up.")
    dropoff_location = models.CharField(max_length=255, help_text="Final destination of the trip.")
    current_cycle_used = models.FloatField(help_text="Hours already used in the current 70-hour/8-day cycle.")
    distance = models.FloatField(null=True, blank=True, help_text="Total trip distance in miles.")
    estimated_duration = models.FloatField(null=True, blank=True, help_text="Estimated duration of the trip in hours.")
    fuel_stops = models.IntegerField(default=0, help_text="Number of fueling stops required during the trip.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the trip was created.")

    def __str__(self):
        return f"Trip from {self.current_location} to {self.dropoff_location}"


class ELDLog(models.Model):
    """
    ELDLog Model:
    Logs different activities for a trip such as driving, resting, fueling, pickup, and drop-off.
    Supports logging activities for multiple days, in compliance with Hours of Service (HOS) rules.
    """
    ACTIVITY_CHOICES = [
        ('Driving', 'Driving'),
        ('Resting', 'Resting'),
        ('Fueling', 'Fueling'),
        ('Pickup', 'Pickup'),
        ('Dropoff', 'Dropoff'),
    ]

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Reference to the associated trip."
    )
    day = models.PositiveIntegerField(help_text="Day number of the trip (1 to 8, based on 70-hour/8-day cycle).")
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_CHOICES,
        help_text="Type of activity being logged (e.g., Driving, Resting)."
    )
    start_time = models.DateTimeField(help_text="Start time of the activity.")
    end_time = models.DateTimeField(help_text="End time of the activity.")
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Location associated with the activity (if applicable)."
    )
    hours = models.FloatField(help_text="Total hours spent on the activity.")

    def __str__(self):
        return f"Log: {self.activity_type} on Day {self.day} - {self.hours} hours"
