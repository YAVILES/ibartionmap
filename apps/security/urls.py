from rest_framework import routers

from .views import UserViewSet, RoleViewSet, ValidUser

router = routers.SimpleRouter()
router.register(r'user', UserViewSet)
router.register(r'valid', ValidUser, basename='valid')
router.register(r'role', RoleViewSet)

urlpatterns = [
]

urlpatterns += router.urls
