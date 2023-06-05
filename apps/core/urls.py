from rest_framework import routers

from .views import SynchronizedTablesViewSet, RelationsTableViewSet, MarkerViewSet, LineViewSet

router = routers.SimpleRouter()
router.register(r'synchronized_tables', SynchronizedTablesViewSet)
router.register(r'relations_table', RelationsTableViewSet)
router.register(r'marker', MarkerViewSet)
router.register(r'line', LineViewSet)

urlpatterns = [
]

urlpatterns += router.urls
