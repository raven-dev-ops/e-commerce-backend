from rest_framework.routers import DefaultRouter
from .views import ReferralCodeViewSet

router = DefaultRouter()
router.register(r"referral-codes", ReferralCodeViewSet, basename="referralcode")

urlpatterns = router.urls
