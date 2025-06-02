from django.urls import path
from rest_framework.routers import DefaultRouter
from core.views import BloodRequestViewSet,ContactMessageCreateView,PublicStatsView,UserDashboardView,DonationViewSet,payment_success,PaymentHistoryView,payment_cancel,payment_fail, DashboardView,BloodEventViewSet,initiate_payment

router = DefaultRouter()
router.register("blood-requests", BloodRequestViewSet, basename="blood-requests")
router.register(r'blood-events', BloodEventViewSet, basename='bloodevent')
router.register(r'donations', DonationViewSet, basename='donations')

urlpatterns = router.urls + [
    path("payment/initiate/", initiate_payment, name="initiate-payment"),
    path("payment/success/", payment_success, name="payment-success"),
    path("payment/fail/", payment_fail, name="payment-fail"),
    path("payment/cancel/", payment_cancel, name="payment-cancel"),
    path('payment/history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('stats/public/', PublicStatsView.as_view(), name='public-stats'),
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
    path('contact/', ContactMessageCreateView.as_view(), name='contact-message'),
]


 
