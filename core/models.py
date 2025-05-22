from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
blood_type_CHOICES = [
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
    blood_type = models.CharField(max_length=3, choices=blood_type_CHOICES)
    units_needed = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    hospital = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    urgency = models.CharField( max_length=20,choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],default='normal')
    additional_info = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    needed_by = models.DateTimeField()
    
    def __str__(self):
        return f"Request for {self.blood_type} by {self.requester.email}"
    class Meta:
        ordering = ['-created_at']


# class Donation(models.Model):
#     donor = models.ForeignKey( User, on_delete=models.CASCADE, related_name='donations')
#     request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='donations')
#     donation_date = models.DateTimeField(auto_now_add=True)
#     units_donated = models.PositiveIntegerField(default=1)
#     is_verified = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.donor.email} donated {self.units_donated} unit(s)"

#     class Meta:
#         unique_together = ('donor', 'request')  
#         ordering = ['-donation_date']


class BloodEvent(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    blood_type = models.CharField(max_length=3, choices=blood_type_CHOICES)
    message = models.TextField(blank=True,null=True)
    required_date = models.DateField()
    location = models.CharField(max_length=255,null=True,blank=False) 
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    accepted_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='accepted_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending') 
    

    def __str__(self):
        return f"{self.creator.email} needs {self.blood_type} on {self.required_date}"

class Donation(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    request = models.ForeignKey(
        BloodRequest, 
        on_delete=models.CASCADE, 
        related_name='donations',
        null=True,  # Make nullable for event donations
        blank=True
    )
    event = models.ForeignKey(  # New field for events
        BloodEvent,
        on_delete=models.CASCADE,
        related_name='donations',
        null=True,
        blank=True
    )
    donation_date = models.DateTimeField(auto_now_add=True)
    units_donated = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ('donor', 'request'),  # Maintains existing constraint
            ('donor', 'event')    # New constraint for events
        ]
        ordering = ['-donation_date']


from django.db import models
from django.contrib.auth import get_user_model



class PaymentHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20)  # success, failed, canceled
    timestamp = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

# contact/models.py
from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} from {self.name}"
