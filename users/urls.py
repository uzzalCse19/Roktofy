from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import (
    UserProfileViewSet, 
    UserViewSet, PublicDonorListView, RequestBloodView,check_profile_complete,DonorListView,UserProfileUpdateView,UserUpdateView_two
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
]
 
