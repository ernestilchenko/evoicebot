from django.apps import AppConfig


class EvoicebotAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evoicebot_app'

    def ready(self):
        import evoicebot_app.signals
