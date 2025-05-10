from django.shortcuts import render
from rest_framework import  viewsets,status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from core.models import  Donation,BloodRequest,BloodEvent
from core.serializers import BloodRequestSerializer,DonationSerializer,BloodEventSerializer
from core.filters import BloodRequestFilter
from core.paginations import BloodRequestPagination
from core.permissions import CanRequestBlood, CanDonateBlood
from users.permissions import IsVerifiedUser
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

User = get_user_model()

class BloodRequestViewSet(viewsets.ModelViewSet):
    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodRequestFilter
    pagination_class = BloodRequestPagination
    permission_classes = [IsVerifiedUser, CanRequestBlood]
    lookup_field = 'pk'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(requester=self.request.user)
        return queryset.select_related('requester')

    @action(detail=True, methods=['post'], permission_classes=[IsVerifiedUser, CanDonateBlood])
    def accept(self, request, pk=None):
        blood_request = self.get_object()
        donor = request.user
        if not donor.is_available:
            return Response(
                {'error': 'You are not currently available to donate'},status=status.HTTP_400_BAD_REQUEST)

        if donor.profile.blood_group != blood_request.blood_group:
            return Response({'error': 'Blood group mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        if blood_request.status == 'accepted':
            return Response({'error': 'This request has already been accepted'},status=status.HTTP_400_BAD_REQUEST )

        with transaction.atomic():
            Donation.objects.create( donor=donor,request=blood_request)
            blood_request.status = 'accepted'
            blood_request.save(update_fields=['status'])
        
            if donor.is_available:
                donor.is_available = False
                donor.save(update_fields=['is_available'])

        return Response(
            {'message': 'Request accepted successfully'}, 
            status=status.HTTP_200_OK
        )

class DonationViewSet(viewsets.ModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [IsVerifiedUser]
    filterset_fields = ['is_verified', 'request__status']
    search_fields = ['donor__email', 'request__blood_group']
    lookup_field = 'pk'

    def get_queryset(self):
        queryset = Donation.objects.select_related(
            'donor',
            'request',
            'request__requester'
        ).prefetch_related('donor__profile')

        if not self.request.user.is_staff:
            queryset = queryset.filter(donor=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_queryset().get(pk=kwargs['pk'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        dashboard = {}
        profile = getattr(user, 'profile', None)
        blood_group = profile.blood_group if profile else None
        dashboard['blood_group'] = blood_group
        if user.user_type in ['recipient', 'both']:
            recipient_data = BloodRequest.objects.filter(
                requester=user
            ).select_related('requester').order_by('-created_at') 
            dashboard['total_requests'] = recipient_data.count()
            dashboard['pending_requests'] = recipient_data.filter(status='pending').count()
            dashboard['my_requests'] = BloodRequestSerializer(
                recipient_data[:10],  
                many=True
            ).data

        if user.user_type in ['donor', 'both'] and blood_group:
            donations = Donation.objects.filter(
                donor=user
            ).select_related(
                'donor', 
                'request',
                'request__requester'
            ).order_by('-donation_date')
            
            verified_donations = donations.filter(is_verified=True)
            dashboard['completed_donations'] = verified_donations.count()
            dashboard['last_donation_date'] = verified_donations.first().donation_date if verified_donations.exists() else None
            dashboard['donation_history'] = DonationSerializer(
                donations[:10],  
                many=True
            ).data

            dashboard['available_requests'] = BloodRequestSerializer(
                BloodRequest.objects.filter(
                    status='pending',
                    blood_group=blood_group
                ).exclude(requester=user).select_related('requester')[:10], 
                many=True
            ).data

        return Response(dashboard)

    def post(self, request):
        user = request.user
        request_id = request.data.get('request_id')
        if not request_id:
            return Response({'error': 'Request ID required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                blood_request = BloodRequest.objects.select_for_update().get(
                    id=request_id, 
                    status='pending'
                )
                Donation.objects.create(
                    donor=user,
                    recipient=blood_request.requester,
                    blood_group=blood_request.blood_group,
                    request=blood_request,
                    status='accepted'
                )
                blood_request.status = 'accepted'
                blood_request.save(update_fields=['status'])
                if user.is_available:
                    user.is_available = False
                    user.save(update_fields=['is_available'])
            return Response({'message': 'Request accepted successfully'})
        except BloodRequest.DoesNotExist:
            return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)

class PaymentPlaceholderView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        pass
    def post(self,reques):
        pass
 


class BloodEventViewSet(viewsets.ModelViewSet):
    serializer_class = BloodEventSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        return BloodEvent.objects.exclude(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        event = self.get_object()
        if request.user == event.creator:
            return Response({'error': 'You cannot accept your own event.'}, status=status.HTTP_400_BAD_REQUEST)
        event.accepted_by.add(request.user)
        return Response({'success': 'You have accepted to donate blood for this event.'}, status=status.HTTP_200_OK)
