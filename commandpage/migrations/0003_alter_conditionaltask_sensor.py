# Generated by Django 4.2.4 on 2023-08-24 01:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('raspi', '0001_initial'),
        ('commandpage', '0002_conditionaltask'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conditionaltask',
            name='sensor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sensor_node', to='raspi.node'),
        ),
    ]
