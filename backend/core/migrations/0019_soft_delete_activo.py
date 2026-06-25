from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_peticion_postulados'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='peticion',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='servicioacompanamiento',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]
