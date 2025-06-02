from rest_framework import viewsets, status,generics,permissions,filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode

from users.serializers import UserProfileSerializer,DonorListSerializer,UserSerializer,PublicDonorSerializer, BloodRequestSerializer
from users.models import User, UserProfile
from users.permissions import IsVerifiedUser
from users.filters import UserFilter,DonorFilter
from users.paginations import UserPagination
from django.contrib.auth import get_user_model
from core.models import BloodRequest ,Donation,PaymentHistory 
from django.shortcuts import render,get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from django.db.models.functions import Coalesce
from django.db.models import Count, Sum, Q, F, Case, When, Value, CharField
from django.utils import timezone
from datetime import timedelta,datetime
from rest_framework.views import APIView
from users.serializers import AdminBloodRequestSerializer,AdminDonationSerializer,AdminUserSerializer


User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    permission_classes = [IsAuthenticated]



class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']  
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        return self.request.user.profile

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'profile'):
            return Response(
                {"detail": "Profile already exists. Use update instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PublicDonorListView(generics.ListAPIView):
    """
    Public homepage view 
    """
    queryset = User.objects.filter(
        user_type__in=['donor', 'both'],
        is_verified=True,
        is_available=True,
        profile__blood_type__isnull=False
        ).select_related('profile')
    serializer_class = PublicDonorSerializer
    permission_classes = [permissions.AllowAny]  


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']  
    def get_queryset(self):
       if getattr(self, 'swagger_fake_view', False):  
           return UserProfile.objects.none()  

       return UserProfile.objects.filter(user=self.request.user)


    def get_object(self):
        return self.request.user.profile

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Profile already exists. Use update instead."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class RequestBloodView(generics.CreateAPIView):
    """
    Authenticated users can request blood from the donor list
    """
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)


class DonorListView(generics.ListAPIView):
    serializer_class = DonorListSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = DonorFilter
    ordering_fields = ['last_donation_date', 'profile__blood_type', 'first_name']
    ordering = ['-last_donation_date']
    search_fields = ['first_name', 'last_name', 'email', 'address']

    def get_queryset(self):
        return User.objects.filter(
           is_available=True,
           profile__blood_type__isnull=False,
        #    last_donation_date__isnull=False
        ).filter(
           Q(user_type='donor') | Q(user_type='both')
        ).select_related('profile')

# new added 


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

# new added 2

from .serializers import UserUpdateSerializer_two

class UserUpdateView_two(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer_two
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user  


# new Added

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_profile_complete(request):
    user = request.user
    is_complete = all([
        user.age is not None,
        bool(user.address),
        bool(user.phone),
        user.is_available is not None,
        hasattr(user, 'profile') and bool(user.profile.blood_type)
    ])
    return Response({'is_profile_complete': is_complete})


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        stats = {
            'users': {
                'total': User.objects.count(),
                'new_today': User.objects.filter(date_joined__date=timezone.now().date()).count(),
                'donors': User.objects.filter(Q(user_type='donor') | Q(user_type='both')).count(),
                'recipients': User.objects.filter(Q(user_type='recipient') | Q(user_type='both')).count(),
                'inactive': User.objects.filter(is_active=False).count(),
            },
            'requests': {
                'total': BloodRequest.objects.count(),
                'status_distribution': BloodRequest.objects.aggregate(
                    pending=Count('id', filter=Q(status='pending')),
                    accepted=Count('id', filter=Q(status='accepted')),
                    completed=Count('id', filter=Q(status='completed')),
                    cancelled=Count('id', filter=Q(status='cancelled'))
                ),
                'urgency_distribution': BloodRequest.objects.aggregate(
                    low=Count('id', filter=Q(urgency='low')),
                    normal=Count('id', filter=Q(urgency='normal')),
                    high=Count('id', filter=Q(urgency='high'))
                ),
                'blood_type_distribution': BloodRequest.objects.values('blood_type').annotate(
                    count=Count('id')
                ).order_by('-count')
            },
            'donations': {
                'total': Donation.objects.count(),
                'verified': Donation.objects.filter(is_verified=True).count(),
                'unverified': Donation.objects.filter(is_verified=False).count(),
                'by_type': Donation.objects.annotate(
                    type=Case(
                        When(request__isnull=False, then=Value('request')),
                        When(event__isnull=False, then=Value('event')),
                        default=Value('unknown'),  # ✅ Added to prevent 500 error
                        output_field=CharField()
                    )
                ).values('type').annotate(count=Count('id'))
            },
            'payments': {
                'total_amount': PaymentHistory.objects.aggregate(
                    total=Sum('amount', filter=Q(status='success'))
                )['total'] or 0,
                'status_counts': PaymentHistory.objects.values('status').annotate(
                    count=Count('id')
                )
            },
            'system': {
                'uptime_days': (timezone.now() - timezone.make_aware(datetime(2023, 1, 1))).days,
                'avg_response_time': 42.5  # Just a placeholder, replace with real metric if available
            }
        }
        return Response(stats)



class AdminUserManagementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_type = request.query_params.get('type')
        is_active = request.query_params.get('active')

        queryset = User.objects.select_related('profile').annotate(
            blood_type=Coalesce(F('profile__blood_type'), Value('')),
            last_donation=Coalesce(F('last_donation_date'), Value(None)),
        )

        if user_type:
            queryset = queryset.filter(user_type=user_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        serializer = AdminUserListSerializer(queryset, many=True)
        return Response(serializer.data)

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response({'status': 'deleted'})




class AdminBloodRequestView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Enhanced filtering
        status = request.query_params.get('status')
        blood_type = request.query_params.get('blood_type')
        urgency = request.query_params.get('urgency')
        
        queryset = BloodRequest.objects.select_related('requester')
        
        if status:
            queryset = queryset.filter(status=status)
        if blood_type:
            queryset = queryset.filter(blood_type=blood_type)
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        requests = queryset.annotate(
            requester_email=F('requester__email'),
            requester_phone=F('requester__phone')
        ).values(
            'id', 'blood_type', 'status', 'units_needed', 
            'hospital', 'location', 'created_at', 'needed_by',
            'requester_email', 'requester_phone', 'urgency',
            'additional_info'
        ).order_by('-created_at')
        
        return Response(requests)
    
    def patch(self, request, req_id):
        blood_request = BloodRequest.objects.get(id=req_id)
        
        # Enhanced request management
        serializer = AdminBloodRequestSerializer(blood_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    def delete(self, request, req_id):
        blood_request = BloodRequest.objects.get(id=req_id)
        blood_request.delete()
        return Response({'status': 'deleted'})

class AdminDonationView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Enhanced donation tracking
        is_verified = request.query_params.get('verified')
        blood_type = request.query_params.get('blood_type')
        
        queryset = Donation.objects.select_related(
            'donor', 'request', 'event'
        )
        
        if is_verified:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        if blood_type:
            queryset = queryset.filter(
                Q(request__blood_type=blood_type) | 
                Q(event__blood_type=blood_type)
            )
        
        donations = queryset.annotate(
            donor_email=F('donor__email'),
            donor_phone=F('donor__phone'),
            blood_type=Case(
                When(request__isnull=False, then=F('request__blood_type')),
                When(event__isnull=False, then=F('event__blood_type')),
                output_field=CharField()
            ),
            donation_type=Case(
                When(request__isnull=False, then=Value('request')),
                When(event__isnull=False, then=Value('event')),
                output_field=CharField()
            )
        ).values(
            'id', 'donor_email', 'donor_phone', 'blood_type',
            'units_donated', 'donation_date', 'is_verified',
            'donation_type'
        ).order_by('-donation_date')
        
        return Response(donations)
    
    def patch(self, request, donation_id):
        donation = Donation.objects.get(id=donation_id)
        
        # Enhanced verification with notes
        serializer = AdminDonationSerializer(donation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

# Additional Admin Functionalities

    
    def post(self, request):
        # Update system settings
        # Implement your settings update logic here
        return Response({'status': 'settings_updated'})

class AdminAuditLogView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get recent admin actions
        logs = [
            {'action': 'user_deactivated', 'admin': 'superuser', 'timestamp': '2023-05-20T10:30:00Z'},
            {'action': 'request_approved', 'admin': 'admin1', 'timestamp': '2023-05-20T09:15:00Z'}
        ]
        return Response(logs)

