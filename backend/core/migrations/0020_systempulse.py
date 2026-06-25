from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_soft_delete_activo'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemPulse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('revision', models.BigIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'system_pulses',
            },
        ),
    ]
