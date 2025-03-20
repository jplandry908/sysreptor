# Generated by Django 5.1.3 on 2024-11-25 07:43

import uuid

import sysreptor.utils.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectNumber',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=sysreptor.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('current_id', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
    ]
