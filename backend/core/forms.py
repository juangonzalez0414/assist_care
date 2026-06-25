from django import forms
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import date
import re

from datetime import datetime

from django.utils import timezone

from .models import EstadoPeticion, EstadoVerificacion, Peticion, PerfilDiscapacitado, PerfilEnfermero, RolUsuario, SexoTipo, Usuario


CIUDADES_COLOMBIA = [
    ('Bogotá D.C.', [('Bogotá D.C.', 'Bogotá D.C.')]),
    ('Antioquia', [('Medellín', 'Medellín'), ('Bello', 'Bello'), ('Envigado', 'Envigado'), ('Itagüí', 'Itagüí'), ('Rionegro', 'Rionegro')]),
    ('Valle del Cauca', [('Cali', 'Cali'), ('Palmira', 'Palmira'), ('Buenaventura', 'Buenaventura'), ('Tuluá', 'Tuluá')]),
    ('Atlántico', [('Barranquilla', 'Barranquilla'), ('Soledad', 'Soledad')]),
    ('Santander', [('Bucaramanga', 'Bucaramanga'), ('Floridablanca', 'Floridablanca'), ('Girón', 'Girón')]),
    ('Bolívar', [('Cartagena', 'Cartagena'), ('Magangué', 'Magangué')]),
    ('Cundinamarca', [('Soacha', 'Soacha'), ('Chía', 'Chía'), ('Zipaquirá', 'Zipaquirá'), ('Facatativá', 'Facatativá')]),
    ('Risaralda', [('Pereira', 'Pereira'), ('Dosquebradas', 'Dosquebradas')]),
    ('Caldas', [('Manizales', 'Manizales')]),
    ('Meta', [('Villavicencio', 'Villavicencio')]),
    ('Nariño', [('Pasto', 'Pasto'), ('Tumaco', 'Tumaco')]),
    ('Tolima', [('Ibagué', 'Ibagué')]),
]


def _validate_pdf_upload(uploaded_file, field_label):
    if not uploaded_file:
        return uploaded_file

    file_name = (getattr(uploaded_file, 'name', '') or '').strip().lower()
    if not file_name.endswith('.pdf'):
        raise ValidationError(f'El campo {field_label} debe estar en formato PDF.')

    content_type = (getattr(uploaded_file, 'content_type', '') or '').strip().lower()
    if content_type and 'pdf' not in content_type:
        raise ValidationError(f'El archivo enviado en {field_label} no parece ser un PDF válido.')

    return uploaded_file


def _validate_strong_password(password):
    password = password or ''
    if len(password) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('La contraseña debe incluir al menos una letra mayúscula.')
    if not re.search(r'\d', password):
        raise ValidationError('La contraseña debe incluir al menos un número.')
    if not re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError('La contraseña debe incluir al menos un carácter especial.')
    return password


