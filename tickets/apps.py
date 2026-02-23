from django.apps import AppConfig


class TicketsConfig(AppConfig):
    name = "tickets"
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Ticketing System'

    def ready(self):
        import tickets.signals  # noqa
