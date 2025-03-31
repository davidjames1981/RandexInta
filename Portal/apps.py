from django.apps import AppConfig
from .utils.folder_setup import ensure_folders_exist


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Portal'

    def ready(self):
        """
        Called when the application is ready.
        Ensures all required folders exist.
        """
        ensure_folders_exist()
