# Generated by Django 4.2.4 on 2023-08-25 14:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('replicator', '0012_replicationschedule_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='replicationschedule',
            name='hour',
        ),
        migrations.RemoveField(
            model_name='replicationschedule',
            name='minute',
        ),
        migrations.RemoveField(
            model_name='replicationschedule',
            name='second',
        ),
    ]