from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password

from core.models import Usuario


class CoreUsuarioBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (username or kwargs.get('email') or '').strip()
        if not email or password is None:
            return None

        usuario = Usuario.objects_all.filter(email__iexact=email).first()
        if usuario is None:
            return None

        if not check_password(password, usuario.password_hash):
            return None

        UserModel = get_user_model()
        django_user = UserModel.objects.filter(username__iexact=email).first()
        if django_user is None:
            django_user = UserModel.objects.create_user(username=email, email=email, password=password)
        else:
            django_user.email = email
            django_user.set_password(password)
            django_user.save(update_fields=['email', 'password'])

        return django_user

