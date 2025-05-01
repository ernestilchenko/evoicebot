from django.contrib import admin
from django.utils.html import format_html

from .models import Project, Team, UserProfile, TeamMembership, Document


# Register your models here.
class TeamInline(admin.TabularInline):
    model = Team
    extra = 0
    fields = ('name', 'uuid', 'created_at')
    readonly_fields = ('uuid', 'created_at')


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    fields = ('user_profile', 'role', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'created_at', 'updated_at', 'teams_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [TeamInline]

    def teams_count(self, obj):
        return obj.teams.count()

    teams_count.short_description = 'Liczba zespołów'

    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('name', 'description', 'logo', 'uuid')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'uuid', 'created_at', 'updated_at', 'members_count')
    list_filter = ('project', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'project__name')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'display_logo')
    date_hierarchy = 'created_at'
    inlines = [TeamMembershipInline]

    def members_count(self, obj):
        return obj.memberships.count()

    members_count.short_description = 'Liczba członków'

    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="100" />', obj.logo.url)
        return "Brak logo"

    display_logo.short_description = 'Podgląd logo'

    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('name', 'description', 'logo', 'display_logo', 'project', 'uuid')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at', 'teams_count')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [TeamMembershipInline]

    def teams_count(self, obj):
        return obj.team_memberships.count()

    teams_count.short_description = 'Liczba zespołów'

    fieldsets = (
        ('Użytkownik', {
            'fields': ('user', 'role')
        }),
        ('Kontakt', {
            'fields': ('phone', 'description')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'team', 'role', 'created_at')
    list_filter = ('role', 'team', 'created_at')
    search_fields = ('user_profile__user__username', 'team__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Członkostwo', {
            'fields': ('user_profile', 'team', 'role', 'created_at')
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'project', 'team', 'created_at', 'has_ai_description', 'has_ai_audio')
    list_filter = ('file_type', 'created_at', 'project', 'team')
    search_fields = ('title', 'description', 'file_type')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'file_preview', 'display_ai_audio')
    date_hierarchy = 'created_at'
    filter_horizontal = ('users',)

    def has_ai_description(self, obj):
        return bool(obj.ai_description)

    has_ai_description.boolean = True
    has_ai_description.short_description = 'Opis AI'

    def has_ai_audio(self, obj):
        return bool(obj.ai_audio)

    has_ai_audio.boolean = True
    has_ai_audio.short_description = 'Audio AI'

    def file_preview(self, obj):
        if obj.file:
            if obj.file_type.lower() in ['jpg', 'jpeg', 'png', 'gif']:
                return format_html('<img src="{}" width="200" />', obj.file.url)
            elif obj.file_type.lower() in ['pdf', 'doc', 'docx', 'txt']:
                return format_html('<a href="{}" target="_blank">Otwórz dokument</a>', obj.file.url)
        return "Brak pliku lub podgląd niedostępny"

    file_preview.short_description = 'Podgląd pliku'

    def display_ai_audio(self, obj):
        if obj.ai_audio:
            return format_html(
                '<audio controls><source src="{}" type="audio/wav">Twoja przeglądarka nie obsługuje odtwarzacza audio.</audio>',
                obj.ai_audio.url)
        return "Brak audio AI"

    display_ai_audio.short_description = 'Odtwarzacz audio AI'

    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('title', 'description', 'file', 'file_type', 'uuid')
        }),
        ('Powiązania', {
            'fields': ('project', 'team', 'users')
        }),
        ('AI', {
            'fields': ('ai_description', 'ai_audio', 'display_ai_audio')
        }),
        ('Podgląd', {
            'fields': ('file_preview',)
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
