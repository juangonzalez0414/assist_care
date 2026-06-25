"""
Vistas de autenticación con 2FA (autenticación de dos factores) por correo.

Flujo:
  1. El usuario envía credenciales en login_view → authenticate()
  2. Si son válidas, se genera un código de 6 dígitos que se envía por correo
     y se redirige a verificar_codigo_view.
  3. El usuario ingresa el código; si es correcto se inicia sesión con
     django.contrib.auth.login() y además se sincroniza con la sesión custom
     (usuario_id) para que todas las vistas protegidas funcionen.
  4. Todas las variables de sesión 2FA se eliminan al finalizar el flujo.
"""

import random
import time
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from allauth.socialaccount.models import SocialApp

from core.models import EstadoVerificacion, RolUsuario, Usuario

logger = logging.getLogger(__name__)

# ── CONSTANTES ────────────────────────────────────────────────────────────────

# Ruta canónica del backend que usamos para login manual.
AUTH_BACKEND_PATH = 'django.contrib.auth.backends.ModelBackend'

# Claves de sesión usadas durante el flujo 2FA.
SESSION_2FA_KEYS = ('2fa_user_id', '2fa_code', '2fa_timestamp')

# Duración del código en segundos (5 minutos).
CODE_EXPIRY_SECONDS = 300


# ── HELPERS ──────────────────────────────────────────────────────────────────

def generate_2fa_code():
    """Genera un código numérico de 6 dígitos aleatorio."""
    return str(random.randint(100000, 999999))


def _clear_2fa_session(request):
    """Elimina todas las variables de sesión relacionadas con el flujo 2FA."""
    for key in SESSION_2FA_KEYS:
        request.session.pop(key, None)
    request.session.pop('pre_login_user_id', None)
    request.session.pop('codigo_2fa', None)


def _login_context():
    """
    Contexto base del login.

    Evita que la plantilla intente construir la URL de Google cuando todavía no
    existe un SocialApp configurado para ese proveedor.
    """
    google_login_available = SocialApp.objects.filter(provider='google').exists()
    return {
        'google_login_available': google_login_available,
    }


# ── VISTAS ───────────────────────────────────────────────────────────────────

