from django.urls import path
from rest_framework.routers import DefaultRouter
from core.views import BloodRequestViewSet ,DonationViewSet,payment_success,payment_cancel,payment_fail, DashboardView,BloodEventViewSet,initiate_payment

router = DefaultRouter()
router.register(r'blood-requests', BloodRequestViewSet, basename='blood-request')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'blood-events', BloodEventViewSet, basename='blood-event')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path("initiate/payment/", initiate_payment, name="initiate/payment"),
    path("api/payment/initiate/", initiate_payment, name="initiate-payment"),
    path("api/payment/success/", payment_success, name="payment-success"),
    path("api/payment/fail/", payment_fail, name="payment-fail"),
    path("api/payment/cancel/", payment_cancel, name="payment-cancel"),
]

