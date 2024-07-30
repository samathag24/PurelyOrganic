from django.apps import AppConfig


class PureorganicsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PureOrganics'

    def ready(self):
        import PureOrganics.signals