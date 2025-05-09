# Generated by Django 4.1.3 on 2022-12-06 14:33

from django.db import migrations, models

import sysreptor.users.querysets


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_pentestuser_created'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='pentestuser',
            managers=[
                ('objects', sysreptor.users.querysets.PentestUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='is_guest',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
