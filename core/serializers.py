from rest_framework import serializers
from core.models import BloodRequest, Donation,BloodEvent
from users.models import User
from django.utils import timezone
from datetime import timedelta

class BloodRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    requester_phone = serializers.CharField(source='requester.phone', read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'requester', 'requester_email', 'requester_phone',
            'blood_group', 'units_needed', 'hospital', 'location',
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
    def validate_blood_group(self, value):
        valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value not in valid_groups:
            raise serializers.ValidationError("Invalid blood group.")
        return value

class DonationSerializer(serializers.ModelSerializer):
    donor_email = serializers.EmailField(source='donor.email', read_only=True)
    donor_phone = serializers.CharField(source='donor.phone', read_only=True)
    request_blood_group = serializers.CharField(source='request.blood_group', read_only=True)
    request_hospital = serializers.CharField(source='request.hospital', read_only=True)
    donation_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'donor_email', 'donor_phone', 'request',
            'request_blood_group', 'request_hospital', 'units_donated',
            'donation_date', 'is_verified'
        ]
        extra_kwargs = {
            'donor': {'write_only': True},
            'request': {'write_only': True},
            'is_verified': {'read_only': True}
        }
    def validate_units_donated(self, value):
        if value < 1:
            raise serializers.ValidationError("At least 1 unit must be donated.")
        return value
    
class BloodEventSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.email')
    accepted_by = serializers.SlugRelatedField(many=True,read_only=True,slug_field='email')

    class Meta:
        model = BloodEvent
        fields = ['id', 'blood_group', 'message', 'required_date', 'creator', 'accepted_by', 'created_at']
        read_only_fields = ['creator', 'accepted_by', 'created_at']


     
