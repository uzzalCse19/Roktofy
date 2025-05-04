from django.urls import path
from rest_framework.routers import DefaultRouter
from core.views import BloodRequestViewSet, DonationViewSet, DashboardView,PaymentPlaceholderView,BloodEventViewSet

router = DefaultRouter()
router.register(r'blood-requests', BloodRequestViewSet, basename='blood-request')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'blood-events', BloodEventViewSet, basename='blood-event')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('payment/', PaymentPlaceholderView.as_view(), name='payment'),
]
