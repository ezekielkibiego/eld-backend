import csv
import io
import requests
import math
from django.http import HttpResponse
from rest_framework import status, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Trip, ELDLog
from .serializers import TripSerializer, ELDLogSerializer
from decouple import config
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def home(request):
    """
    Simple welcome message to confirm the app is running.
    """
    return HttpResponse("Welcome to the ELD App!")


class TripCreateView(views.APIView):
    """
    Create a new trip and calculate route information using OpenRouteService API.
    """
    def get_coordinates(self, location):
        if "," in location:
            try:
                lat, lon = map(float, location.split(","))
                return [lon, lat]
            except ValueError:
                raise ValueError("Invalid coordinates format. Use 'latitude,longitude'.")
        
        geocode_url = "https://api.openrouteservice.org/geocode/search"
        headers = {"Authorization": config('OPENROUTESERVICE_API_KEY')}
        params = {"text": location}

        response = requests.get(geocode_url, headers=headers, params=params)
        if response.status_code == 200:
            geocode_data = response.json()
            if geocode_data.get('features'):
                return geocode_data['features'][0]['geometry']['coordinates']
        return None

    def post(self, request, *args, **kwargs):
        serializer = TripSerializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save()
            try:
                current_location = self.get_coordinates(trip.current_location)
                dropoff_location = self.get_coordinates(trip.dropoff_location)
                
                if not current_location or not dropoff_location:
                    return Response({"error": "Invalid locations provided."}, status=status.HTTP_400_BAD_REQUEST)
                
                url = "https://api.openrouteservice.org/v2/directions/driving-car"
                headers = {"Authorization": config('OPENROUTESERVICE_API_KEY')}
                payload = {"coordinates": [current_location, dropoff_location]}
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    route_data = response.json()
                    if 'routes' in route_data and len(route_data['routes']) > 0:
                        route = route_data['routes'][0]
                        trip.distance = route['summary']['distance'] / 1609.34  
                        trip.estimated_duration = route['summary']['duration'] / 3600  
                        trip.fuel_stops = max(0, math.floor(trip.distance / 1000))
                        trip.save()
                        
                        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)
                
                return Response({"error": "Failed to retrieve route."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ELDLogCreateView(views.APIView):
    """
    Generate ELD logs for a trip based on HOS rules:
    - 11-hour driving limit per day.
    - 14-hour driving window.
    - 34-hour restart if 60 hours are reached.
    - Fuel stops every 1,000 miles.
    """
    def post(self, request, *args, **kwargs):
        trip_id = request.data.get('trip_id')
        trip = Trip.objects.filter(id=trip_id).first()

        if not trip:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        logs = []
        total_hours = trip.current_cycle_used
        day = 1
        driving_window_hours = 0

        while total_hours < 70 and day <= 7:
            if total_hours >= 60:
                total_hours = 0  
                logs.append(
                    ELDLog.objects.create(
                        trip=trip,
                        day=day,
                        activity_type="Reset 34H",
                        start_time=timezone.now(),
                        end_time=timezone.now() + timezone.timedelta(hours=34),
                        hours=34,
                        location=trip.pickup_location if day == 1 else trip.dropoff_location,
                    )
                )
                day += 2  
                continue  

            if driving_window_hours >= 14:
                driving_window_hours = 0

            driving_hours = min(11, 70 - total_hours)
            driving_log = ELDLog.objects.create(
                trip=trip,
                day=day,
                activity_type="Driving",
                start_time=timezone.now(),
                end_time=timezone.now() + timezone.timedelta(hours=driving_hours),
                hours=driving_hours,
                location=trip.pickup_location if day == 1 else trip.dropoff_location,
            )
            logs.append(driving_log)
            total_hours += driving_hours
            driving_window_hours += driving_hours

            if driving_hours == 11 or driving_window_hours >= 14:
                resting_log = ELDLog.objects.create(
                    trip=trip,
                    day=day,
                    activity_type="Resting",
                    start_time=timezone.now(),
                    end_time=timezone.now() + timezone.timedelta(hours=10),
                    hours=10,
                    location=trip.dropoff_location if day == 1 else trip.pickup_location,
                )
                logs.append(resting_log)

            day += 1

        serialized_logs = ELDLogSerializer(logs, many=True)
        return Response(serialized_logs.data, status=status.HTTP_201_CREATED)
class TripLogsCSVView(views.APIView):
    """
    Export ELD logs of a trip as a CSV file with formatted dates.
    """
    def get(self, request, trip_id, *args, **kwargs):
        trip = Trip.objects.filter(id=trip_id).first()
        if not trip:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        logs = ELDLog.objects.filter(trip=trip)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="trip_{trip_id}_logs.csv"'

        writer = csv.writer(response)
        writer.writerow(['Day', 'Activity Type', 'Start Time', 'End Time', 'Hours'])

        for log in logs:
            writer.writerow([
                log.day,
                log.activity_type,
                log.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                log.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                log.hours
            ])

        return response



class TripLogsPDFView(views.APIView):
    """
    Export ELD logs of a trip as a PDF file with formatted dates.
    """
    def get(self, request, trip_id, *args, **kwargs):
        trip = Trip.objects.filter(id=trip_id).first()
        if not trip:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        logs = ELDLog.objects.filter(trip=trip)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="trip_{trip_id}_logs.pdf"'

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        data = [['Day', 'Activity Type', 'Start Time', 'End Time', 'Hours']]
        for log in logs:
            data.append([
                log.day,
                log.activity_type,
                log.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                log.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                log.hours
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        doc.build([table])
        response.write(buffer.getvalue())
        buffer.close()
        return response



class TripLogsJSONView(views.APIView):
    """
    Export ELD logs as JSON data.
    """
    def get(self, request, trip_id, *args, **kwargs):
        trip = Trip.objects.filter(id=trip_id).first()
        if not trip:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        logs = ELDLog.objects.filter(trip=trip)
        serialized_logs = ELDLogSerializer(logs, many=True)
        return Response(serialized_logs.data, status=status.HTTP_200_OK)

class TripDetailView(views.APIView):
    """
    API endpoint to fetch details of a trip.
    """
    def get(self, request, trip_id, *args, **kwargs):
        trip = Trip.objects.filter(id=trip_id).first()
        if not trip:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        trip_data = TripSerializer(trip).data
        return Response(trip_data, status=status.HTTP_200_OK)