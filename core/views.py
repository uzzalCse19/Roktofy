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
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework import permissions
from rest_framework.decorators import api_view
from django.conf import settings as main_settings
from django.http import HttpResponseRedirect
from core.models import PaymentHistory
User = get_user_model()
import uuid



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
    filterset_fields = ['request__status']
    search_fields = ['donor__email', 'request__blood_type']
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

from django.db import transaction
# class DashboardView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         dashboard = {}

#         # Get user profile and blood type if available
#         profile = getattr(user, 'profile', None)
#         blood_type = profile.blood_type if profile else None
#         dashboard['blood_type'] = blood_type

#         # Recipient Dashboard Info
#         if user.user_type in ['recipient', 'both']:
#             recipient_requests = BloodRequest.objects.filter(
#                 requester=user
#             ).select_related('requester').order_by('-created_at')

#             dashboard['total_requests'] = recipient_requests.count()
#             dashboard['pending_requests'] = recipient_requests.filter(status='pending').count()
#             dashboard['my_requests'] = BloodRequestSerializer(
#                 recipient_requests[:10], many=True
#             ).data

#         # Donor Dashboard Info
#         if user.user_type in ['donor', 'both'] and blood_type:
#             donations = Donation.objects.filter(
#                 donor=user
#             ).select_related(
#                 'donor', 'request', 'request__requester'
#             ).order_by('-donation_date')

#             verified_donations = donations.filter(is_verified=True)

#             dashboard['completed_donations'] = verified_donations.count()
#             dashboard['last_donation_date'] = (
#                 verified_donations.first().donation_date if verified_donations.exists() else None
#             )
#             dashboard['donation_history'] = DonationSerializer(
#                 donations[:10], many=True
#             ).data

#             # Available blood requests for this donor’s blood type
#             available_requests = BloodRequest.objects.filter(
#                 status='pending',
#                 blood_type=blood_type
#             ).exclude(requester=user).select_related('requester').order_by('-created_at')[:10]

#             dashboard['available_requests'] = BloodRequestSerializer(
#                 available_requests, many=True
#             ).data

#         return Response(dashboard)

#     def post(self, request):
#         user = request.user
#         request_id = request.data.get('request_id')

#         if not request_id:
#             return Response({'error': 'Request ID required'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             with transaction.atomic():
#                 blood_request = BloodRequest.objects.select_for_update().get(
#                     id=request_id,
#                     status='pending'
#                 )

#                 # Create the donation record
#                 Donation.objects.create(
#                     donor=user,
#                     recipient=blood_request.requester,
#                     blood_type=blood_request.blood_type,
#                     request=blood_request,
#                     status='accepted'
#                 )

#                 # Update the request status
#                 blood_request.status = 'accepted'
#                 blood_request.save(update_fields=['status'])

#                 # Set donor availability to False
#                 if user.is_available:
#                     user.is_available = False
#                     user.save(update_fields=['is_available'])

#             return Response({'message': 'Request accepted successfully'})

#         except BloodRequest.DoesNotExist:
#             return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from users.models import User
from core.models import BloodRequest, Donation, BloodEvent
from core.serializers import BloodRequestSerializer, DonationSerializer


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

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.models import User
from core.models import BloodRequest, Donation, BloodEvent
from .serializers import BloodRequestSerializer, DonationSerializer

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


# @api_view(['POST'])
# def payment_success(request):
#     print("Inside success")
#     return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/success")


# @api_view(['POST'])
# def payment_cancel(request):
#     return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/cancel/")

# @api_view(['POST'])
# def payment_fail(request):
#     print("Inside fail")
#     return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/payment/fail/")

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



from rest_framework.generics import ListAPIView
from .serializers import PaymentHistorySerializer

class PaymentHistoryView(ListAPIView):
    serializer_class = PaymentHistorySerializer
    
    def get_queryset(self):
        return PaymentHistory.objects.filter(user=self.request.user).order_by('-timestamp')

# new added

# from django.db.models import Count
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from users.models import User
# from core.models import BloodRequest, Donation, BloodEvent
# from django.utils import timezone

# @api_view(['GET'])
# def dashboard_stats(request):
#     # Total donors (users who have donated at least once)
#     total_donors = User.objects.filter(donations__isnull=False).distinct().count()
    
