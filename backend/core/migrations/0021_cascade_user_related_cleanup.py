from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_systempulse'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditorialog',
            name='usuario_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='auditoria_logs', to='core.usuario'),
        ),
        migrations.AlterField(
            model_name='reporte',
            name='usuario_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='reportes', to='core.usuario'),
        ),
    ]
