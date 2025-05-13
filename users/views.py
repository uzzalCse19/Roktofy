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
from core.models import BloodRequest  # adjust path as needed
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.filters import DonorFilter
from users.serializers import DonorListSerializer
from django.db.models import Q

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    permission_classes = [IsAuthenticated]


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
            profile__blood_type__isnull=False
        ).filter(
            Q(user_type='donor') | Q(user_type='both')
        ).select_related('profile').only(
            'id', 'first_name', 'last_name', 'email', 'address', 
            'last_donation_date', 'is_available',
            'profile__blood_type'
        )


# new added 

# users/views.py
from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


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
    

