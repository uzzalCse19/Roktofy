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


# new add 11:57

class DonationSerializer(serializers.ModelSerializer):
    donor = serializers.SerializerMethodField(read_only=True)
    request_info = serializers.SerializerMethodField(read_only=True)
    event_info = serializers.SerializerMethodField(read_only=True)
    
    # ✅ Add this line to show blood_type in response
    blood_type = serializers.SerializerMethodField(read_only=True)

    request = serializers.PrimaryKeyRelatedField(
        queryset=BloodRequest.objects.all(), 
        write_only=True,
        required=False,
        allow_null=True
    )
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
            'units_donated', 'donation_date', 'is_verified',
            'blood_type'  # ✅ Include here
        ]
        read_only_fields = ['donation_date', 'is_verified', 'donor', 'request_info', 'event_info', 'blood_type']

    def get_donor(self, obj):
        return {
            'id': obj.donor.id,
            'name': f"{obj.donor.first_name} {obj.donor.last_name}",
            'email': obj.donor.email,
            'phone': obj.donor.phone,
            'blood_type': obj.donor.profile.blood_type if hasattr(obj.donor, 'profile') else None
        }

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

    # ✅ Method to return blood_type from request or event
    def get_blood_type(self, obj):
        if obj.request and obj.request.blood_type:
            return obj.request.blood_type
        elif obj.event and obj.event.blood_type:
            return obj.event.blood_type
        return None

    def validate(self, data):
        if data.get('units_donated', 1) < 1:
            raise serializers.ValidationError(
                {"units_donated": "At least 1 unit must be donated."}
            )
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



