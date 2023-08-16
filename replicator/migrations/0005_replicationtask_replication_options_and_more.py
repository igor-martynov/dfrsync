# Generated by Django 4.2.2 on 2023-06-28 14:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('replicator', '0004_alter_replication_dst_file_to_check_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReplicationTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(blank=True, null=True, verbose_name='start')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='end')),
                ('dry_run', models.BooleanField(default=False)),
                ('bytes_copied', models.IntegerField(blank=True, default=0, null=True)),
                ('error', models.BooleanField(default=False)),
                ('warning', models.BooleanField(default=False)),
                ('OK', models.BooleanField(default=False)),
                ('complete', models.BooleanField(default=False)),
                ('error_text', models.TextField(blank=True, null=True)),
                ('cmd_output_text', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='replication',
            name='options',
            field=models.CharField(default='axv --delete', max_length=512),
        ),
        migrations.DeleteModel(
            name='ReplicationRunResult',
        ),
        migrations.AddField(
            model_name='replicationtask',
            name='replication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='replicator.replication'),
        ),
    ]
