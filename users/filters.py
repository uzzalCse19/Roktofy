import django_filters
from users.models import User
from django.db.models import Q

blood_type_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]
class UserFilter(django_filters.FilterSet):
    blood_type = django_filters.CharFilter(field_name='profile__blood_type', lookup_expr='iexact')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    class Meta:
        model = User
        fields = ['blood_type', 'is_available']

class DonorFilter(django_filters.FilterSet):
    blood_type = django_filters.ChoiceFilter( field_name='profile__blood_type', choices=blood_type_CHOICES,label='Filter by Blood Group')
    search = django_filters.CharFilter( method='custom_search', label='Search (name, email, address)')
    class Meta:
        model = User
        fields = ['blood_type']
        
    def custom_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(address__icontains=value)
        )
