from django.conf import settings

from .models import RolUsuario, Usuario


class SessionUser:
    def __init__(self, usuario):
        self._usuario = usuario

    @property
    def is_authenticated(self):
        return self._usuario is not None

    @property
    def id(self):
        return getattr(self._usuario, 'id', None)

    @property
    def pk(self):
        return self.id

    @property
    def email(self):
        return getattr(self._usuario, 'email', '')

    @property
    def rol(self):
        return getattr(self._usuario, 'rol', '')

    @property
    def is_staff(self):
        return self.rol in (RolUsuario.ADMIN, RolUsuario.SUPER_ADMIN)

    @property
    def is_superuser(self):
        return self.rol == RolUsuario.SUPER_ADMIN


def session_user(request):
    if (
        request.path.startswith('/admin/')
        or request.path.startswith('/django-admin/')
        or request.path.startswith('/dashboard/admin/')
    ):
        return {
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return {
            'user': SessionUser(None),
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }

    usuario = Usuario.objects.filter(id=usuario_id).only('id', 'email', 'rol').first()
    return {
        'user': SessionUser(usuario),
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
    }
