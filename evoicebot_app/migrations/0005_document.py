# Generated by Django 5.2 on 2025-04-21 18:13

import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evoicebot_app', '0004_project_logo_project_uuid'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('title', models.CharField(max_length=255, verbose_name='Temat')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Opis')),
                ('file', models.FileField(upload_to='documents/', verbose_name='Plik')),
                ('file_format', models.CharField(blank=True, max_length=50, verbose_name='Format pliku')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data aktualizacji')),
                ('file_size', models.PositiveIntegerField(blank=True, null=True, verbose_name='Rozmiar pliku (bajty)')),
                ('users', models.ManyToManyField(related_name='documents', to=settings.AUTH_USER_MODEL, verbose_name='Użytkownicy')),
            ],
            options={
                'verbose_name': 'Dokument',
                'verbose_name_plural': 'Dokumenty',
                'ordering': ['-created_at'],
            },
        ),
    ]
