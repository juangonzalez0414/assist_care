import datetime
import re

from django.contrib.auth.hashers import make_password
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import PerfilEnfermeroUpdateForm
from .models import (
    EstadoPeticion,
    EstadoPostulacion,
    EstadoVerificacion,
    PerfilDiscapacitado,
    PerfilEnfermero,
    Peticion,
    Postulacion,
    RolUsuario,
    SexoTipo,
    Usuario,
)


class DashboardAdminSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create(
            email='admin@assist.test',
            password_hash=make_password('Admin123!'),
            rol=RolUsuario.ADMIN,
            estado=EstadoVerificacion.APROBADO,
        )
        session = self.client.session
        session['usuario_id'] = str(self.admin.id)
        session.save()

    def test_dashboard_admin_search_works_without_username_field(self):
        response = self.client.get(reverse('dashboard_admin'), {'search': 'admin'})
        self.assertEqual(response.status_code, 200)


class PerfilEnfermeroUpdateFormTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            email='enfermero@assist.test',
            password_hash=make_password('Nurse123!'),
            rol=RolUsuario.ENFERMERO,
            estado=EstadoVerificacion.APROBADO,
        )
        self.perfil = PerfilEnfermero.objects.create(
            usuario=self.usuario,
            nombres='Ana',
            apellidos='Perez',
            cedula='1234567890',
            ciudad='Bogota',
            fecha_nacimiento=datetime.date(1990, 1, 1),
            sexo=SexoTipo.F,
            telefono_whatsapp='+573001112233',
            url_tarjeta_profesional='https://example.com/tarjeta',
        )

    def test_update_form_normalizes_phone_before_saving(self):
        form = PerfilEnfermeroUpdateForm(
            data={
                'nombres': 'Ana Maria',
                'apellidos': 'Perez Gomez',
                'telefono_whatsapp': '3001234567',
                'ciudad': 'Medellin',
                'direccion_residencia': 'Calle 1 # 2-3',
                'url_tarjeta_profesional': 'https://example.com/nueva-tarjeta',
                'especialidad': 'Adulto mayor',
                'biografia': 'Experiencia en cuidado domiciliario.',
                'cuenta_tipo': 'Ahorros',
                'cuenta_banco': 'Bancolombia',
                'cuenta_numero': '1234567890',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        before_update = self.perfil.fecha_actualizacion
        form.save(self.perfil)
        self.perfil.refresh_from_db()

        self.assertEqual(self.perfil.telefono_whatsapp, '+573001234567')
        self.assertEqual(self.perfil.ciudad, 'Medellin')
        self.assertEqual(self.perfil.cuenta_tipo, 'Ahorros')
        self.assertGreaterEqual(self.perfil.fecha_actualizacion, before_update or timezone.now())

    def test_update_form_rejects_invalid_phone(self):
        form = PerfilEnfermeroUpdateForm(
            data={
                'nombres': 'Ana',
                'apellidos': 'Perez',
                'telefono_whatsapp': '123',
                'ciudad': 'Bogota',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('telefono_whatsapp', form.errors)


class PostulacionMismoDiaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.enfermero = Usuario.objects.create(
            email='nurse@assist.test',
            password_hash=make_password('Nurse123!'),
            rol=RolUsuario.ENFERMERO,
            estado=EstadoVerificacion.APROBADO,
        )
        session = self.client.session
        session['usuario_id'] = str(self.enfermero.id)
        session.save()

        self.paciente_a = Usuario.objects.create(
            email='paciente-a@assist.test',
            password_hash=make_password('Paciente123!'),
            rol=RolUsuario.DISCAPACITADO,
            estado=EstadoVerificacion.APROBADO,
        )
        self.paciente_b = Usuario.objects.create(
            email='paciente-b@assist.test',
            password_hash=make_password('Paciente123!'),
            rol=RolUsuario.DISCAPACITADO,
            estado=EstadoVerificacion.APROBADO,
        )

    def _crear_peticion(self, paciente, fecha_evento, titulo):
        return Peticion.objects.create(
            discapacitado=paciente,
            titulo=titulo,
            descripcion='Servicio de prueba',
            fecha_evento=fecha_evento,
            fecha_fin=fecha_evento + datetime.timedelta(hours=1),
            ciudad='Ibague',
            direccion='Calle 1 # 2-3',
            estado=EstadoPeticion.ACTIVA,
        )

    def test_no_permite_segunda_postulacion_del_mismo_dia(self):
        fecha_base = timezone.make_aware(datetime.datetime(2026, 6, 18, 9, 0))
        peticion_a = self._crear_peticion(self.paciente_a, fecha_base, 'Servicio A')
        peticion_b = self._crear_peticion(
            self.paciente_b,
            timezone.make_aware(datetime.datetime(2026, 6, 18, 15, 0)),
            'Servicio B',
        )
        Postulacion.objects.create(
            peticion=peticion_a,
            enfermero=self.enfermero,
            estado=EstadoPostulacion.PENDIENTE,
        )

        response = self.client.post(
            reverse('postular_peticion', args=[peticion_b.id]),
            data={'next': reverse('dashboard_enfermero')},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Postulacion.objects.filter(enfermero=self.enfermero, peticion=peticion_b).count(),
            0,
        )
        mensajes = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('Ya tienes una postulación registrada para el 18/06/2026' in m for m in mensajes))

    def test_permite_postularse_en_un_dia_diferente(self):
        peticion_a = self._crear_peticion(
            self.paciente_a,
            timezone.make_aware(datetime.datetime(2026, 6, 18, 9, 0)),
            'Servicio A',
        )
        peticion_b = self._crear_peticion(
            self.paciente_b,
            timezone.make_aware(datetime.datetime(2026, 6, 19, 15, 0)),
            'Servicio B',
        )
        Postulacion.objects.create(
            peticion=peticion_a,
            enfermero=self.enfermero,
            estado=EstadoPostulacion.PENDIENTE,
        )

        response = self.client.post(
            reverse('postular_peticion', args=[peticion_b.id]),
            data={'next': reverse('dashboard_enfermero')},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Postulacion.objects.filter(enfermero=self.enfermero, peticion=peticion_b).count(),
            1,
        )


class RegistroDisponibilidadTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            email='existente@assist.test',
            password_hash=make_password('Registro123!'),
            rol=RolUsuario.DISCAPACITADO,
            estado=EstadoVerificacion.APROBADO,
        )
        PerfilDiscapacitado.objects.create(
            usuario=self.usuario,
            nombres='Laura',
            apellidos='Gomez',
            cedula='1234567890',
            ciudad='Bogota',
            fecha_nacimiento=datetime.date(1990, 1, 1),
            sexo=SexoTipo.F,
        )

    def test_retorna_duplicados_de_correo_y_cedula(self):
        response = self.client.get(
            reverse('registro_disponibilidad'),
            {
                'correo': 'existente@assist.test',
                'cedula': '1234567890',
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertTrue(payload['correo']['valid_format'])
        self.assertTrue(payload['correo']['exists'])
        self.assertTrue(payload['cedula']['valid_format'])
        self.assertTrue(payload['cedula']['exists'])

    def test_retorna_disponible_para_datos_unicos(self):
        response = self.client.get(
            reverse('registro_disponibilidad'),
            {
                'correo': 'nuevo@assist.test',
                'cedula': '5555511111',
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertTrue(payload['correo']['valid_format'])
        self.assertFalse(payload['correo']['exists'])
        self.assertTrue(payload['cedula']['valid_format'])
        self.assertFalse(payload['cedula']['exists'])

    def test_retorna_formato_invalido_sin_marcar_duplicado(self):
        response = self.client.get(
            reverse('registro_disponibilidad'),
            {
                'correo': 'correo-invalido',
                'cedula': '12',
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['correo']['valid_format'])
        self.assertFalse(payload['correo']['exists'])
        self.assertFalse(payload['cedula']['valid_format'])
        self.assertFalse(payload['cedula']['exists'])


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            email='reset@assist.test',
            password_hash=make_password('Inicial123!'),
            rol=RolUsuario.DISCAPACITADO,
            estado=EstadoVerificacion.APROBADO,
        )

    def test_forgot_password_sends_reset_email_and_updates_password(self):
        response = self.client.post(
            reverse('forgot_password'),
            {'correo': self.usuario.email},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('restablece tu contraseña', mail.outbox[0].subject.lower())
        self.assertIn('/restablecer-contrasena/', mail.outbox[0].body)

        match = re.search(r'https?://[^\s]+/restablecer-contrasena/[^\s]+', mail.outbox[0].body)
        self.assertIsNotNone(match)
        reset_path = match.group(0)
        token = reset_path.rstrip('/').rsplit('/', 1)[-1]

        reset_response = self.client.post(
            reverse('reset_password', args=[token]),
            {
                'password': 'NuevaClave123!',
                'confirm_password': 'NuevaClave123!',
            },
        )

        self.assertEqual(reset_response.status_code, 302)
        self.assertEqual(reset_response.url, reverse('login'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.password_hash)
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password('NuevaClave123!', self.usuario.password_hash))

    def test_reset_password_rejects_invalid_token(self):
        response = self.client.get(reverse('reset_password', args=['token-invalido']), follow=True)

        self.assertEqual(response.status_code, 200)
        mensajes = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('no es válido' in m.lower() or 'ya expiró' in m.lower() for m in mensajes))
