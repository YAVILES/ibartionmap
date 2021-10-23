from django.contrib.auth.backends import ModelBackend
from rest_framework import exceptions
from django.contrib.auth import get_user_model

from apps.security.models import User

UserModel = get_user_model()


class CustomAuthenticationBackend(ModelBackend):

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        status = getattr(user, 'status', None)
        return status == User.ACTIVE

    def authenticate(self, request, password=None, **kwargs):
        username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None:
            username = kwargs.get('username')
        if username is None or password is None:
            return
        else:
            try:
                user = UserModel._default_manager.get_by_natural_key(str(username).lower())
            except UserModel.DoesNotExist:
                raise exceptions.AuthenticationFailed(
                    'El correo suministrado, no se encuentra registrado. Intente con uno diferente'
                )
            if not user.check_password(password):
                raise exceptions.AuthenticationFailed(
                    'La contraseña ingresada no es correcta. Por favor, inténtelo nuevamente'
                )
            if not self.user_can_authenticate(user):
                raise exceptions.AuthenticationFailed('Usuario inactivo')
            return user
