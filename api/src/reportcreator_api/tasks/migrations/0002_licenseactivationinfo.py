# Generated by Django 5.1.4 on 2025-01-09 09:24

import uuid

from django.db import migrations, models

import reportcreator_api.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LicenseActivationInfo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=reportcreator_api.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('license_type', models.CharField(choices=[('community', 'Community'), ('professional', 'Professional')], max_length=255)),
                ('license_hash', models.CharField(max_length=255, null=True)),
                ('last_activation_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
    ]
