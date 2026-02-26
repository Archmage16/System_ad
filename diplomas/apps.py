from django.apps import AppConfig

class DiplomasConfig(AppConfig):
    name = 'diplomas'

    def ready(self):
        from .generator import register_fonts
        register_fonts()