# Generated by Django 5.1.7 on 2025-03-21 17:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_location', models.CharField(help_text='Starting location of the trip.', max_length=255)),
                ('pickup_location', models.CharField(help_text='Location where the cargo is picked up.', max_length=255)),
                ('dropoff_location', models.CharField(help_text='Final destination of the trip.', max_length=255)),
                ('current_cycle_used', models.FloatField(help_text='Hours already used in the current 70-hour/8-day cycle.')),
                ('distance', models.FloatField(blank=True, help_text='Total trip distance in miles.', null=True)),
                ('estimated_duration', models.FloatField(blank=True, help_text='Estimated duration of the trip in hours.', null=True)),
                ('fuel_stops', models.IntegerField(default=0, help_text='Number of fueling stops required during the trip.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the trip was created.')),
            ],
        ),
        migrations.CreateModel(
            name='ELDLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.PositiveIntegerField(help_text='Day number of the trip (1 to 8, based on 70-hour/8-day cycle).')),
                ('activity_type', models.CharField(choices=[('Driving', 'Driving'), ('Resting', 'Resting'), ('Fueling', 'Fueling'), ('Pickup', 'Pickup'), ('Dropoff', 'Dropoff')], help_text='Type of activity being logged (e.g., Driving, Resting).', max_length=50)),
                ('start_time', models.DateTimeField(help_text='Start time of the activity.')),
                ('end_time', models.DateTimeField(help_text='End time of the activity.')),
                ('location', models.CharField(blank=True, help_text='Location associated with the activity (if applicable).', max_length=255, null=True)),
                ('hours', models.FloatField(help_text='Total hours spent on the activity.')),
                ('trip', models.ForeignKey(help_text='Reference to the associated trip.', on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='eldapp.trip')),
            ],
        ),
    ]
