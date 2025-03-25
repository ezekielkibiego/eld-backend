from django.urls import path
from . import views
from .views import TripDetailView

urlpatterns = [
    path('', views.home, name='home'),

    path('trips/', views.TripCreateView.as_view(), name='create_trip'),
    path('trips/<int:trip_id>/logs/', views.ELDLogCreateView.as_view(), name='create_eld_logs'),
    path('trips/<int:trip_id>/', TripDetailView.as_view(), name='trip-detail'),

    path('trips/<int:trip_id>/csv/', views.TripLogsCSVView.as_view(), name='export_trip_csv'),
    path('trips/<int:trip_id>/pdf/', views.TripLogsPDFView.as_view(), name='export_trip_pdf'),
    path('trips/<int:trip_id>/json/', views.TripLogsJSONView.as_view(), name='export_trip_json'),
    
]
