"""
Middleware de expiración de sesión por inactividad.

VERIFICACIÓN DIRECTA DE EXPIRACIÓN:
===================================
No confiamos en session_key de Django. En su lugar, verificamos
explícitamente si la sesión tiene expiry y si ya pasó.

Funciona con AMBOS sistemas de autenticación:
1. Sistema custom (session['usuario_id']) → login normal
2. Sistema Django auth (request.user) → login con Google/allauth
"""

import logging

from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone

logger = logging.getLogger(__name__)


class InactivitySessionMiddleware:

    EXEMPT_PATHS = frozenset([
        '/login/',
        '/registro/',
        '/verificar-codigo/',
        '/recuperar-contrasena/',
        '/admin/',
        '/django-admin/',
    ])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── 1. Rutas exentas ────────────────────────────────────────────
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            return self.get_response(request)

        # ── 2. ¿Está autenticado en ALGÚN sistema? ────────────────────
        is_custom_auth = bool(request.session.get('usuario_id'))
        user = getattr(request, 'user', None)
        is_django_auth = bool(user and getattr(user, 'is_authenticated', False))
        
        if not (is_custom_auth or is_django_auth):
            return self.get_response(request)

        # ── 3. Verificar expiración explícitamente ─────────────────────
        # get_expiry_age() retorna None si no hay expiry, o los segundos restantes
        # get_expiry_date() retorna None si no hay expiry, o un datetime
        expiry_age = request.session.get_expiry_age()
        expiry_date = request.session.get_expiry_date()

        # Si hay expiry configurado y ya pasó
        if expiry_date is not None:
            now = timezone.now()
            if now >= expiry_date:
                logger.warning(f"SESIÓN EXPIRADA: expiry={expiry_date}, now={now}")
                request.session.flush()
                messages.error(request, 'Tu sesión expiró por inactividad.')
                return redirect('login')

        # ── 4. Sesión vigente ───────────────────────────────────────────
        return self.get_response(request)
