# Generated by Django 4.2.2 on 2023-06-20 07:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Replication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('src', models.CharField(max_length=512)),
                ('dest', models.CharField(max_length=512)),
                ('dry_run', models.BooleanField()),
                ('enabled', models.BooleanField()),
                ('src_file_to_check', models.CharField(max_length=512)),
                ('dst_file_to_check', models.CharField(max_length=512)),
                ('retries', models.IntegerField()),
                ('pre_cmd', models.CharField(max_length=512)),
                ('post_cmd', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='ReplicationSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ReplicationRunResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(verbose_name='end')),
                ('dry_run', models.BooleanField()),
                ('replication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='replicator.replication')),
            ],
        ),
    ]
