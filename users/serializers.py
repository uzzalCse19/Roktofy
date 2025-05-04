from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer

User = get_user_model()
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = [
            'email','first_name', 'last_name', 'password', 'confirm_password', 'phone', 'user_type', 
            'address', 'age', 'last_donation_date', 'is_available', 'is_verified']
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            user_type=validated_data.get('user_type', 'both'),
            address=validated_data.get('address', ''),
            age=validated_data.get('age', 18),
            last_donation_date=validated_data.get('last_donation_date', None),
            is_available=validated_data.get('is_available', True),
            is_verified=validated_data.get('is_verified', False)
        )
        UserProfile.objects.create(user=user)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['is_verified'] = user.is_verified
        token['email'] = user.email
        return token

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    is_available = serializers.BooleanField(source='user.is_available', read_only=True)
    avatar=serializers.ImageField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'phone', 'user_type', 'blood_group',
            'health_conditions', 'avatar', 'is_available'
        ]
    def validate_blood_group(self, value):
        valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value and value not in valid_groups:
            raise serializers.ValidationError("Invalid blood group")
        return value
    
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'user_type', 'address', 'age',
            'last_donation_date', 'is_available', 'is_verified', 'profile'
        ]
        read_only_fields = ['is_verified']
        ref_name = 'CustomUserSerializer' 


class PublicDonorSerializer(serializers.ModelSerializer):
    blood_group = serializers.CharField(source='profile.blood_group')
    avatar = serializers.ImageField(source='profile.avatar', allow_null=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'address', 'age', 'blood_group', 'avatar']


class BloodRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    blood_group = serializers.CharField(max_length=5)
    message = serializers.CharField(max_length=500)
    required_date = serializers.DateField()

    class Meta:
        ref_name = "UserBloodRequest"  


class DonorListSerializer(serializers.ModelSerializer):
    blood_group = serializers.CharField(source='profile.blood_group')
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'blood_group','address','last_donation_date','is_available']
    def get_full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name if name else obj.email







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
                  'last_name', 'address', 'phone']
