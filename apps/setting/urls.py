from rest_framework import routers

from .views import ConnectionViewSet

router = routers.SimpleRouter()
router.register(r'connection', ConnectionViewSet)

urlpatterns = [
]

urlpatterns += router.urls