def login_view(request):
    """
    Vista de inicio de sesión con 2FA.

    GET  → renderiza el formulario de login.
    POST → autentica credenciales, genera código 2FA, lo envía por correo
            y redirige a verificar_codigo_view.
    """
    if request.method == 'POST':
        correo = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not correo or not password:
            messages.error(request, 'Por favor ingresa tu correo y contraseña.')
            return render(request, 'two_factor/core/login.html', _login_context())

        # Autenticar contra auth.User usando el email como username
        django_user = authenticate(request, username=correo, password=password)

        if django_user is not None:
            # Verificar estado de la cuenta en el modelo custom
            usuario = Usuario.objects.filter(email__iexact=correo).first()

            if usuario is not None and usuario.estado != EstadoVerificacion.APROBADO:
                messages.info(
                    request,
                    'Tu cuenta está en revisión. Te notificaremos por correo cuando sea aprobada.',
                )
                return redirect('verificacion_proceso')

            # ── Generar código 2FA ─────────────────────────────────────────
            code = generate_2fa_code()
            timestamp = time.time()

            request.session['2fa_user_id'] = str(django_user.id)
            request.session['2fa_code'] = code
            request.session['2fa_timestamp'] = timestamp
            request.session['2fa_backend'] = getattr(django_user, 'backend', AUTH_BACKEND_PATH)
            # También guardamos el email para poder encontrar el Usuario custom
            request.session['2fa_email'] = correo.lower()

            # ── Enviar correo ───────────────────────────────────────────────
            subject = 'Tu código de verificación Axius Care'
            message = (
                f'Hola,\n\n'
                f'Tu código de verificación es: {code}\n\n'
                f'Este código expira en 5 minutos.\n\n'
                f'Saludos,\nEl equipo de Axius Care'
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [correo]

            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Se ha enviado un código de verificación a tu correo.')
            except Exception:
                logger.exception('Error al enviar correo 2FA a %s', correo)
                messages.error(request, 'Hubo un problema al enviar el código. Intenta de nuevo.')
                _clear_2fa_session(request)
                return render(request, 'two_factor/core/login.html', _login_context())

            return redirect('verificar_codigo')

        else:
            messages.error(request, 'Credenciales inválidas. Por favor intenta de nuevo.')

    return render(request, 'two_factor/core/login.html', _login_context())


def verificar_codigo_view(request):
    """
    Vista para verificar el código 2FA enviado por correo.

    GET  → muestra el formulario de ingreso del código (si la sesión 2FA existe).
    POST → valida el código, inicia sesión y limpia la sesión 2FA.
    """
    # ── 1. Validación de sesión ─────────────────────────────────────────────
    if '2fa_user_id' not in request.session:
        messages.error(
            request,
            'Sesión de verificación expirada. Por favor inicia sesión de nuevo.',
        )
        return redirect('login')

    if request.method == 'POST':
        codigo_ingresado = (request.POST.get('codigo') or '').strip()
        codigo_guardado = request.session.get('2fa_code', '')
        timestamp = request.session.get('2fa_timestamp', 0)

        # ── 2. Verificación de expiración ──────────────────────────────────
        if time.time() - timestamp > CODE_EXPIRY_SECONDS:
            messages.error(request, 'El código ha expirado. Por favor inicia sesión de nuevo.')
            _clear_2fa_session(request)
            return redirect('login')

        # ── 3. Verificación del código ──────────────────────────────────────
        if codigo_ingresado == codigo_guardado:
            User = get_user_model()
            try:
                django_user = User.objects.get(pk=request.session['2fa_user_id'])
            except User.DoesNotExist:
                messages.error(request, 'Sesión inválida. Por favor inicia sesión de nuevo.')
                _clear_2fa_session(request)
                return redirect('login')

            # ── 4. Login con Django auth ───────────────────────────────────
            django_user.backend = AUTH_BACKEND_PATH
            django_login(request, django_user)
            # ⭐ CRÍTICO: Resetear timer de la cookie de sesión
            request.session.set_expiry(60)

            # ── 5. Sincronizar con la sesión custom (usuario_id) ─────────
            email = request.session.get('2fa_email', '').lower()
            usuario = Usuario.objects.filter(email__iexact=email).first()
            if usuario:
                request.session['usuario_id'] = str(usuario.id)
                request.usuario = usuario
                logger.info(
                    "2FA exitoso para usuario %s (email=%s, rol=%s, estado=%s)",
                    usuario.id, email, usuario.rol, usuario.estado
                )
            else:
                logger.warning(
                    "No se encontró core.Usuario para django_user.id=%s (email=%s). "
                    "El usuario podría no tener sesión custom.",
                    django_user.id, email
                )

            # ── 6. Limpieza de sesión 2FA ───────────────────────────────
            _clear_2fa_session(request)

            # ── 7. DEBUG: verificar que la sesión quedó bien ──────────────
            logger.debug(
                "Sesión después del login 2FA → "
                "request.user.is_authenticated=%s, "
                "request.session.get('_auth_user_id')=%s, "
                "request.session.get('usuario_id')=%s, "
                "request.usuario=%s",
                getattr(request.user, 'is_authenticated', None),
                request.session.get('_auth_user_id'),
                request.session.get('usuario_id'),
                getattr(request, 'usuario', None),
            )

            # ── 8. Redirección según tipo de usuario ─────────────────────
            if usuario and usuario.estado != EstadoVerificacion.APROBADO:
                return redirect('verificacion_proceso')

            # Verificar si necesita completar perfil
            if usuario:
                has_disc = hasattr(usuario, 'perfil_discapacitado') and usuario.perfil_discapacitado is not None
                has_enf = hasattr(usuario, 'perfil_enfermero') and usuario.perfil_enfermero is not None
                if usuario.rol == RolUsuario.DISCAPACITADO and not has_disc:
                    return redirect('completar_perfil')
                if usuario.rol == RolUsuario.ENFERMERO and not has_enf:
                    return redirect('completar_perfil')

            if usuario and usuario.is_staff:
                return redirect('dashboard_admin')
            if getattr(django_user, 'is_staff', False):
                return redirect('dashboard_admin')
            if usuario and usuario.rol == RolUsuario.ENFERMERO:
                return redirect('dashboard_enfermero')
            if usuario and usuario.rol == RolUsuario.DISCAPACITADO:
                return redirect('dashboard_discapacitado')
            return redirect('dashboard')

        else:
            messages.error(request, 'Código incorrecto. Por favor intenta de nuevo.')

    # GET con sesión válida → mostrar formulario de verificación
    return render(request, 'core/autenticacion/verificar_codigo.html')