class RegistroUsuarioForm(forms.Form):
    correo = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Correo',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña segura'}),
        label="Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}),
        label="Confirmar Contraseña"
    )
    rol = forms.ChoiceField(
        choices=[
            (RolUsuario.DISCAPACITADO, 'Necesito acompañamiento'),
            (RolUsuario.ENFERMERO, 'Quiero brindar acompañamiento'),
        ],
        label='¿Cómo deseas participar?',
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial=RolUsuario.DISCAPACITADO,
    )

    nombres = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=100)
    apellidos = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=100)
    cedula = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'pattern': r'\d*', 'autocomplete': 'off'}),
        max_length=20,
    )
    ciudad = forms.ChoiceField(
        choices=CIUDADES_COLOMBIA,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    sexo = forms.ChoiceField(
        choices=[(SexoTipo.M, 'Masculino'), (SexoTipo.F, 'Femenino')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Sexo',
    )
    cedula_documento = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'}),
        label='Cédula escaneada (PDF o imagen)',
    )
    telefono_whatsapp = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'pattern': r'\d*', 'maxlength': '10', 'autocomplete': 'off'}),
        max_length=10,
        required=False,
        label='Teléfono WhatsApp (solo enfermero)',
    )
    url_certificado_discapacidad = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        label='Certificado de discapacidad (PDF)',
    )
    url_tarjeta_profesional = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        label='Tarjeta profesional de enfermería (PDF)',
    )

    field_order = [
        'nombres',
        'apellidos',
        'cedula',
        'ciudad',
        'fecha_nacimiento',
        'sexo',
        'cedula_documento',
        'correo',
        'rol',
        'telefono_whatsapp',
        'url_certificado_discapacidad',
        'url_tarjeta_profesional',
        'password',
        'confirm_password',
    ]

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo and not re.match(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(?:\.[A-Za-z]{2,})?$', correo):
            raise ValidationError('El formato del correo no es válido.')
        if correo and Usuario.objects_all.filter(email__iexact=correo).exists():
            raise ValidationError('Ya existe una cuenta con este correo.')
        return correo

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula and not re.match(r'^\d{5,20}$', cedula):
            raise ValidationError('La cédula debe contener solo números (5 a 20 dígitos).')
        if cedula and (
            PerfilDiscapacitado.objects.filter(cedula=cedula).exists()
            or PerfilEnfermero.objects.filter(cedula=cedula).exists()
        ):
            raise ValidationError('Ya existe un perfil con esta cédula.')
        return cedula

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        return _validate_strong_password(password)

    def clean_telefono_whatsapp(self):
        telefono = (self.cleaned_data.get('telefono_whatsapp') or '').strip()
        if telefono and not re.match(r'^\d{10}$', telefono):
            raise ValidationError('El teléfono debe contener 10 dígitos numéricos.')
        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            today = date.today()
            age = today.year - fecha.year - ((today.month, today.day) < (fecha.month, fecha.day))
            if age < 18:
                raise ValidationError("Debes ser mayor de edad para registrarte.")
        return fecha

    def clean_url_certificado_discapacidad(self):
        return _validate_pdf_upload(
            self.cleaned_data.get('url_certificado_discapacidad'),
            'Certificado de discapacidad',
        )

    def clean_url_tarjeta_profesional(self):
        return _validate_pdf_upload(
            self.cleaned_data.get('url_tarjeta_profesional'),
            'Tarjeta profesional',
        )

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        telefono_whatsapp = cleaned_data.get('telefono_whatsapp')
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        certificado_discapacidad = cleaned_data.get('url_certificado_discapacidad')
        url_tarjeta_profesional = cleaned_data.get('url_tarjeta_profesional')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")

        if rol == RolUsuario.ENFERMERO and not telefono_whatsapp:
            self.add_error('telefono_whatsapp', 'Este campo es obligatorio para el rol enfermero.')

        if rol == RolUsuario.ENFERMERO and not url_tarjeta_profesional:
            self.add_error('url_tarjeta_profesional', 'Este campo es obligatorio para el rol enfermero.')

        if rol == RolUsuario.DISCAPACITADO and not certificado_discapacidad:
            self.add_error('url_certificado_discapacidad', 'Este campo es obligatorio para el rol discapacitado.')

        return cleaned_data

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        usuario = Usuario.objects.create(
            email=data['correo'],
            password_hash=make_password(data['password']),
            rol=data['rol'],
            estado=EstadoVerificacion.PENDIENTE_REVISION,
        )

        if data['rol'] == RolUsuario.DISCAPACITADO:
            PerfilDiscapacitado.objects.create(
                usuario=usuario,
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                cedula=data['cedula'],
                ciudad=data['ciudad'],
                fecha_nacimiento=data['fecha_nacimiento'],
                sexo=data['sexo'],
                url_cedula=data['cedula_documento'],
                url_certificado_discapacidad=data['url_certificado_discapacidad'] or None,
            )
        elif data['rol'] == RolUsuario.ENFERMERO:
            PerfilEnfermero.objects.create(
                usuario=usuario,
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                cedula=data['cedula'],
                ciudad=data['ciudad'],
                fecha_nacimiento=data['fecha_nacimiento'],
                sexo=data['sexo'],
                telefono_whatsapp=f"+57{data['telefono_whatsapp']}",
                url_cedula=data['cedula_documento'],
                url_tarjeta_profesional=data['url_tarjeta_profesional'] or None,
            )

        return usuario

class CompletarPerfilSocialForm(forms.Form):
    rol = forms.ChoiceField(
        choices=[
            (RolUsuario.DISCAPACITADO, 'Necesito acompañamiento'),
            (RolUsuario.ENFERMERO, 'Quiero brindar acompañamiento'),
        ],
        label='¿Cómo deseas participar?',
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial=RolUsuario.DISCAPACITADO,
    )

    nombres = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=100)
    apellidos = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=100)
    cedula = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'pattern': r'\d*', 'autocomplete': 'off'}),
        max_length=20,
    )
    ciudad = forms.ChoiceField(
        choices=CIUDADES_COLOMBIA,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    sexo = forms.ChoiceField(
        choices=[(SexoTipo.M, 'Masculino'), (SexoTipo.F, 'Femenino')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Sexo',
    )
    cedula_documento = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'}),
        label='Cédula escaneada (PDF o imagen)',
    )
    telefono_whatsapp = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'pattern': r'\d*', 'maxlength': '10', 'autocomplete': 'off'}),
        max_length=10,
        required=False,
        label='Teléfono WhatsApp (solo enfermero)',
    )
    url_certificado_discapacidad = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        label='Certificado de discapacidad (solo paciente)',
    )
    url_tarjeta_profesional = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        label='Tarjeta profesional de enfermería (solo enfermero, PDF)',
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._usuario = usuario

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula and not re.match(r'^\d{5,20}$', cedula):
            raise ValidationError('La cédula debe contener solo números (5 a 20 dígitos).')

        if cedula:
            q1 = PerfilDiscapacitado.objects.filter(cedula=cedula)
            q2 = PerfilEnfermero.objects.filter(cedula=cedula)
            if self._usuario is not None:
                q1 = q1.exclude(usuario=self._usuario)
                q2 = q2.exclude(usuario=self._usuario)
            if q1.exists() or q2.exists():
                raise ValidationError('Ya existe un perfil con esta cédula.')
        return cedula

    def clean_telefono_whatsapp(self):
        telefono = (self.cleaned_data.get('telefono_whatsapp') or '').strip()
        if telefono and not re.match(r'^\d{10}$', telefono):
            raise ValidationError('El teléfono debe contener 10 dígitos numéricos.')
        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            today = date.today()
            age = today.year - fecha.year - ((today.month, today.day) < (fecha.month, fecha.day))
            if age < 18:
                raise ValidationError("Debes ser mayor de edad para continuar.")
        return fecha

    def clean_url_certificado_discapacidad(self):
        return _validate_pdf_upload(
            self.cleaned_data.get('url_certificado_discapacidad'),
            'Certificado de discapacidad',
        )

    def clean_url_tarjeta_profesional(self):
        return _validate_pdf_upload(
            self.cleaned_data.get('url_tarjeta_profesional'),
            'Tarjeta profesional',
        )

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        telefono_whatsapp = cleaned_data.get('telefono_whatsapp')
        certificado_discapacidad = cleaned_data.get('url_certificado_discapacidad')
        url_tarjeta_profesional = cleaned_data.get('url_tarjeta_profesional')
        perfil_discapacitado_existente = getattr(self._usuario, 'perfil_discapacitado', None) if self._usuario else None
        perfil_enfermero_existente = getattr(self._usuario, 'perfil_enfermero', None) if self._usuario else None
        certificado_existente = bool(
            perfil_discapacitado_existente
            and getattr(perfil_discapacitado_existente, 'url_certificado_discapacidad', None)
        )
        tarjeta_existente = bool(
            perfil_enfermero_existente
            and getattr(perfil_enfermero_existente, 'url_tarjeta_profesional', None)
        )

        if rol == RolUsuario.ENFERMERO and not telefono_whatsapp:
            self.add_error('telefono_whatsapp', 'Este campo es obligatorio para el rol enfermero.')

        if rol == RolUsuario.ENFERMERO and not url_tarjeta_profesional and not tarjeta_existente:
            self.add_error('url_tarjeta_profesional', 'Este campo es obligatorio para el rol enfermero.')

        if rol == RolUsuario.DISCAPACITADO and not certificado_discapacidad and not certificado_existente:
            self.add_error('url_certificado_discapacidad', 'Este campo es obligatorio para el rol paciente.')

        return cleaned_data

    @transaction.atomic
    def save(self, usuario):
        data = self.cleaned_data
        usuario.rol = data['rol']
        usuario.estado = EstadoVerificacion.PENDIENTE_REVISION
        usuario.save(update_fields=['rol', 'estado'])

        if data['rol'] == RolUsuario.DISCAPACITADO:
            PerfilEnfermero.objects.filter(usuario=usuario).delete()
            perfil_discapacitado_existente = getattr(usuario, 'perfil_discapacitado', None)
            PerfilDiscapacitado.objects.update_or_create(
                usuario=usuario,
                defaults={
                    'nombres': data['nombres'],
                    'apellidos': data['apellidos'],
                    'cedula': data['cedula'],
                    'ciudad': data['ciudad'],
                    'fecha_nacimiento': data['fecha_nacimiento'],
                    'sexo': data['sexo'],
                    'url_cedula': data['cedula_documento'],
                    'url_certificado_discapacidad': (
                        data['url_certificado_discapacidad']
                        or getattr(perfil_discapacitado_existente, 'url_certificado_discapacidad', None)
                    ),
                },
            )
        elif data['rol'] == RolUsuario.ENFERMERO:
            PerfilDiscapacitado.objects.filter(usuario=usuario).delete()
            perfil_enfermero_existente = getattr(usuario, 'perfil_enfermero', None)
            PerfilEnfermero.objects.update_or_create(
                usuario=usuario,
                defaults={
                    'nombres': data['nombres'],
                    'apellidos': data['apellidos'],
                    'cedula': data['cedula'],
                    'ciudad': data['ciudad'],
                    'fecha_nacimiento': data['fecha_nacimiento'],
                    'sexo': data['sexo'],
                    'telefono_whatsapp': f"+57{data['telefono_whatsapp']}",
                    'url_cedula': data['cedula_documento'],
                    'url_tarjeta_profesional': (
                        data['url_tarjeta_profesional']
                        or getattr(perfil_enfermero_existente, 'url_tarjeta_profesional', None)
                    ),
                },
            )

        return usuario

