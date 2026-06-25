from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.emailing import compact_email_details, make_email_detail, send_notification_email
from core.models import EstadoPeticion, Peticion


class Command(BaseCommand):
    help = 'Closes expired accompaniment requests and notifies patients via email.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--delete', action='store_true')
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = bool(options.get('dry_run'))
        delete = bool(options.get('delete'))
        limit = int(options.get('limit') or 0)

        base_qs = Peticion.objects.select_related('discapacitado').filter(
            estado=EstadoPeticion.ACTIVA,
            fecha_evento__lt=now,
        ).order_by('fecha_evento')

        total = base_qs.count()
        qs = base_qs
        if limit > 0:
            qs = base_qs[:limit]
            total = min(total, limit)
        self.stdout.write(f'Running cleanup task at {now.isoformat()}')
        self.stdout.write(f'Expired requests found: {total}')

        processed = 0
        notified = 0
        cancelled = 0
        removed = 0
        failed = 0

        from_email = (
            getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            or getattr(settings, 'EMAIL_HOST_USER', '')
            or 'no-reply@assistcare.local'
        )

        for peticion in qs:
            processed += 1
            paciente = getattr(peticion, 'discapacitado', None)
            email = (getattr(paciente, 'email', '') or '').strip()
            nombre = (getattr(paciente, 'nombre_completo', '') or '').strip() or email or 'Usuario'
            titulo = (getattr(peticion, 'titulo', '') or '').strip() or 'Solicitud de acompañamiento'

            fecha_inicio = getattr(peticion, 'fecha_evento', None)
            fecha_fin = getattr(peticion, 'fecha_fin', None)
            fecha_label = fecha_inicio.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %I:%M %p') if fecha_inicio else 'No disponible'
            rango_label = fecha_label
            if fecha_inicio and fecha_fin:
                rango_label = (
                    f"{fecha_inicio.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %I:%M %p')}"
                    f" - {fecha_fin.astimezone(timezone.get_current_timezone()).strftime('%I:%M %p')}"
                )

            subject = f'[Assist Care] Notificación: Solicitud de Acompañamiento No Asignada - {titulo}'

            if dry_run:
                self.stdout.write(f'[DRY-RUN] Would notify {email or "SIN CORREO"} and {"delete" if delete else "cancel"} request {peticion.id}')
                continue

            if not email:
                failed += 1
                self.stdout.write(self.style.WARNING(f'Skipped request {peticion.id}: patient email missing'))
                continue

            ok = send_notification_email(
                subject=subject,
                to=email,
                from_email=from_email,
                status_label='Solicitud vencida',
                headline='Tu solicitud fue cancelada automáticamente',
                message=(
                    f'Hola {nombre}, ningún profesional aceptó tu solicitud a tiempo y por eso fue cancelada automáticamente.'
                ),
                details=compact_email_details(
                    make_email_detail('Titulo', titulo),
                    make_email_detail('Fecha y horario', rango_label),
                ),
                footer_note='Si aún necesitas el servicio, crea una nueva solicitud con una programación actualizada.',
            )
            if ok:
                notified += 1
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f'Email failed for request {peticion.id}'))
                continue

            try:
                with transaction.atomic():
                    if delete:
                        peticion.delete()
                        removed += 1
                    else:
                        peticion.estado = EstadoPeticion.CANCELADA
                        peticion.save(update_fields=['estado'])
                        cancelled += 1
            except Exception as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(f'Cleanup failed for request {peticion.id}: {exc}'))

        self.stdout.write(f'Processed: {processed}')
        self.stdout.write(f'Notified: {notified}')
        self.stdout.write(f'Cancelled: {cancelled}')
        self.stdout.write(f'Deleted: {removed}')
        self.stdout.write(f'Failed: {failed}')
