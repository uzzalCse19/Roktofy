import django_filters
from core.models import BloodRequest

class BloodRequestFilter(django_filters.FilterSet):
    blood_group = django_filters.CharFilter(lookup_expr='iexact') 
    status = django_filters.CharFilter(lookup_expr='iexact')
    urgency = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = BloodRequest
        fields = ['blood_group', 'status', 'urgency']





