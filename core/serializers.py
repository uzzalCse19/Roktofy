from rest_framework import serializers
from core.models import BloodRequest, Donation,BloodEvent
from users.models import User
from django.utils import timezone
from datetime import timedelta

from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from .models import BloodRequest

class BloodRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    requester_phone = serializers.CharField(source='requester.phone', read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'requester', 'requester_email', 'requester_phone',
            'blood_type', 'units_needed', 'hospital', 'location',
            'urgency', 'additional_info', 'status', 'created_at', 'needed_by'
        ]
        extra_kwargs = {
            'requester': {'write_only': True},
            'needed_by': {'required': True},
            'urgency': {'default': 'normal'}
        }

    def validate_needed_by(self, value):
        if value < timezone.now() + timedelta(hours=1):
            raise serializers.ValidationError("Needed by time must be at least 1 hour from now.")
        return value

    def validate_units_needed(self, value):
        if value < 1:
            raise serializers.ValidationError("At least 1 unit is required.")
        return value

    def validate_blood_type(self, value):
        valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value not in valid_groups:
            raise serializers.ValidationError("Invalid blood group.")
        return value
    
from rest_framework import serializers
from core.models import Donation

# class DonationSerializer(serializers.ModelSerializer):
#     donor = serializers.SerializerMethodField(read_only=True)
#     request_info = serializers.SerializerMethodField(read_only=True)
#     request = serializers.PrimaryKeyRelatedField(
#         queryset=BloodRequest.objects.all(), write_only=True
#     )
#     units_donated = serializers.IntegerField(min_value=1, default=1)

#     class Meta:
#         model = Donation
#         fields = [
#             'id', 'donor', 'request', 'request_info', 'units_donated',
#             'donation_date', 'is_verified'
#         ]
#         read_only_fields = ['donation_date', 'is_verified', 'donor', 'request_info']

#     def get_donor(self, obj):
#         return {
#             'id': obj.donor.id,
#             'name': f"{obj.donor.first_name} {obj.donor.last_name}",
#             'email': obj.donor.email,
#             'phone': obj.donor.phone,
#             'blood_type': obj.donor.profile.blood_type if hasattr(obj.donor, 'profile') else None
#         }

#     def get_request_info(self, obj):
#         if not hasattr(obj, 'request'):
#             return None
#         return {
#             'id': obj.request.id,
#             'blood_type': obj.request.blood_type,
#             'hospital': obj.request.hospital,
#             'location': obj.request.location,
#             'urgency': obj.request.urgency,
#             'status': obj.request.status
#         }

#     def validate(self, data):
#         if data.get('units_donated', 1) < 1:
#             raise serializers.ValidationError(
#                 {"units_donated": "At least 1 unit must be donated."}
#             )
#         return data

