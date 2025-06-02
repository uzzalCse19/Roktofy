from django.shortcuts import render
from rest_framework import  viewsets,status,permissions
from rest_framework.response import Response
from rest_framework.decorators import action,api_view
from django_filters.rest_framework import DjangoFilterBackend
from core.models import  Donation,BloodRequest,BloodEvent,PaymentHistory,ContactMessage
from core.serializers import BloodRequestSerializer,DonationSerializer,PaymentHistorySerializer,BloodEventSerializer,ContactMessageSerializer
from core.filters import BloodRequestFilter,DonationFilter
from core.paginations import BloodRequestPagination
from core.permissions import CanRequestBlood, CanDonateBlood
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings as main_settings
from django.http import HttpResponseRedirect
from django.db.models import Count
from django.utils import timezone
from users.models import User
import uuid
from rest_framework.generics import ListAPIView

User = get_user_model()





class BloodRequestViewSet(viewsets.ModelViewSet):
    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodRequestFilter
    pagination_class = BloodRequestPagination
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BloodRequest.objects.none()

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(requester=self.request.user)
        return queryset.select_related('requester')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def for_donor(self, request):
        donor = request.user
        if not donor.is_available:
            return Response([], status=200)

        blood_type = getattr(donor.profile, 'blood_type', None)
        if not blood_type:
            return Response([], status=200)

        requests = BloodRequest.objects.filter(
            blood_type=blood_type,
            status='pending'
        ).exclude(requester=donor).select_related('requester')

        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        blood_request = self.get_object()
        donor = request.user

        if blood_request.status == 'accepted':
            donation = Donation.objects.filter(donor=donor, request=blood_request).first()
            if not donation:
                return Response({'error': 'This request was accepted by someone else.'}, status=400)

            donation.delete()
            blood_request.status = 'pending'
            blood_request.save(update_fields=['status'])
            donor.is_available = True
            donor.save(update_fields=['is_available'])

        return Response({'message': 'Request cancelled successfully'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        blood_request = self.get_object()
        donor = request.user

        if not donor.is_available:
            return Response(
                {'error': 'You are not currently available to donate'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if donor.profile.blood_type != blood_request.blood_type:
            return Response(
                {'error': 'Blood group mismatch'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if blood_request.status == 'accepted':
            return Response(
                {'error': 'This request has already been accepted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            Donation.objects.create(donor=donor, request=blood_request)
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
    permission_classes = [IsAuthenticated]
    
    filterset_class = DonationFilter 
    
    # Add event__blood_type to existing search
    search_fields = [
        'donor__email', 
        'request__blood_type',
        'event__blood_type'
    ]
    lookup_field = 'pk'

    def get_queryset(self):
        queryset = Donation.objects.select_related(
            'donor',
            'request',
            'request__requester',
            'event',  # New relation
            'event__creator'  # New relation
        ).prefetch_related('donor__profile')

        if not self.request.user.is_staff:
            queryset = queryset.filter(donor=self.request.user)
        return queryset

    # Keep perform_create unchanged - it will work with new serializer
    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)

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
    

class BloodEventViewSet(viewsets.ModelViewSet):
    serializer_class = BloodEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BloodEvent.objects.exclude(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_events(self, request):
        events = BloodEvent.objects.filter(creator=request.user)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        event = self.get_object()
        if request.user == event.creator:
            return Response({'error': 'You cannot accept your own event.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create donation record
        donation = Donation.objects.create(
            donor=request.user,
            event=event,
            units_donated=1
        )
        
        # Add user to accepted_by
        event.accepted_by.add(request.user)
        
        return Response({
            'success': 'You have accepted to donate blood for this event.',
            'donation_id': donation.id
        }, status=status.HTTP_200_OK)
    

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dashboard = {}

        # Get user profile and blood type if available
        profile = getattr(user, 'profile', None)
        blood_type = profile.blood_group if profile else None
        dashboard['blood_type'] = blood_type

        # Recipient Dashboard Info
        if user.user_type in ['recipient', 'both']:
            recipient_requests = BloodRequest.objects.filter(
                requester=user
            ).select_related('requester').order_by('-created_at')

            dashboard['total_requests'] = recipient_requests.count()
            dashboard['pending_requests'] = recipient_requests.filter(status='pending').count()
            dashboard['my_requests'] = BloodRequestSerializer(
                recipient_requests[:10], many=True
            ).data

        # Donor Dashboard Info
        if user.user_type in ['donor', 'both'] and blood_type:
            donations = Donation.objects.filter(
                donor=user
            ).select_related(
                'donor', 'request', 'request__requester'
            ).order_by('-donation_date')

            verified_donations = donations.filter(is_verified=True)

            dashboard['completed_donations'] = verified_donations.count()
            dashboard['last_donation_date'] = (
                verified_donations.first().donation_date if verified_donations.exists() else None
            )
            dashboard['donation_history'] = DonationSerializer(
                donations[:10], many=True
            ).data

            # Available blood requests for this donor’s blood type
            available_requests = BloodRequest.objects.filter(
                status='pending',
                blood_type=blood_type
            ).exclude(requester=user).select_related('requester').order_by('-created_at')[:10]

            dashboard['available_requests'] = BloodRequestSerializer(
                available_requests, many=True
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

                # Create the donation record
                Donation.objects.create(
                    donor=user,
                    recipient=blood_request.requester,
                    blood_type=blood_request.blood_type,
                    request=blood_request,
                    status='accepted'
                )

                # Update the request status
                blood_request.status = 'accepted'
                blood_request.save(update_fields=['status'])

                # Set donor availability to False
                if user.is_available:
                    user.is_available = False
                    user.save(update_fields=['is_available'])

            return Response({'message': 'Request accepted successfully'})

        except BloodRequest.DoesNotExist:
            return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)


# Public statistics endpoint (no authentication required)
class PublicStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_donors': User.objects.filter(donations__isnull=False).distinct().count(),
            'total_recipients': User.objects.filter(blood_requests__isnull=False).distinct().count(),
            'total_blood_requests': BloodRequest.objects.count(),
            'completed_donations': Donation.objects.filter(is_verified=True).count(),
            'pending_requests': BloodRequest.objects.filter(status='pending').count(),
            'upcoming_events': BloodEvent.objects.filter(
                required_date__gte=timezone.now().date(),
                status='pending'
            ).count()
        }
        return Response(stats)

# Authenticated user dashboard
class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dashboard = {
            'user_info': self._get_user_info(user),
            'recipient_data': self._get_recipient_data(user) if user.user_type in ['recipient', 'both'] else None,
            'donor_data': self._get_donor_data(user) if user.user_type in ['donor', 'both'] else None
        }
        return Response(dashboard)

    def _get_user_info(self, user):
        profile = getattr(user, 'profile', None)
        return {
            'name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'user_type': user.user_type,
            'blood_type': profile.blood_type if profile else None,
            'last_donation_date': user.last_donation_date,
            'is_available': user.is_available
        }

    def _get_recipient_data(self, user):
        requests = BloodRequest.objects.filter(
            requester=user
        ).select_related('requester').order_by('-created_at')
        
        return {
            'total_requests': requests.count(),
            'pending_requests': requests.filter(status='pending').count(),
            'recent_requests': BloodRequestSerializer(requests[:5], many=True).data
        }

    def _get_donor_data(self, user):
        profile = getattr(user, 'profile', None)
        if not profile or not profile.blood_type:
            return None
            
        donations = Donation.objects.filter(
            donor=user
        ).select_related('donor', 'request').order_by('-donation_date')

        verified_donations = donations.filter(is_verified=True)

        return {
            'total_donations': donations.count(),
            'verified_donations': verified_donations.count(),
            'last_donation': DonationSerializer(verified_donations.first()).data if verified_donations.exists() else None,
            'recent_donations': DonationSerializer(donations[:5], many=True).data,
            'available_requests': BloodRequestSerializer(
                BloodRequest.objects.filter(
                    status='pending',
                    blood_type=profile.blood_type
                ).exclude(requester=user).select_related('requester')[:5],
                many=True
            ).data
        }

    
    @transaction.atomic
    def post(self, request):
        user = request.user
        request_id = request.data.get('request_id')

        if not request_id:
            return Response({'error': 'Request ID required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            blood_request = BloodRequest.objects.select_for_update().get(
                id=request_id,
                status='pending'
            )

            if blood_request.requester == user:
                return Response(
                    {'error': 'You cannot accept your own request'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create donation record
            donation = Donation.objects.create(
                donor=user,
                request=blood_request,
                units_donated=1,
                is_verified=True
            )

            # Update request status
            blood_request.status = 'accepted'
            blood_request.save(update_fields=['status'])

            # Update donor availability
            if user.is_available:
                user.is_available = False
                user.save(update_fields=['is_available'])

            return Response(
                DonationSerializer(donation).data,
                status=status.HTTP_201_CREATED
            )

        except BloodRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid request ID'},
                status=status.HTTP_404_NOT_FOUND
            )



class ContactMessageCreateView(APIView):
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Message sent successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from sslcommerz_lib import SSLCOMMERZ 

@api_view(['POST'])
def initiate_payment(request):
    user=request.user
    print(user)
    amount=request.data.get("amount")
    print(request.data)
    settings = { 'store_id': 'phima68242c124ae93', 'store_pass': 'phima68242c124ae93@ssl', 'issandbox': True }
    sslcz = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = amount
    post_body['currency'] = "BDT"
    post_body['tran_id'] = str(uuid.uuid4())
    post_body['success_url'] = f"{main_settings.BACKEND_URL}/api/payment/success/"
    post_body['fail_url'] = f"{main_settings.BACKEND_URL}/api/payment/fail/"
    post_body['cancel_url'] = f"{main_settings.BACKEND_URL}/api/payment/cancel/"
    post_body['emi_option'] = 0
    post_body['cus_name'] = f"{user.first_name} {user.last_name}"
    post_body['cus_email'] = user.email
    post_body['cus_phone'] = user.phone
    post_body['cus_add1'] = user.address
    post_body['cus_city'] = "Dhaka"
    post_body['cus_country'] = "Bangladesh"
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Donation Service"
    post_body['product_category'] = "Service"
    post_body['product_profile'] = "general"


    response = sslcz.createSession(post_body) # API response
    # print(response)

    if response.get("status") == 'SUCCESS':
        return Response({"payment_url": response['GatewayPageURL']})
    return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)



# views.py
@api_view(['POST'])
def payment_success(request):
    # Get data from SSLCommerz response
    payment_data = request.data
    
    # Create payment history record
    PaymentHistory.objects.create(
        user=request.user,
        amount=payment_data.get('amount'),
        transaction_id=payment_data.get('tran_id'),
        status='success',
        first_name=payment_data.get('cus_name', '').split()[0] if payment_data.get('cus_name') else '',
        last_name=' '.join(payment_data.get('cus_name', '').split()[1:]) if payment_data.get('cus_name') else '',
        email=payment_data.get('cus_email'),
        phone=payment_data.get('cus_phone')
    )
    
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/success")

@api_view(['POST'])
def payment_fail(request):
    payment_data = request.data
    PaymentHistory.objects.create(
        user=request.user,
        amount=payment_data.get('amount'),
        transaction_id=payment_data.get('tran_id'),
        status='failed',
        first_name=payment_data.get('cus_name', '').split()[0] if payment_data.get('cus_name') else '',
        last_name=' '.join(payment_data.get('cus_name', '').split()[1:]) if payment_data.get('cus_name') else '',
        email=payment_data.get('cus_email'),
        phone=payment_data.get('cus_phone')
    )
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/fail/")

@api_view(['POST'])
def payment_cancel(request):
    payment_data = request.data
    PaymentHistory.objects.create(
        user=request.user,
        amount=payment_data.get('amount'),
        transaction_id=payment_data.get('tran_id'),
        status='canceled',
        first_name=payment_data.get('cus_name', '').split()[0] if payment_data.get('cus_name') else '',
        last_name=' '.join(payment_data.get('cus_name', '').split()[1:]) if payment_data.get('cus_name') else '',
        email=payment_data.get('cus_email'),
        phone=payment_data.get('cus_phone')
    )
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/cancel/")





class PaymentHistoryView(ListAPIView):
    serializer_class = PaymentHistorySerializer
    
    def get_queryset(self):
        return PaymentHistory.objects.filter(user=self.request.user).order_by('-timestamp')


