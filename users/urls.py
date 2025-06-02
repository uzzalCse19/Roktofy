from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import (
    UserProfileViewSet, 
    UserViewSet, PublicDonorListView, RequestBloodView,check_profile_complete,DonorListView,UserProfileUpdateView,UserUpdateView_two
)
from .views import (
    AdminDashboardView,
    AdminUserManagementView,
    AdminBloodRequestView,
    AdminDonationView,
    AdminAuditLogView,
    # AdminSystemSettingsView
)

router = DefaultRouter()
router.register('user-list', UserViewSet, basename='user')
router.register('profile', UserProfileViewSet, basename='profile')


urlpatterns = [
    path('', include(router.urls)),
    path('public-donors/', PublicDonorListView.as_view(), name='public-donors'),
    path('request-blood/', RequestBloodView.as_view(), name='request-blood'),
    path('donor-list/', DonorListView.as_view(), name='donor-list'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('me/update/', UserUpdateView_two.as_view(), name='user-update'), 
    path('api/check-profile/', check_profile_complete, name='check-profile'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserManagementView.as_view(), name='admin-users-list'),
    path('admin/users/<int:user_id>/', AdminUserManagementView.as_view(), name='admin-user-detail'),
    
  
    path('admin/blood-requests/', AdminBloodRequestView.as_view(), name='admin-requests-list'),
    path('admin/blood-requests/<int:req_id>/', AdminBloodRequestView.as_view(), name='admin-request-detail'),
    
 
    path('admin/donations/', AdminDonationView.as_view(), name='admin-donations-list'),
    path('admin/donations/<int:donation_id>/', AdminDonationView.as_view(), name='admin-donation-detail'),

    path('admin/audit-logs/', AdminAuditLogView.as_view(), name='admin-audit-logs'),
]


 
