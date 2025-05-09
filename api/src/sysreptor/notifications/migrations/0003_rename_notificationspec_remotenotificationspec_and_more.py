# Generated by Django 5.2 on 2025-04-08 11:56

import itertools

import django.core.serializers.json
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import sysreptor.utils.crypto.fields
from sysreptor.utils.utils import datetime_from_date


def migrate_notifications(apps, schema_editor):
    UserNotification = apps.get_model('notifications', 'UserNotification')
    # Migrate active_until to visible_until
    notifications_active_until = UserNotification.objects \
        .filter(remotenotificationspec__active_until__isnull=False) \
        .filter(visible_until__isnull=True) \
        .select_related('remotenotificationspec')
    for batch in itertools.batched(notifications_active_until, 1000):
        for n in batch:
            n.visible_until = datetime_from_date(n.remotenotificationspec.active_until)
        UserNotification.objects.bulk_update(batch, ['visible_until'])


def reverse_migrate_notifications(apps, schema_editor):
    UserNotification = apps.get_model('notifications', 'UserNotification')
    # Delete all non-remote notifications
    UserNotification.objects.filter(remotenotificationspec__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_remove_notificationspec_instance_conditions'),
        ('pentests', '0063_alter_pentestproject_project_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NotificationSpec',
            new_name='RemoteNotificationSpec',
        ),
        migrations.AlterModelOptions(
            name='usernotification',
            options={'ordering': ['-created']},
        ),
        migrations.RenameField(
            model_name='usernotification',
            old_name='notification',
            new_name='remotenotificationspec',
        ),
        migrations.AlterField(
            model_name='usernotification',
            name='remotenotificationspec',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='notifications.remotenotificationspec'),
        ),
        migrations.AlterUniqueTogether(
            name='usernotification',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='additional_content',
            field=sysreptor.utils.crypto.fields.EncryptedField(base_field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder), editable=True),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='backuplog',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api_utils.backuplog'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pentests.comment'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='finding',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pentests.pentestfinding'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pentests.projectnotebookpage'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pentests.pentestproject'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pentests.reportsection'),
        ),
        migrations.AddField(
            model_name='usernotification',
            name='type',
            field=models.CharField(choices=[('remote', 'Remote'), ('member', 'Member'), ('finished', 'Finished'), ('archived', 'Archived'), ('deleted', 'Deleted'), ('commented', 'Commented'), ('assigned', 'Assigned'), ('backup_missing', 'Backup Missing')], default='remote', max_length=50, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='usernotification',
            name='visible_until',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(code=migrate_notifications, reverse_code=reverse_migrate_notifications),
    ]
