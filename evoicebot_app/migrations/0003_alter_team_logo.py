# Generated by Django 5.2 on 2025-04-21 17:14

import storages.backends.gcloud
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evoicebot_app', '0002_alter_project_options_alter_team_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='logo',
            field=models.ImageField(blank=True, null=True, storage=storages.backends.gcloud.GoogleCloudStorage(), upload_to='team_logos/', verbose_name='Logo'),
        ),
    ]
