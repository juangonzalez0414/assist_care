from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import Donacion, PerfilDiscapacitado, PerfilEnfermero, Peticion, Postulacion, Usuario


class UsuarioActivoFilter(SimpleListFilter):
    title = 'Activo'
    parameter_name = 'activo'

    def lookups(self, request, model_admin):
        return [('1', 'Sí'), ('0', 'No')]

    def queryset(self, request, queryset):
        value = self.value()
        if value == '1':
            return queryset.filter(estado='aprobado')
        if value == '0':
            return queryset.exclude(estado='aprobado')
        return queryset


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre_completo', 'rol', 'estado', 'is_active', 'is_staff', 'fecha_creacion')
    list_filter = (UsuarioActivoFilter, 'rol', 'estado')
    search_fields = ('email',)
    ordering = ('-fecha_creacion',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('perfil_enfermero', 'perfil_discapacitado')


@admin.register(PerfilEnfermero)
class PerfilEnfermeroAdmin(admin.ModelAdmin):
    list_display = ('usuario_email', 'nombres', 'apellidos', 'cedula', 'telefono_whatsapp', 'ciudad', 'ver_cedula', 'ver_tarjeta_profesional', 'fecha_actualizacion')
    search_fields = ('usuario__email', 'nombres', 'apellidos', 'cedula')
    list_filter = ('ciudad', 'sexo')
    ordering = ('-fecha_actualizacion',)

    def usuario_email(self, obj):
        return obj.usuario.email

    def ver_cedula(self, obj):
        if not obj.url_cedula:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.url_cedula.url)

    def ver_tarjeta_profesional(self, obj):
        if not obj.url_tarjeta_profesional:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.tarjeta_profesional_url)


@admin.register(PerfilDiscapacitado)
class PerfilDiscapacitadoAdmin(admin.ModelAdmin):
    list_display = ('usuario_email', 'nombres', 'apellidos', 'cedula', 'ciudad', 'ver_cedula', 'ver_certificado', 'fecha_actualizacion')
    search_fields = ('usuario__email', 'nombres', 'apellidos', 'cedula')
    list_filter = ('ciudad', 'sexo')
    ordering = ('-fecha_actualizacion',)

    def usuario_email(self, obj):
        return obj.usuario.email

    def ver_cedula(self, obj):
        if not obj.url_cedula:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.url_cedula.url)

    def ver_certificado(self, obj):
        if not obj.url_certificado_discapacidad:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.certificado_discapacidad_url)


@admin.register(Peticion)
class PeticionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'discapacitado', 'ciudad', 'estado', 'fecha_evento', 'fecha_creacion')
    list_filter = ('estado', 'ciudad')
    search_fields = ('titulo', 'descripcion', 'ciudad', 'discapacitado__email')
    ordering = ('-fecha_creacion',)


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('peticion', 'enfermero', 'estado', 'fecha_postulacion')
    list_filter = ('estado',)
    search_fields = ('peticion__titulo', 'enfermero__email')
    ordering = ('-fecha_postulacion',)


@admin.register(Donacion)
class DonacionAdmin(admin.ModelAdmin):
    list_display = ('referencia_payco', 'donante', 'email', 'monto', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('referencia_payco', 'donante', 'email')
    ordering = ('-fecha_creacion',)
