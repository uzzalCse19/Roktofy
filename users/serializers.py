from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer

User = get_user_model()

blood_type_CHOICES = [
    ('O+', 'O+'), ('O-', 'O-'),
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
]

# class UserProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email', read_only=True)
#     phone = serializers.CharField(source='user.phone', read_only=True)
#     user_type = serializers.CharField(source='user.user_type', read_only=True)
#     is_available = serializers.BooleanField(source='user.is_available', read_only=True)
#     avatar=serializers.ImageField(required=False, allow_null=True)
    
#     class Meta:
#         model = UserProfile
#         fields = [
#             'id', 'email', 'phone', 'user_type', 'blood_type',
#             'health_conditions', 'avatar', 'is_available'
#         ]
#     def validate_blood_type(self, value):
#         valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
#         if value and value not in valid_groups:
#             raise serializers.ValidationError("Invalid blood group")
#         return value
    
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
                  'last_name', 'address', 'phone']



class UserCreateSerializer_two(BaseUserCreateSerializer):
    blood_type = serializers.ChoiceField(
        choices=blood_type_CHOICES,
        required=True,
        write_only=True  # Blood type shouldn't be returned in response
    )
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'address', 'phone', 'age', 'user_type', 'blood_type'
        ]
    
    def create(self, validated_data):
        try:
            blood_type = validated_data.pop('blood_type')
            user = super().create(validated_data)
            
            # Create or update user profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'blood_type': blood_type}
            )
            
            return user
        except Exception as e:
            raise serializers.ValidationError(
                {"detail": f"Failed to create user profile: {str(e)}"}
            )

class UserSerializer_two(BaseUserSerializer):
    blood_type = serializers.SerializerMethodField()
    
    class Meta(BaseUserSerializer.Meta):
        ref_name = 'CustomUser'
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'address', 'phone', 'blood_type',
            'is_available', 'last_donation_date', 'user_type'
        ]
        read_only_fields = ['is_available', 'last_donation_date']  # If these should be read-only
    
    def get_blood_type(self, obj):
        """Safely get blood_type from profile if exists"""
        return obj.profile.blood_type if hasattr(obj, 'profile') else None

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