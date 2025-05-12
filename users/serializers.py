from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    is_available = serializers.BooleanField(source='user.is_available', read_only=True)
    avatar=serializers.ImageField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'phone', 'user_type', 'blood_type',
            'health_conditions', 'avatar', 'is_available'
        ]
    def validate_blood_type(self, value):
        valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value and value not in valid_groups:
            raise serializers.ValidationError("Invalid blood group")
        return value
    

# class UserCreateSerializer(BaseUserCreateSerializer):
#     class Meta(BaseUserCreateSerializer.Meta):
#         fields = [
#             'id', 'email', 'password', 'first_name', 'last_name',
#             'address', 'phone', 'age', 'user_type'
#         ]
blood_type_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]

class UserCreateSerializer(BaseUserCreateSerializer):
    blood_type = serializers.ChoiceField(choices=blood_type_CHOICES, required=False)

    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'address', 'phone', 'user_type', 'blood_type'
        ]

    def create(self, validated_data):
        # Extract blood_type safely
        blood_type = validated_data.pop('blood_type', None)

        # Create the user (User model)
        user = super().create(validated_data)

        # Check if UserProfile already exists
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        # If the UserProfile exists, update the blood_type
        if not created and blood_type:
            user_profile.blood_type = blood_type
            user_profile.save()

        # If blood_type is provided and UserProfile was created, save it
        if created and blood_type:
            user_profile.blood_type = blood_type
            user_profile.save()

        return user


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        ref_name = 'CustomUser'
        fields = ['id', 'email', 'first_name',
                  'last_name', 'address', 'phone']

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
        fields = ['id', 'full_name', 'email', 'blood_type','address','last_donation_date','is_available']
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




# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=8)
#     confirm_password = serializers.CharField(write_only=True, min_length=8)
#     class Meta:
#         model = User
#         fields = [
#             'email','first_name', 'last_name', 'password', 'confirm_password', 'phone', 'user_type', 
#             'address', 'age', 'last_donation_date', 'is_available', 'is_verified']
        
#     def validate(self, data):
#         if data['password'] != data['confirm_password']:
#             raise serializers.ValidationError("Passwords do not match.")
#         return data
#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
#         user = User.objects.create_user(
#             email=validated_data['email'],
#             password=validated_data['password'],
#             phone=validated_data.get('phone', ''),
#             user_type=validated_data.get('user_type', 'both'),
#             address=validated_data.get('address', ''),
#             age=validated_data.get('age', 18),
#             last_donation_date=validated_data.get('last_donation_date', None),
#             is_available=validated_data.get('is_available', True),
#             is_verified=validated_data.get('is_verified', True)
#         )
#         UserProfile.objects.create(user=user)
#         return user


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['user_type'] = user.user_type
#         token['is_verified'] = user.is_verified
#         token['email'] = user.email
#         return token