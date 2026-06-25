from datetime import timedelta
import re
import uuid
from decimal import Decimal

from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class ActivoQuerySet(models.QuerySet):
    def delete(self):
        return super().update(activo=False)

    def hard_delete(self):
        return super().delete()


class ActivoManager(models.Manager):
    def get_queryset(self):
        return ActivoQuerySet(self.model, using=self._db).filter(activo=True)


class UsuarioQuerySet(ActivoQuerySet):
    def delete(self):
        return models.QuerySet.delete(self)

    def hard_delete(self):
        return models.QuerySet.delete(self)


class UsuarioManager(models.Manager):
    def get_queryset(self):
        return UsuarioQuerySet(self.model, using=self._db).filter(activo=True)


class RolUsuario(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super admin'
    ADMIN = 'admin', 'Admin'
    DISCAPACITADO = 'discapacitado', 'Discapacitado'
    ENFERMERO = 'enfermero', 'Enfermero'


class EstadoVerificacion(models.TextChoices):
    PREREGISTRO = 'preregistro', 'Preregistro'
    PENDIENTE_REVISION = 'pendiente_revision', 'Pendiente revisión'
    APROBADO = 'aprobado', 'Aprobado'
    RECHAZADO = 'rechazado', 'Rechazado'


class SexoTipo(models.TextChoices):
    M = 'M', 'M'
    F = 'F', 'F'
    OTRO = 'Otro', 'Otro'


class EstadoPeticion(models.TextChoices):
    ACTIVA = 'activa', 'Activa'
    ASIGNADA = 'asignada', 'Asignada'
    COMPLETADA = 'completada', 'Completada'
    CANCELADA = 'cancelada', 'Cancelada'


class EstadoPostulacion(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    ACEPTADA = 'aceptada', 'Aceptada'
    RECHAZADA = 'rechazada', 'Rechazada'


class Usuario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=RolUsuario.choices)
    estado = models.CharField(max_length=30, choices=EstadoVerificacion.choices, default=EstadoVerificacion.PREREGISTRO)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    objects = UsuarioManager()
    objects_all = UsuarioQuerySet.as_manager()

    class Meta:
        db_table = 'usuarios'
        indexes = [
            models.Index(fields=['email', 'estado'], name='idx_usuarios_email_estado'),
        ]

    def __str__(self):
        return self.email

    @property
    def is_active(self):
        return self.activo and self.estado == EstadoVerificacion.APROBADO

    def delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def deactivate(self):
        self.activo = False
        self.save(update_fields=['activo'])

    @property
    def is_staff(self):
        return self.rol in (RolUsuario.ADMIN, RolUsuario.SUPER_ADMIN)

    @property
    def is_superuser(self):
        return self.rol == RolUsuario.SUPER_ADMIN

    @property
    def nombre_completo(self):
        if self.rol == RolUsuario.ENFERMERO and hasattr(self, 'perfil_enfermero') and self.perfil_enfermero:
            return f'{self.perfil_enfermero.nombres} {self.perfil_enfermero.apellidos}'.strip()
        if self.rol == RolUsuario.DISCAPACITADO and hasattr(self, 'perfil_discapacitado') and self.perfil_discapacitado:
            return f'{self.perfil_discapacitado.nombres} {self.perfil_discapacitado.apellidos}'.strip()
        return ''


class PerfilDiscapacitado(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_discapacitado')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    ciudad = models.CharField(max_length=100)
    telefono_contacto = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=10, choices=SexoTipo.choices)
    foto_perfil = models.FileField(upload_to='avatars/', max_length=500, null=True, blank=True)
    url_cedula = models.FileField(upload_to='cedulas/', max_length=500, null=True, blank=True)
    url_certificado_discapacidad = models.FileField(
        upload_to='certificados/',
        max_length=500,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
    )
    biografia = models.TextField(blank=True, default='')
    historia = models.TextField(blank=True, default='')
    acces_screen_reader = models.BooleanField(default=False)
    acces_high_contrast = models.BooleanField(default=True)
    acces_simplified_nav = models.BooleanField(default=False)
    emergency_nombre = models.CharField(max_length=150, blank=True, default='')
    emergency_parentesco = models.CharField(max_length=80, blank=True, default='')
    emergency_telefono = models.CharField(max_length=30, blank=True, default='')
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'perfil_discapacitado'

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def telefono_contacto_wa(self):
        digits = re.sub(r'\D', '', self.telefono_contacto or '')
        if not digits:
            return ''
        if digits.startswith('57'):
            return digits
        return f'57{digits}'

    @property
    def certificado_discapacidad_url(self):
        certificado = getattr(self, 'url_certificado_discapacidad', None)
        if not certificado:
            return ''
        name = getattr(certificado, 'name', '') or str(certificado)
        if name.startswith(('http://', 'https://')):
            return name
        try:
            return certificado.url
        except Exception:
            return name


class PerfilEnfermero(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_enfermero')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    ciudad = models.CharField(max_length=100)
    direccion_residencia = models.CharField(max_length=255, blank=True, default='')
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=10, choices=SexoTipo.choices)
    telefono_whatsapp = models.CharField(max_length=20)
    foto_perfil = models.FileField(upload_to='avatars/', max_length=500, null=True, blank=True)
    url_cedula = models.FileField(upload_to='cedulas/', max_length=500, null=True, blank=True)
    url_tarjeta_profesional = models.FileField(
        upload_to='tarjetas_profesionales/',
        max_length=500,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
    )
    especialidad = models.CharField(max_length=120, blank=True, default='Registered Nurse')
    cuenta_tipo = models.CharField(max_length=20, blank=True, default='')
    cuenta_banco = models.CharField(max_length=80, blank=True, default='')
    cuenta_numero = models.CharField(max_length=40, blank=True, default='')
    biografia = models.TextField(blank=True, default='')
    calificacion_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('5.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('5.00'))],
    )
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'perfil_enfermero'

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def telefono_whatsapp_wa(self):
        digits = re.sub(r'\D', '', self.telefono_whatsapp or '')
        if not digits:
            return ''
        if digits.startswith('57'):
            return digits
        return f'57{digits}'

    @property
    def tarjeta_profesional_url(self):
        tarjeta = getattr(self, 'url_tarjeta_profesional', None)
        if not tarjeta:
            return ''
        name = getattr(tarjeta, 'name', '') or str(tarjeta)
        if name.startswith(('http://', 'https://')):
            return name
        try:
            return tarjeta.url
        except Exception:
            return name


class Peticion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discapacitado = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='discapacitado_id', related_name='peticiones')
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    fecha_evento = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, default='')
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    google_maps_url = models.CharField(max_length=600, blank=True, default='')
    postulados = models.ManyToManyField(
        Usuario,
        through='Postulacion',
        related_name='servicios_postulados',
        blank=True,
    )
    estado = models.CharField(max_length=20, choices=EstadoPeticion.choices, default=EstadoPeticion.ACTIVA)
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    objects = ActivoManager()
    objects_all = ActivoQuerySet.as_manager()

    class Meta:
        db_table = 'peticiones'
        indexes = [
            models.Index(fields=['ciudad', 'estado'], name='idx_peticiones_ciudad_estado'),
        ]

    def __str__(self):
        return self.titulo

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.save(update_fields=['activo'])

    @property
    def puede_cancelarse(self):
        if self.estado == EstadoPeticion.ACTIVA:
            return True
        if self.estado == EstadoPeticion.ASIGNADA:
            if not self.fecha_aceptacion:
                return True
            limite = self.fecha_aceptacion + timedelta(hours=24)
            return timezone.now() <= limite
        return False


class Postulacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    peticion = models.ForeignKey(Peticion, on_delete=models.CASCADE, db_column='peticion_id', related_name='postulaciones')
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='enfermero_id', related_name='postulaciones')
    estado = models.CharField(max_length=20, choices=EstadoPostulacion.choices, default=EstadoPostulacion.PENDIENTE)
    fecha_postulacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'postulaciones'
        constraints = [
            models.UniqueConstraint(fields=['peticion', 'enfermero'], name='unica_postulacion'),
        ]


class EstadoServicio(models.TextChoices):
    EN_CAMINO = 'En Camino', 'En Camino'
    EN_PROGRESO = 'En Progreso', 'En Progreso'
    COMPLETADO = 'Completado', 'Completado'
    CANCELADO = 'Cancelado', 'Cancelado'


class ServicioAcompanamiento(models.Model):
    peticion = models.ForeignKey(Peticion, on_delete=models.SET_NULL, null=True, blank=True, related_name='servicios')
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='servicios_paciente')
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='servicios_enfermero', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=EstadoServicio.choices, default=EstadoServicio.EN_CAMINO)
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    codigo_verificacion = models.CharField(max_length=4, null=True, blank=True)
    codigo_intentos = models.PositiveSmallIntegerField(default=0)
    codigo_bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    objects = ActivoManager()
    objects_all = ActivoQuerySet.as_manager()

    class Meta:
        db_table = 'servicios_acompanamiento'

    def __str__(self):
        return f'Servicio {self.id}'

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.save(update_fields=['activo'])