#     # Total recipients (users who have made at least one request)
#     total_recipients = User.objects.filter(blood_requests__isnull=False).distinct().count()
    
#     # Total users
#     total_users = User.objects.count()
    
#     # Total blood requests
#     total_requests = BloodRequest.objects.count()
    
#     # Completed donations (verified donations)
#     completed_donations = Donation.objects.filter(is_verified=True).count()
    
#     # Pending requests
#     pending_requests = BloodRequest.objects.filter(status='pending').count()
    
#     # Upcoming blood events
#     upcoming_events = BloodEvent.objects.filter(
#         required_date__gte=timezone.now().date(),
#         status='pending'
#     ).count()
    
#     return Response({
#         'totalDonors': total_donors,
#         'totalRecipients': total_recipients,
#         'totalUsers': total_users,
#         'totalRequests': total_requests,
#         'completedDonations': completed_donations,
#         'pendingRequests': pending_requests,
#         'upcomingEvents': upcoming_events,
#     })



# # new added-10-05

# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import BloodEvent, Donation
# from .serializers import BloodEventSerializer2, DonationSerializer2
# from users.models import User

# class BloodEventListCreateView(generics.ListCreateAPIView):
#     serializer_class = BloodEventSerializer2
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         return BloodEvent.objects.all().order_by('-created_at')
    
#     def perform_create(self, serializer):
#         serializer.save(creator=self.request.user)
    
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['request'] = self.request
#         return context

# class AcceptBloodEventView(generics.CreateAPIView):
#     serializer_class = DonationSerializer2
#     permission_classes = [IsAuthenticated]
    
#     def create(self, request, *args, **kwargs):
#         event_id = request.data.get('event')
#         try:
#             event = BloodEvent.objects.get(id=event_id)
#         except BloodEvent.DoesNotExist:
#             return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
#         if event.creator == request.user:
#             return Response({'error': 'You cannot accept your own event'}, 
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         if event.accepted_by.filter(id=request.user.id).exists():
#             return Response({'error': 'You have already accepted this event'}, 
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         # Create donation record
#         donation = Donation.objects.create(
#             donor=request.user,
#             event=event,
#             units_donated=1,
#             is_verified=True
#         )
        
#         # Add donor to accepted_by
#         event.accepted_by.add(request.user)
        
#         # Send email to event creator
#         self.send_acceptance_email(event, request.user)
        
#         serializer = self.get_serializer(donation)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#     def send_acceptance_email(self, event, donor):
#         subject = f"Your blood donation request has been accepted"
#         message = f"""
#         Hello {event.creator.first_name},
        
#         {donor.first_name} {donor.last_name} has accepted your blood donation request for {event.blood_type}.
        
#         Donor Details:
#         Name: {donor.first_name} {donor.last_name}
#         Email: {donor.email}
#         Phone: {donor.phone}
        
#         Please contact the donor to arrange the donation.
        
#         Thank you,
#         Blood Donation Team
#         """
#         send_mail(
#             subject,
#             message,
#             settings.DEFAULT_FROM_EMAIL,
#             [event.creator.email],
#             fail_silently=False,
#         )

# class DonationHistoryView(generics.ListAPIView):
#     serializer_class = DonationSerializer2
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         return Donation.objects.filter(donor=self.request.user).order_by('-donation_date')


# class DashboardView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         user = request.user
#         dashboard = {}
#         profile = getattr(user, 'profile', None)
#         blood_type = profile.blood_type if profile else None
#         dashboard['blood_type'] = blood_type
#         if user.user_type in ['recipient', 'both']:
#             recipient_data = BloodRequest.objects.filter(
#                 requester=user
#             ).select_related('requester').order_by('-created_at') 
#             dashboard['total_requests'] = recipient_data.count()
#             dashboard['pending_requests'] = recipient_data.filter(status='pending').count()
#             dashboard['my_requests'] = BloodRequestSerializer(
#                 recipient_data[:10],  
#                 many=True
#             ).data

#         if user.user_type in ['donor', 'both'] and blood_type:
#             donations = Donation.objects.filter(
#                 donor=user
#             ).select_related(
#                 'donor', 
#                 'request',
#                 'request__requester'
#             ).order_by('-donation_date')
            
