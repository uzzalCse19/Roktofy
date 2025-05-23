from rest_framework import viewsets, status,generics,permissions,filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from users.models import User, UserProfile
from users.serializers import UserSerializer, UserProfileSerializer
from users.permissions import IsVerifiedUser
from users.filters import UserFilter
from users.paginations import UserPagination
from django.contrib.auth import get_user_model
from users.serializers import PublicDonorSerializer, BloodRequestSerializer
from core.models import BloodRequest ,Donation,PaymentHistory # adjust path as needed
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.filters import DonorFilter
from users.serializers import DonorListSerializer
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes


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

    # def get_queryset(self):
    #     return UserProfile.objects.filter(user=self.request.user)

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
            profile__blood_type__isnull=False
        ).filter(
            Q(user_type='donor') | Q(user_type='both')
        ).select_related('profile').only(
            'id', 'first_name', 'last_name', 'email', 'phone', 'address', 
            'last_donation_date', 'is_available',
            'profile__blood_type'
        )


# new added 

from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

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


# admin_dashboard/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
# from django.db.models import Count, Sum, Q, F
# from django.utils import timezone
# from datetime import timedelta
from django.db.models.functions import Coalesce
# from users.models import User, UserProfile
# from core.models import (BloodRequest, Donation, 
#                         BloodEvent, PaymentHistory, ContactMessage)

# class AdminDashboardView(APIView):
#     permission_classes = [IsAdminUser]
    
#     def get(self, request):
#         # System Stats
#         stats = {
#             'users': {
#                 'total': User.objects.count(),
#                 'new_today': User.objects.filter(date_joined__date=timezone.now()).count(),
#                 'donors': User.objects.filter(Q(user_type='donor') | Q(user_type='both')).count(),
#             },
#             'requests': {
#                 'total': BloodRequest.objects.count(),
#                 'pending': BloodRequest.objects.filter(status='pending').count(),
#                 'urgent': BloodRequest.objects.filter(urgency='high').count(),
#             },
#             'donations': {
#                 'total': Donation.objects.count(),
#                 'verified': Donation.objects.filter(is_verified=True).count(),
#             },
#             'payments': PaymentHistory.objects.aggregate(
#                 total=Sum('amount', filter=Q(status='success'))
#             )['total'] or 0
#         }
#         return Response(stats)

# class AdminUserManagementView(APIView):
#     permission_classes = [IsAdminUser]
    
#     def get(self, request):
#         users = User.objects.annotate(
#             blood_type=F('profile__blood_type')
#         ).values('id', 'email', 'first_name', 'last_name', 
#                 'is_active', 'user_type', 'blood_type')
#         return Response(users)
    
#     def patch(self, request, user_id):
#         user = User.objects.get(id=user_id)
#         user.is_active = not user.is_active  # Toggle active status
#         user.save()
#         return Response({'status': 'success'})

# class AdminBloodRequestView(APIView):
#     permission_classes = [IsAdminUser]
    
#     def get(self, request):
#         requests = BloodRequest.objects.select_related('requester').annotate(
#             requester_email=F('requester__email')
#         ).values('id', 'blood_type', 'status', 'units_needed', 
#                 'hospital', 'created_at', 'requester_email')
#         return Response(requests)
    
#     def patch(self, request, req_id):
#         blood_request = BloodRequest.objects.get(id=req_id)
#         blood_request.status = request.data.get('status', blood_request.status)
#         blood_request.save()
#         return Response({'status': 'updated'})

# class AdminDonationView(APIView):
#     permission_classes = [IsAdminUser]
    
#     def get(self, request):
#         donations = Donation.objects.select_related(
#             'donor', 'request', 'event'
#         ).annotate(
#             donor_email=F('donor__email'),
#             blood_type=Coalesce(
#                 F('request__blood_type'), 
#                 F('event__blood_type')
#             )
#         ).values('id', 'donor_email', 'blood_type', 
#                 'units_donated', 'donation_date', 'is_verified')
#         return Response(donations)
    
#     def patch(self, request, donation_id):
#         donation = Donation.objects.get(id=donation_id)
#         donation.is_verified = not donation.is_verified  # Toggle verification
#         donation.save()
#         return Response({'status': 'verified' if donation.is_verified else 'unverified'})



# new added 

from django.db.models import Count, Sum, Q, F, Case, When, Value, CharField
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import AdminBloodRequestSerializer,AdminDonationSerializer,AdminUserSerializer

from django.utils import timezone
from django.db.models import Q, Count, Sum, Case, When, Value, CharField
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from datetime import datetime


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


from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import AdminUserSerializer

from django.db.models import F, Value
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import AdminUserSerializer  # Make sure this is correctly imported

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import AdminUserSerializer, AdminUserListSerializer  # নিচে তৈরি করতে হবে

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

# Serializers (add to serializers.py)



# class UserRegistrationView(generics.CreateAPIView):
#     serializer_class = UserRegistrationSerializer
#     permission_classes = [permissions.AllowAny]

#     def perform_create(self, serializer):
#         user = serializer.save()
#         user.is_active = False  # Prevent login before activation
#         user.save()

#         # Generate token and uid
#         token = default_token_generator.make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))

#         # Build activation URL
#         activation_url = self.request.build_absolute_uri(
#             reverse('activate-account', kwargs={'uidb64': uid, 'token': token})
#         )

#         # Send activation email
#         send_mail(
#             subject='Activate your Blood Bank account',
#             message=f'Hi {user.email}, please activate your account using the link: {activation_url}',
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[user.email],
#             fail_silently=False,
#         )

#         return user

# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer

# @require_GET  # Restrict to GET requests only
# def activate_account(request, uidb64, token):
#     """
#     Activates a user account using a token-based verification system.
    
#     Args:
#         uidb64 (str): Base64-encoded user ID.
#         token (str): Account activation token.
    
#     Returns:
#         JsonResponse: Success or error message.
#     """
#     try:
#         # Decode user ID
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = User.objects.get(pk=uid)

#         # Validate token
#         if not default_token_generator.check_token(user, token):
#             raise ValidationError("Invalid activation link.")

#         # Activate user
#         if not user.is_active:
#             user.is_active = True
#             user.is_verified = True  # Optional: Track verification separately
#             user.save()
#             return JsonResponse(
#                 {'success': 'Account activated successfully.'},
#                 status=200
#             )
#         else:
#             return JsonResponse(
#                 {'info': 'Account is already active.'},
#                 status=200
#             )

#     except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
#         return JsonResponse(
#             {'error': 'Activation failed. Invalid or expired link.'},
#             status=400
#         )
#     except ValidationError as e:
#         return JsonResponse(
#             {'error': str(e)},
#             status=400
#         )
    

# class UserProfileViewSet(viewsets.ModelViewSet):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]
#     lookup_field = 'pk'
#     def get_queryset(self):
#         return UserProfile.objects.filter(user=self.request.user)
    
#     def create(self, request, *args, **kwargs):
#         if hasattr(request.user, 'profile'):
#             return Response(
#                 {"detail": "Profile already exists. Use update instead."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return super().create(request, *args, **kwargs)
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
