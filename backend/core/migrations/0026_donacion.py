import django.core.validators
import django.utils.timezone
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_servicioacompanamiento_codigo_bloqueado_hasta_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donante', models.CharField(max_length=160)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('referencia_payco', models.CharField(max_length=120, unique=True)),
                ('estado', models.CharField(choices=[('aceptada', 'Aceptada'), ('rechazada', 'Rechazada'), ('pendiente', 'Pendiente')], default='pendiente', max_length=20)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'donaciones',
                'indexes': [models.Index(fields=['estado', 'fecha_creacion'], name='idx_donaciones_estado_fecha')],
            },
        ),
    ]
