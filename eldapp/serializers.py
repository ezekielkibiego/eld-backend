from rest_framework import serializers
from .models import Trip, ELDLog


class TripSerializer(serializers.ModelSerializer):
    """
    Serializer for the Trip model.
    Handles serialization and deserialization of Trip data.
    """
    class Meta:
        model = Trip
        fields = [
            'id', 'current_location', 'pickup_location', 'dropoff_location',
            'current_cycle_used', 'distance', 'estimated_duration',
            'fuel_stops', 'created_at'
        ]
        read_only_fields = ['id', 'distance', 'estimated_duration', 'fuel_stops', 'created_at']


class ELDLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the ELDLog model.
    Handles serialization and deserialization of ELD Log data.
    """
    class Meta:
        model = ELDLog
        fields = [
            'id', 'trip', 'day', 'activity_type', 'start_time', 
            'end_time', 'location', 'hours'
        ]
        read_only_fields = ['id']
