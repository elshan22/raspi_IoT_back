# Generated by Django 4.2.3 on 2023-08-28 02:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datapage', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='light',
            old_name='time',
            new_name='timestamp',
        ),
        migrations.RenameField(
            model_name='temperature',
            old_name='time',
            new_name='timestamp',
        ),
    ]