#             verified_donations = donations.filter(is_verified=True)
#             dashboard['completed_donations'] = verified_donations.count()
#             dashboard['last_donation_date'] = verified_donations.first().donation_date if verified_donations.exists() else None
#             dashboard['donation_history'] = DonationSerializer(
#                 donations[:10],  
#                 many=True
#             ).data

#             dashboard['available_requests'] = BloodRequestSerializer(
#                 BloodRequest.objects.filter(
#                     status='pending',
#                     blood_type=blood_type
#                 ).exclude(requester=user).select_related('requester')[:10], 
#                 many=True
#             ).data

#         return Response(dashboard)

#     def post(self, request):
#         user = request.user
#         request_id = request.data.get('request_id')
#         if not request_id:
#             return Response({'error': 'Request ID required'}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             with transaction.atomic():
#                 blood_request = BloodRequest.objects.select_for_update().get(
#                     id=request_id, 
#                     status='pending'
#                 )
#                 Donation.objects.create(
#                     donor=user,
#                     recipient=blood_request.requester,
#                     blood_type=blood_request.blood_type,
#                     request=blood_request,
#                     status='accepted'
#                 )
#                 blood_request.status = 'accepted'
#                 blood_request.save(update_fields=['status'])
#                 if user.is_available:
#                     user.is_available = False
#                     user.save(update_fields=['is_available'])
#             return Response({'message': 'Request accepted successfully'})
#         except BloodRequest.DoesNotExist:
#             return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)




from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import transaction
from django.utils import timezone
from users.models import User
from core.models import BloodRequest, Donation, BloodEvent

# Global statistics endpoint (unauthenticated)
# @api_view(['GET'])
# def system_stats(request):
#     stats = {
#         'totalDonors': User.objects.filter(donations__isnull=False).distinct().count(),
#         'totalRecipients': User.objects.filter(blood_requests__isnull=False).distinct().count(),
#         'totalUsers': User.objects.count(),
#         'totalRequests': BloodRequest.objects.count(),
#         'completedDonations': Donation.objects.filter(is_verified=True).count(),
#         'pendingRequests': BloodRequest.objects.filter(status='pending').count(),
#         'upcomingEvents': BloodEvent.objects.filter(
#             required_date__gte=timezone.now().date(),
#             status='pending'
#         ).count()
#     }
#     return Response(stats)

# # Personalized dashboard (authenticated)
# class UserDashboardView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         dashboard = {
#             'system_stats': system_stats(request._request).data,
#             'personal_stats': self._get_personal_stats(user)
#         }
#         return Response(dashboard)

#     def _get_personal_stats(self, user):
#         stats = {}
#         profile = getattr(user, 'profile', None)
#         blood_type = profile.blood_type if profile else None
        
#         # Recipient stats
#         if user.user_type in ['recipient', 'both']:
#             stats.update(self._get_recipient_stats(user))
        
#         # Donor stats
#         if user.user_type in ['donor', 'both'] and blood_type:
#             stats.update(self._get_donor_stats(user, blood_type))
        
#         return stats

#     def _get_recipient_stats(self, user):
#         requests = BloodRequest.objects.filter(requester=user)
#         return {
#             'my_requests': {
#                 'total': requests.count(),
#                 'pending': requests.filter(status='pending').count(),
#                 'recent': BloodRequestSerializer(requests[:5], many=True).data
#             }
#         }

#     def _get_donor_stats(self, user, blood_type):
#         donations = Donation.objects.filter(donor=user)
#         verified = donations.filter(is_verified=True)
        
#         return {
#             'my_donations': {
#                 'total': donations.count(),
#                 'verified': verified.count(),
#                 'last_date': verified.first().donation_date if verified.exists() else None,
#                 'recent': DonationSerializer(donations[:5], many=True).data
#             },
#             'available_requests': BloodRequestSerializer(
#                 BloodRequest.objects.filter(
#                     status='pending',
#                     blood_type=blood_type
#                 ).exclude(requester=user)[:5],
#                 many=True
#             ).data
#         }

#     @transaction.atomic
#     def post(self, request):
#         # ... keep your existing post logic for accepting requests ...




 

