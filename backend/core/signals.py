import logging
import threading

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .emailing import compact_email_details, make_email_detail, send_notification_email
from .models import Calificacion, Peticion, Postulacion, RolUsuario, ServicioAcompanamiento, SystemPulse, Usuario

logger = logging.getLogger(__name__)

def _schedule_admin_metrics_pulse():
    def _bump():
        try:
            SystemPulse.bump('admin_metrics')
        except Exception:
            logger.exception("Error actualizando pulso de métricas admin.")

    transaction.on_commit(_bump)


@receiver(post_save, sender=Usuario)
def notificar_admins_nuevo_registro(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.rol in (RolUsuario.ADMIN, RolUsuario.SUPER_ADMIN):
        return

    def _send():
        admin_emails = list(
            Usuario.objects.filter(rol__in=[RolUsuario.ADMIN, RolUsuario.SUPER_ADMIN])
            .exclude(email='')
            .values_list('email', flat=True)
            .distinct()
        )
        if not admin_emails:
            return

        from_email = getattr(settings, 'EMAIL_HOST_USER', '') or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        ok = send_notification_email(
            subject='Assist Care · Nuevo registro pendiente de revisión',
            to=admin_emails,
            from_email=from_email,
            status_label='Nuevo registro',
            headline='Se registró un nuevo usuario en la plataforma',
            message='Un nuevo usuario requiere revisión administrativa de perfil y documentos para aprobar su acceso.',
            details=compact_email_details(
                make_email_detail('Correo del usuario', getattr(instance, 'email', '') or 'No registrado'),
                make_email_detail('Rol solicitado', instance.get_rol_display()),
            ),
            cta_text='Abrir panel administrativo',
            cta_url='',
            footer_note='Ingresa a la consola administrativa para revisar y gestionar la solicitud.',
        )
        if not ok:
            logger.error("Error enviando notificación de nuevo registro a administradores.")

    def _dispatch_async():
        t = threading.Thread(target=_send, daemon=True)
        t.start()

    transaction.on_commit(_dispatch_async)


@receiver(post_save, sender=Usuario)
def pulse_admin_metrics_usuario_save(sender, instance, created, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_delete, sender=Usuario)
def pulse_admin_metrics_usuario_delete(sender, instance, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_save, sender=Peticion)
def pulse_admin_metrics_peticion_save(sender, instance, created, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_delete, sender=Peticion)
def pulse_admin_metrics_peticion_delete(sender, instance, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_save, sender=Postulacion)
def pulse_admin_metrics_postulacion_save(sender, instance, created, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_delete, sender=Postulacion)
def pulse_admin_metrics_postulacion_delete(sender, instance, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_save, sender=ServicioAcompanamiento)
def pulse_admin_metrics_servicio_save(sender, instance, created, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_delete, sender=ServicioAcompanamiento)
def pulse_admin_metrics_servicio_delete(sender, instance, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_save, sender=Calificacion)
def pulse_admin_metrics_calificacion_save(sender, instance, created, **kwargs):
    _schedule_admin_metrics_pulse()


@receiver(post_delete, sender=Calificacion)
def pulse_admin_metrics_calificacion_delete(sender, instance, **kwargs):
    _schedule_admin_metrics_pulse()

