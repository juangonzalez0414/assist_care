from django.core.validators import FileExtensionValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_cascade_user_related_cleanup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfildiscapacitado',
            name='url_certificado_discapacidad',
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                upload_to='certificados/',
                validators=[FileExtensionValidator(['pdf'])],
            ),
        ),
    ]
