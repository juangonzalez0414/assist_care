from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from functools import wraps
from .models import EstadoVerificacion, RolUsuario, Usuario


def usuario_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        wants_json = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in (request.headers.get('accept') or '')
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            django_user = getattr(request, 'user', None)
            if django_user is not None and getattr(django_user, 'is_authenticated', False):
                correo = (getattr(django_user, 'email', None) or '').strip().lower()
                if not correo:
                    messages.error(request, "No pudimos identificar tu correo de Google.")
                    if wants_json:
                        return JsonResponse({'status': 'error', 'message': 'No pudimos identificar tu correo de Google.'}, status=401)
                    return redirect('login')

                usuario = Usuario.objects.filter(email__iexact=correo).first()
                if not usuario:
                    try:
                        with transaction.atomic():
                            usuario, _created = Usuario.objects.get_or_create(
                                email=correo,
                                defaults={
                                    'password_hash': make_password(None),
                                    'rol': RolUsuario.DISCAPACITADO,
                                    'estado': EstadoVerificacion.PREREGISTRO,
                                },
                            )
                    except IntegrityError:
                        # Si otra petición creó el usuario en paralelo, lo recuperamos.
                        usuario = Usuario.objects.filter(email__iexact=correo).first()
                if not usuario:
                    messages.error(request, "No pudimos cargar tu usuario en este momento.")
                    if wants_json:
                        return JsonResponse({'status': 'error', 'message': 'No pudimos cargar tu usuario en este momento.'}, status=500)
                    return redirect('login')
                request.session['usuario_id'] = str(usuario.id)
                request.usuario = usuario
                return view_func(request, *args, **kwargs)

            if wants_json:
                return JsonResponse({'status': 'error', 'message': 'Autenticación requerida.'}, status=401)
            return redirect('login')

        usuario = Usuario.objects.filter(id=usuario_id).first()
        if not usuario:
            request.session.flush()
            if wants_json:
                return JsonResponse({'status': 'error', 'message': 'Autenticación requerida.'}, status=401)
            return redirect('login')

        request.usuario = usuario
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def role_required(role_value):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            wants_json = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in (request.headers.get('accept') or '')
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                if wants_json:
                    return JsonResponse({'status': 'error', 'message': 'Autenticación requerida.'}, status=401)
                return redirect('login')

            usuario = Usuario.objects.filter(id=usuario_id).first()
            if not usuario:
                request.session.flush()
                if wants_json:
                    return JsonResponse({'status': 'error', 'message': 'Autenticación requerida.'}, status=401)
                return redirect('login')

            request.usuario = usuario

            if usuario.rol != role_value:
                messages.error(request, "No tienes permisos para acceder a esta sección.")
                if wants_json:
                    return JsonResponse({'status': 'error', 'message': 'No tienes permisos para acceder a esta sección.'}, status=403)
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        django_user = getattr(request, 'user', None)
        if (
            django_user is not None
            and getattr(django_user, 'is_authenticated', False)
            and (getattr(django_user, 'is_superuser', False) or getattr(django_user, 'is_staff', False))
        ):
            return view_func(request, *args, **kwargs)

        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('login')

        usuario = Usuario.objects.filter(id=usuario_id).first()
        if not usuario:
            request.session.flush()
            return redirect('login')

        request.usuario = usuario

        if usuario.rol not in (RolUsuario.ADMIN, RolUsuario.SUPER_ADMIN):
            return HttpResponseForbidden('Acceso denegado')

        return view_func(request, *args, **kwargs)

    return _wrapped_view