class LoginForm(forms.Form):
    correo = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'})
    )


class ForgotPasswordForm(forms.Form):
    correo = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        label='Correo electrónico',
    )


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña segura'}),
        label='Nueva contraseña',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirma la nueva contraseña'}),
        label='Confirmar contraseña',
    )

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        return _validate_strong_password(password)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')
        return cleaned_data


class PerfilEnfermeroUpdateForm(forms.Form):
    CUENTA_TIPO_CHOICES = (
        ('', 'Seleccionar...'),
        ('Ahorros', 'Ahorros'),
        ('Corriente', 'Corriente'),
    )

    nombres = forms.CharField(max_length=100)
    apellidos = forms.CharField(max_length=100)
    telefono_whatsapp = forms.CharField(max_length=16)
    ciudad = forms.CharField(max_length=100)
    direccion_residencia = forms.CharField(max_length=255, required=False)
    url_tarjeta_profesional = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,application/pdf'}),
    )
    especialidad = forms.CharField(max_length=120, required=False)
    biografia = forms.CharField(required=False, widget=forms.Textarea)
    cuenta_tipo = forms.ChoiceField(choices=CUENTA_TIPO_CHOICES, required=False)
    cuenta_banco = forms.CharField(max_length=80, required=False)
    cuenta_numero = forms.CharField(max_length=40, required=False)

    def clean_nombres(self):
        value = (self.cleaned_data.get('nombres') or '').strip()
        if not value:
            raise ValidationError('Los nombres son obligatorios.')
        return value

    def clean_apellidos(self):
        value = (self.cleaned_data.get('apellidos') or '').strip()
        if not value:
            raise ValidationError('Los apellidos son obligatorios.')
        return value

    def clean_ciudad(self):
        value = (self.cleaned_data.get('ciudad') or '').strip()
        if not value:
            raise ValidationError('La ciudad es obligatoria.')
        return value

    def clean_telefono_whatsapp(self):
        value = (self.cleaned_data.get('telefono_whatsapp') or '').strip()
        digits = re.sub(r'\D', '', value)
        if digits.startswith('57') and len(digits) == 12:
            digits = digits[2:]
        if not re.match(r'^\d{10}$', digits):
            raise ValidationError('El teléfono debe contener 10 dígitos válidos.')
        return f'+57{digits}'

    def clean_direccion_residencia(self):
        return (self.cleaned_data.get('direccion_residencia') or '').strip()

    def clean_url_tarjeta_profesional(self):
        return _validate_pdf_upload(
            self.cleaned_data.get('url_tarjeta_profesional'),
            'Tarjeta profesional',
        )

    def clean_especialidad(self):
        return (self.cleaned_data.get('especialidad') or '').strip()

    def clean_biografia(self):
        return (self.cleaned_data.get('biografia') or '').strip()

    def clean_cuenta_banco(self):
        return (self.cleaned_data.get('cuenta_banco') or '').strip()

    def clean_cuenta_numero(self):
        return (self.cleaned_data.get('cuenta_numero') or '').strip()

    def save(self, perfil):
        data = self.cleaned_data
        perfil.nombres = data['nombres']
        perfil.apellidos = data['apellidos']
        perfil.telefono_whatsapp = data['telefono_whatsapp']
        perfil.ciudad = data['ciudad']
        perfil.direccion_residencia = data['direccion_residencia']
        if data['url_tarjeta_profesional']:
            perfil.url_tarjeta_profesional = data['url_tarjeta_profesional']
        perfil.especialidad = data['especialidad']
        perfil.biografia = data['biografia']
        perfil.cuenta_tipo = data['cuenta_tipo']
        perfil.cuenta_banco = data['cuenta_banco']
        perfil.cuenta_numero = data['cuenta_numero']
        perfil.fecha_actualizacion = timezone.now()
        perfil.save()
        return perfil


