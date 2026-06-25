from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0016_peticion_fecha_fin_peticion_google_maps_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='peticion',
            name='fecha_aceptacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