# new add Donation Serializer
class DonationSerializer(serializers.ModelSerializer):
    donor = serializers.SerializerMethodField(read_only=True)
    request_info = serializers.SerializerMethodField(read_only=True)
    event_info = serializers.SerializerMethodField(read_only=True)  # New field
    
    # Keep existing request field but make it optional
    request = serializers.PrimaryKeyRelatedField(
        queryset=BloodRequest.objects.all(), 
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Add new event field
    event = serializers.PrimaryKeyRelatedField(
        queryset=BloodEvent.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    units_donated = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'request', 'event', 'request_info', 'event_info',
            'units_donated', 'donation_date', 'is_verified'
        ]
        read_only_fields = ['donation_date', 'is_verified', 'donor', 'request_info', 'event_info']

    # Keep existing get_donor method unchanged
    def get_donor(self, obj):
        return {
            'id': obj.donor.id,
            'name': f"{obj.donor.first_name} {obj.donor.last_name}",
            'email': obj.donor.email,
            'phone': obj.donor.phone,
            'blood_type': obj.donor.profile.blood_type if hasattr(obj.donor, 'profile') else None
        }

    # Keep existing request_info method unchanged
    def get_request_info(self, obj):
        if not obj.request:
            return None
        return {
            'id': obj.request.id,
            'blood_type': obj.request.blood_type,
            'hospital': obj.request.hospital,
            'location': obj.request.location,
            'urgency': obj.request.urgency,
            'status': obj.request.status
        }

    # Add new method for event info
    def get_event_info(self, obj):
        if not obj.event:
            return None
        return {
            'id': obj.event.id,
            'blood_type': obj.event.blood_type,
            'location': obj.event.location,
            'required_date': obj.event.required_date,
            'status': obj.event.status
        }

    def validate(self, data):
        # Keep existing units validation
        if data.get('units_donated', 1) < 1:
            raise serializers.ValidationError(
                {"units_donated": "At least 1 unit must be donated."}
            )
        
        # Add new validation for request/event exclusivity
        if not data.get('request') and not data.get('event'):
            raise serializers.ValidationError(
                "Either request or event must be specified."
            )
            
        if data.get('request') and data.get('event'):
            raise serializers.ValidationError(
                "Cannot specify both request and event."
            )
            
        return data

from .models import PaymentHistory

class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = ['amount', 'transaction_id', 'status', 'timestamp', 'first_name', 'last_name']

     



# new added


# from rest_framework import serializers
# from core.models import BloodEvent, Donation
# from users.models import User

# class BloodEventSerializer_new(serializers.ModelSerializer):
#     creator_email = serializers.EmailField(source='creator.email', read_only=True)
#     creator_name = serializers.SerializerMethodField()
#     is_creator = serializers.SerializerMethodField()
#     has_accepted = serializers.SerializerMethodField()
    
#     class Meta:
#         model = BloodEvent
#         fields = [
#             'id', 'blood_type', 'message', 'required_date', 'location',
#             'creator', 'creator_email', 'creator_name', 'status',
#             'created_at', 'is_creator', 'has_accepted'
#         ]
#         extra_kwargs = {
#             'creator': {'read_only': True},
#         }
    
#     def get_creator_name(self, obj):
#         return f"{obj.creator.first_name} {obj.creator.last_name}"
    
#     def get_is_creator(self, obj):
#         request = self.context.get('request')
#         return request.user == obj.creator if request else False
    
#     def get_has_accepted(self, obj):
#         request = self.context.get('request')
#         if request and request.user.is_authenticated:
#             return obj.accepted_by.filter(id=request.user.id).exists()
#         return False

# from rest_framework import serializers
# from core.models import BloodEvent, Donation
# from users.models import User

# class DonationSerializer_new(serializers.ModelSerializer):
#     donor_email = serializers.EmailField(source='donor.email', read_only=True)
#     donor_name = serializers.SerializerMethodField()
#     event_id = serializers.PrimaryKeyRelatedField(queryset=BloodEvent.objects.all(), write_only=True)
    
#     class Meta:
#         model = Donation
#         fields = ['id', 'donor', 'donor_email', 'donor_name', 'event', 'event_id', 
#                  'donation_date', 'units_donated', 'is_verified']
#         extra_kwargs = {
#             'donor': {'read_only': True},
#             'donation_date': {'read_only': True},
#             'event': {'read_only': True},
#         }
    
#     def get_donor_name(self, obj):
#         if obj.donor:
#             return f"{obj.donor.first_name} {obj.donor.last_name}"
#         return None
    
#     def create(self, validated_data):
#         # Remove event_id from validated_data as we'll use it to get the event
#         event_id = validated_data.pop('event_id')
#         event = BloodEvent.objects.get(id=event_id.id)
        
#         donation = Donation.objects.create(
#             donor=self.context['request'].user,
#             event=event,
#             **validated_data
#         )
#         return donation


# purno Serializer

# class DonationSerializer(serializers.ModelSerializer):
#     donor_email = serializers.EmailField(source='donor.email', read_only=True)
#     donor_phone = serializers.CharField(source='donor.phone', read_only=True)
#     request_blood_type = serializers.CharField(source='request.blood_type', read_only=True)
#     request_hospital = serializers.CharField(source='request.hospital', read_only=True)
#     donation_date = serializers.DateTimeField(read_only=True)

#     class Meta:
#         model = Donation
#         fields = [
#             'id', 'donor', 'donor_email', 'donor_phone', 'request',
#             'request_blood_type', 'request_hospital', 'units_donated',
#             'donation_date', 'is_verified'
#         ]
#         extra_kwargs = {
#             'donor': {'write_only': True},
#             'request': {'write_only': True},
#             'is_verified': {'read_only': True}
#         }
#     def validate_units_donated(self, value):
#         if value < 1:
#             raise serializers.ValidationError("At least 1 unit must be donated.")
#         return value
    
# class DonationSerializer(serializers.ModelSerializer):
#     donor_info = serializers.SerializerMethodField()
#     request_info = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Donation
#         fields = [
#             'id', 'units_donated', 'donation_date', 'is_verified',
#             'donor_info', 'request_info'
#         ]
#         read_only_fields = fields

#     def get_donor_info(self, obj):
#         return {
#             'id': obj.donor.id,
#             'email': obj.donor.email,
#             'phone': obj.donor.phone,
#             'name': f"{obj.donor.first_name} {obj.donor.last_name}"
#         }

#     def get_request_info(self, obj):
#         if not hasattr(obj, 'request'):
#             return None
#         return {
#             'blood_type': obj.request.blood_type,
#             'hospital': obj.request.hospital,
#             'urgency': obj.request.urgency
#         }



class BloodEventSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.email')
    accepted_by = serializers.SlugRelatedField(many=True,read_only=True,slug_field='email')

    class Meta:
        model = BloodEvent
        fields = ['id', 'blood_type', 'message', 'required_date','location', 'creator', 'accepted_by', 'created_at', 'status']
        read_only_fields = ['creator', 'accepted_by', 'created_at']
    
# contact/serializers.py
from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'


# new BloodEventSerializer

# serializers.py
# class BloodEventSerializer(serializers.ModelSerializer):
#     creator = serializers.ReadOnlyField(source='creator.email')
#     accepted_by = serializers.SlugRelatedField(many=True, read_only=True, slug_field='email')
#     is_accepted = serializers.SerializerMethodField()
#     can_accept = serializers.SerializerMethodField()

#     class Meta:
#         model = BloodEvent
#         fields = ['id', 'blood_type', 'message', 'required_date', 'location', 
#                  'creator', 'accepted_by', 'created_at', 'status',
#                  'is_accepted', 'can_accept']
#         read_only_fields = ['creator', 'accepted_by', 'created_at', 'status']

#     def get_is_accepted(self, obj):
#         request = self.context.get('request')
#         if request and request.user.is_authenticated:
#             return obj.accepted_by.filter(id=request.user.id).exists()
#         return False

#     def get_can_accept(self, obj):
#         request = self.context.get('request')
#         if request and request.user.is_authenticated:
#             return request.user != obj.creator
#         return False