from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from django.conf import settings


BLOOD_GROUP_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]
class BloodRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units_needed = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    hospital = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    urgency = models.CharField( max_length=20,choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],default='normal')
    additional_info = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    needed_by = models.DateTimeField()
    
    def __str__(self):
        return f"Request for {self.blood_group} by {self.requester.email}"
    class Meta:
        ordering = ['-created_at']


class Donation(models.Model):
    donor = models.ForeignKey( User, on_delete=models.CASCADE, related_name='donations')
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='donations')
    donation_date = models.DateTimeField(auto_now_add=True)
    units_donated = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.donor.email} donated {self.units_donated} unit(s)"

    class Meta:
        unique_together = ('donor', 'request')  
        ordering = ['-donation_date']


class BloodEvent(models.Model):
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    message = models.TextField(blank=True,null=True)
    required_date = models.DateField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    accepted_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='accepted_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.creator.email} needs {self.blood_group} on {self.required_date}"
