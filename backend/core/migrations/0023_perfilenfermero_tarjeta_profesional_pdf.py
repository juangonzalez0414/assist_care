from django.core.validators import FileExtensionValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_perfildiscapacitado_certificado_pdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfilenfermero',
            name='url_tarjeta_profesional',
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                upload_to='tarjetas_profesionales/',
                validators=[FileExtensionValidator(['pdf'])],
            ),
        ),
    ]