class Calificacion(models.Model):
    servicio = models.OneToOneField(ServicioAcompanamiento, on_delete=models.CASCADE, related_name='calificacion')
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_realizadas')
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_recibidas')
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'calificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Calificación {self.id}'

class CalificacionPaciente(models.Model):
    servicio = models.ForeignKey(ServicioAcompanamiento, on_delete=models.CASCADE, related_name='calificaciones_paciente')
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_recibidas_paciente')
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_emitidas_enfermero')
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'calificaciones_paciente'
        ordering = ['-fecha_creacion']
        constraints = [
            models.UniqueConstraint(fields=['servicio', 'enfermero'], name='unica_calificacion_paciente_por_servicio'),
        ]

    def __str__(self):
        return f'CalificacionPaciente {self.id}'


class TipoReporte(models.TextChoices):
    INCIDENCIA = 'incidencia', 'Incidencia'
    AUDITORIA = 'auditoria', 'Auditoría'
    RENDIMIENTO = 'rendimiento', 'Rendimiento'


class Reporte(models.Model):
    usuario_admin = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True, related_name='reportes')
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TipoReporte.choices, default=TipoReporte.INCIDENCIA)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reportes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.titulo} - {self.tipo}'


class AuditoriaLog(models.Model):
    usuario_admin = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True, related_name='auditoria_logs')
    accion = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    archivado = models.BooleanField(default=False)

    class Meta:
        db_table = 'auditoria_logs'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f'{self.fecha_hora} - {self.accion}'


class ConfigTarifas(models.Model):
    precio_hora = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('45000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'config_tarifas'

    def __str__(self):
        return f"precio_hora={self.precio_hora} comision={self.comision}"


class SystemPulse(models.Model):
    name = models.CharField(max_length=80, unique=True)
    revision = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_pulses'

    def __str__(self):
        return f'{self.name}:{self.revision}'

    @classmethod
    def bump(cls, name: str):
        with transaction.atomic():
            pulse, _created = cls.objects.select_for_update().get_or_create(name=name, defaults={'revision': 0})
            pulse.revision = pulse.revision + 1
            pulse.save(update_fields=['revision', 'updated_at'])
            return pulse.revision


class EstadoDonacion(models.TextChoices):
    ACEPTADA = 'aceptada', 'Aceptada'
    RECHAZADA = 'rechazada', 'Rechazada'
    PENDIENTE = 'pendiente', 'Pendiente'


class Donacion(models.Model):
    donante = models.CharField(max_length=160)
    email = models.EmailField(blank=True, default='')
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    referencia_payco = models.CharField(max_length=120, unique=True)
    estado = models.CharField(max_length=20, choices=EstadoDonacion.choices, default=EstadoDonacion.PENDIENTE)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'donaciones'
        indexes = [
            models.Index(fields=['estado', 'fecha_creacion'], name='idx_donaciones_estado_fecha'),
        ]

    def __str__(self):
        return f'{self.referencia_payco} · {self.estado}'

