import django_filters
from core.models import BloodRequest

class BloodRequestFilter(django_filters.FilterSet):
    blood_type = django_filters.CharFilter(lookup_expr='iexact') 
    status = django_filters.CharFilter(lookup_expr='iexact')
    urgency = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = BloodRequest
        fields = ['blood_type', 'status', 'urgency']

import django_filters
from .models import Donation

class DonationFilter(django_filters.FilterSet):
    # Null-safe filters
    event_status = django_filters.CharFilter(field_name='event__status', lookup_expr='iexact')
    event_blood_type = django_filters.CharFilter(field_name='event__blood_type', lookup_expr='iexact')
    request_status = django_filters.CharFilter(field_name='request__status', lookup_expr='iexact')

    class Meta:
        model = Donation
        fields = ['event_status', 'event_blood_type', 'request_status']




