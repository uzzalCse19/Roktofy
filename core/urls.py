from django.urls import path
from rest_framework.routers import DefaultRouter
from core.views import BloodRequestViewSet ,DonationViewSet, DashboardView,BloodEventViewSet,initiate_payment

router = DefaultRouter()
router.register(r'blood-requests', BloodRequestViewSet, basename='blood-request')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'blood-events', BloodEventViewSet, basename='blood-event')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
     path("initiate-payment/", initiate_payment, name="initiate-payment"),
    # path("donation/initiate/", initiate_donation, name="initiate-donation"),
    # path("donation/success/", donation_success, name="donation-success"),
    # path("donation/fail/", donation_fail, name="donation-fail"),
    # path("donation/cancel/", donation_cancel, name="donation-cancel"),
    # path('blood-requests/check-eligibility/<int:donor_id>/', check_donor_eligibility),
]
