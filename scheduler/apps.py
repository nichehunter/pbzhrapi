from django.apps import AppConfig
from django.conf import settings
import threading


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'

    # def ready(self):
    #     if settings.SCHEDULER_DEFAULT:
    #         from scheduler import operators

    #         def run_scheduler():
    #             operators.start()

    #         thread = threading.Thread(target=run_scheduler, daemon=True)
    #         thread.start()
