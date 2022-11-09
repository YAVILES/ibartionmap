from rest_framework import routers

from .views import SynchronizedTablesViewSet, DataGroupViewSet, RelationsTableViewSet, MarkerViewSet

router = routers.SimpleRouter()
router.register(r'synchronized_tables', SynchronizedTablesViewSet)
router.register(r'data_group', DataGroupViewSet)
router.register(r'relations_table', RelationsTableViewSet)
router.register(r'marker', MarkerViewSet)

urlpatterns = [
]

urlpatterns += router.urls
