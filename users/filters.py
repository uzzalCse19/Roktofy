import django_filters
from users.models import User
from django.db.models import Q

BLOOD_GROUP_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]
class UserFilter(django_filters.FilterSet):
    blood_group = django_filters.CharFilter(field_name='profile__blood_group', lookup_expr='iexact')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    class Meta:
        model = User
        fields = ['blood_group', 'is_available']

class DonorFilter(django_filters.FilterSet):
    blood_group = django_filters.ChoiceFilter( field_name='profile__blood_group', choices=BLOOD_GROUP_CHOICES,label='Filter by Blood Group')
    search = django_filters.CharFilter( method='custom_search', label='Search (name, email, address)')
    class Meta:
        model = User
        fields = ['blood_group']
        
    def custom_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(address__icontains=value)
        )
