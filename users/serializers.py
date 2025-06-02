from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from core.models import BloodEvent,BloodRequest,Donation
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer

User = get_user_model()

blood_type_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]


    
from rest_framework import serializers
from users.models import UserProfile, User


class UserProfileSerializer(serializers.ModelSerializer):
    # Flattened User fields inside the profile serializer
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    phone = serializers.CharField(source='user.phone', required=False)
    user_type = serializers.CharField(source='user.user_type', required=False)
    address = serializers.CharField(source='user.address', required=False)
    age = serializers.IntegerField(source='user.age', required=False)
    last_donation_date = serializers.DateField(source='user.last_donation_date', required=False)
    is_available = serializers.BooleanField(source='user.is_available', required=False)
    is_verified = serializers.BooleanField(source='user.is_verified', required=False)
    email = serializers.EmailField(source='user.email', read_only=True)  # read-only

    class Meta:
        model = UserProfile
        fields = [
            'email',  # from user
            'first_name',
            'last_name',
            'phone',
            'user_type',
            'address',
            'age',
            'last_donation_date',
            'is_available',
            'is_verified',
            'blood_type',
            'health_conditions',
            'avatar',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        # Update fields from User model
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update fields from UserProfile model
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'address', 'phone', 'age', 'user_type'
        ]
class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        ref_name = 'CustomUser'
        fields = ['id', 'email', 'first_name',
                  'last_name', 'address', 'phone','is_staff']



class PublicDonorSerializer(serializers.ModelSerializer):
    blood_type = serializers.CharField(source='profile.blood_type')
    avatar = serializers.ImageField(source='profile.avatar', allow_null=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'address', 'age', 'blood_type', 'avatar']

class BloodRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    blood_type = serializers.CharField(max_length=5)
    message = serializers.CharField(max_length=500)
    required_date = serializers.DateField()

    class Meta:
        ref_name = "UserBloodRequest"  

class DonorListSerializer(serializers.ModelSerializer):
    blood_type = serializers.CharField(source='profile.blood_type')
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email',  'phone','blood_type','address','last_donation_date','is_available']
    def get_full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name if name else obj.email


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    blood_type = serializers.ChoiceField(choices=UserProfile._meta.get_field('blood_type').choices, required=False)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'password', 'phone', 'age', 'address', 'user_type', 
            'first_name', 'last_name', 'blood_type'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        blood_type = validated_data.pop('blood_type', None)

        # Create User instance
        user = super().create(validated_data)

        # Create associated UserProfile with blood_type
        UserProfile.objects.create(user=user, blood_type=blood_type)

        return user

# new added
from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['blood_type', 'health_conditions', 'avatar']  # Include avatar here

# new added 2

class UserUpdateSerializer_two(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'user_type', 'age', 'address', 'last_donation_date', 'is_available']



# new for Admin

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_active', 'user_type', 'first_name', 'last_name', 'phone', 'address']

# serializers.py

class AdminUserListSerializer(serializers.ModelSerializer):
    blood_type = serializers.CharField(source='profile.blood_type', default='')
    last_donation = serializers.DateField(source='last_donation_date', allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'user_type', 'blood_type',
            'last_donation', 'date_joined', 'last_login'
        ]

class AdminBloodRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodRequest
        fields = ['status', 'units_needed', 'hospital', 'location', 'urgency']

class AdminDonationSerializer(serializers.ModelSerializer):
    verification_notes = serializers.CharField(required=False)
    
    class Meta:
        model = Donation
        fields = ['is_verified', 'verification_notes', 'units_donated']

