from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from users.managers import CustomUserManager
from users.validators import validate_phone_number
import os
from cloudinary.models import CloudinaryField
from uuid import uuid4


blood_type_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]


def upload_avatar_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"avatars/{instance.user.id}_{uuid4().hex}.{ext}"

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('donor', 'Donor'),
        ('recipient', 'Recipient'),
        ('both', 'Both'),
    ]
    username = None  
    first_name = models.CharField(max_length=150, blank=True,null=True)
    last_name = models.CharField(max_length=150, blank=True,null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, validators=[validate_phone_number])
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='both')
    address = models.TextField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    last_donation_date = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    blood_type = models.CharField(max_length=3, choices=blood_type_CHOICES, null=True, blank=True)
    health_conditions = models.TextField(blank=True)
    # avatar = models.ImageField(upload_to=upload_avatar_path, null=True, blank=True)
    avatar = CloudinaryField('image', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

