from rest_framework import routers

from .views import ConnectionViewSet, IntervalScheduleViewSet

router = routers.SimpleRouter()
router.register(r'connection', ConnectionViewSet)
router.register(r'interval_schedule', IntervalScheduleViewSet)

urlpatterns = [
]

urlpatterns += router.urls
