# Generated by Django 4.2.4 on 2023-08-23 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('replicator', '0010_replicationtask_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='replicationschedule',
            name='every_n_days',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='replicationtask',
            name='returncode',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
