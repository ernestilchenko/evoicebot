import os
import uuid

from django.contrib.auth.models import User
from django.db import models
from storages.backends.gcloud import GoogleCloudStorage


class Project(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255, verbose_name="Nazwa")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    logo = models.ImageField(upload_to='project_logos/', blank=True, null=True, verbose_name="Logo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekty"


class Team(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nazwa")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True, verbose_name="Logo",
                             storage=GoogleCloudStorage())
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='teams', verbose_name="Projekt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    def __str__(self):
        return self.name

    def get_members(self):
        """Zwraca wszystkich członków zespołu"""
        return UserProfile.objects.filter(team_memberships__team=self)

    class Meta:
        verbose_name = "Zespół"
        verbose_name_plural = "Zespoły"


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('member', 'Członek zespołu'),
        ('viewer', 'Obserwator'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Użytkownik")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="Globalna rola")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    def __str__(self):
        return self.user.username

    def get_teams(self):
        """Zwraca wszystkie zespoły, do których należy użytkownik"""
        return Team.objects.filter(memberships__user_profile=self)

    class Meta:
        verbose_name = "Profil użytkownika"
        verbose_name_plural = "Profile użytkowników"


class TeamMembership(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('member', 'Członek zespołu'),
        ('viewer', 'Obserwator'),
    )

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='team_memberships',
                                     verbose_name="Profil użytkownika")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships', verbose_name="Zespół")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="Rola w zespole")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dołączenia")

    class Meta:
        unique_together = ('user_profile', 'team')
        verbose_name = "Członkostwo w zespole"
        verbose_name_plural = "Członkostwa w zespołach"

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.team.name} ({self.get_role_display()})"


class Document(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255, verbose_name="Tytuł")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    file = models.FileField(upload_to='documents/', verbose_name="Plik", storage=GoogleCloudStorage())
    file_type = models.CharField(max_length=50, verbose_name="Format pliku")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    deadline = models.DateField(null=True, blank=True, verbose_name="Termin ważności")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents',
                                null=True, blank=True, verbose_name="Projekt")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='documents',
                             null=True, blank=True, verbose_name="Zespół")
    users = models.ManyToManyField(UserProfile, related_name='documents', verbose_name="Użytkownicy")

    # AI fields
    ai_description = models.TextField(blank=True, null=True, verbose_name="Opis AI")
    ai_audio = models.FileField(upload_to='documents/audio/', blank=True, null=True,
                                storage=GoogleCloudStorage(), verbose_name="Audio AI")

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumenty"

    def __str__(self):
        return self.title

    def get_file_extension(self):
        return os.path.splitext(self.file.name)[1][1:].lower()

    def save(self, *args, **kwargs):
        # Automatyczne ustawienie typu pliku na podstawie rozszerzenia
        if not self.file_type and self.file:
            self.file_type = self.get_file_extension()
        super().save(*args, **kwargs)


class VoiceCall(models.Model):
    CALL_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('busy', 'Busy'),
        ('no-answer', 'No Answer'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]

    sid = models.CharField(max_length=100, unique=True, verbose_name="Twilio SID")
    to_number = models.CharField(max_length=20, verbose_name="Numer odbiorcy")
    from_number = models.CharField(max_length=20, verbose_name="Numer nadawcy")
    message_text = models.TextField(verbose_name="Treść wiadomości")
    status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, default='initiated', verbose_name="Status")
    duration = models.IntegerField(null=True, blank=True, verbose_name="Czas trwania (sekundy)")
    cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Koszt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="Data odebrania")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Data zakończenia")

    document = models.ForeignKey('Document', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='voice_calls', verbose_name="Dokument")
    user_profile = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='voice_calls', verbose_name="Profil użytkownika")
    confirmation_received = models.BooleanField(default=False, verbose_name="Potwierdzenie otrzymane")

    class Meta:
        verbose_name = "Połączenie głosowe"
        verbose_name_plural = "Połączenia głosowe"
        ordering = ['-created_at']

    def __str__(self):
        return f"Call to {self.to_number} - {self.status}"

    def update_status_from_twilio(self):
        from .api.twilio_service import TwilioService
        service = TwilioService()
        new_status = service.get_call_status(self.sid)
        if new_status and new_status != self.status:
            self.status = new_status
            self.save()
        return new_status
