from rest_framework import routers

from .views import SynchronizedTablesViewSet, DataGroupViewSet, RelationsTableViewSet

router = routers.SimpleRouter()
router.register(r'synchronized_tables', SynchronizedTablesViewSet)
router.register(r'data_group', DataGroupViewSet)
router.register(r'relations_table', RelationsTableViewSet)

urlpatterns = [
]

urlpatterns += router.urls