class SolicitarAyudaForm(forms.ModelForm):
    fecha_evento_fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha del evento',
    )
    fecha_evento_hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora del evento',
    )

    class Meta:
        model = Peticion
        fields = ['titulo', 'descripcion', 'ciudad', 'direccion']

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._usuario = usuario

    def clean(self):
        cleaned = super().clean()
        f = cleaned.get('fecha_evento_fecha')
        h = cleaned.get('fecha_evento_hora')
        if not f or not h:
            return cleaned
        dt = datetime.combine(f, h)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        if dt <= timezone.now():
            raise ValidationError('La fecha y hora de inicio no pueden ser anteriores al momento actual.')

        if self._usuario is not None:
            tz = timezone.get_current_timezone()
            inicio_dia = timezone.make_aware(datetime.combine(f, datetime.min.time()), tz)
            fin_dia = inicio_dia + timedelta(days=1)
            usuario_id = getattr(self._usuario, 'pk', None)
            print(f'DEBUG: Validando solicitud para el Usuario ID: {usuario_id}')
            existe_mismo_dia = Peticion.objects.filter(
                discapacitado_id=usuario_id,
                fecha_evento__gte=inicio_dia,
                fecha_evento__lt=fin_dia,
                estado__in=[
                    EstadoPeticion.ACTIVA,
                    EstadoPeticion.ASIGNADA,
                ],
            ).exists()
            if existe_mismo_dia:
                raise ValidationError(
                    f'Ya tienes un acompañamiento programado para el {f.strftime("%d/%m/%Y")}. '
                    'Solo puedes crear otro para un día diferente.'
                )

        cleaned['fecha_evento'] = dt
        return cleaned

    def save_for_user(self, usuario):
        inst = super().save(commit=False)
        inst.discapacitado = usuario
        inst.estado = EstadoPeticion.ACTIVA
        inst.fecha_evento = self.cleaned_data['fecha_evento']
        inst.save()
        return inst


class CrearAdminForm(forms.Form):
    correo = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'adm-input', 'placeholder': 'admin@ejemplo.com'}),
        label='Correo del administrador',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'adm-input', 'placeholder': 'Contraseña segura'}),
        label='Contraseña',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'adm-input', 'placeholder': 'Confirmar contraseña'}),
        label='Confirmar contraseña',
    )

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo and not re.match(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(?:\.[A-Za-z]{2,})?$', correo):
            raise ValidationError('El formato del correo no es válido.')
        if correo and Usuario.objects.filter(email__iexact=correo).exists():
            raise ValidationError('Ya existe una cuenta con este correo.')
        return correo

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if len(password) < 6:
            raise ValidationError('La contraseña debe tener al menos 6 caracteres.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe incluir al menos una letra mayúscula.')
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe incluir al menos un número.')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('La contraseña debe incluir al menos un carácter especial.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        return Usuario.objects.create(
            email=data['correo'],
            password_hash=make_password(data['password']),
            rol=RolUsuario.ADMIN,
            estado='aprobado',
        )
