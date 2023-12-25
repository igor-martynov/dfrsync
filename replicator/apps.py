from django.apps import AppConfig
import sys
import logging
logger = logging.getLogger(__name__)


class ReplicatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'replicator'
    
    
    def ready(self):
        from .base import ReplicationTaskRunner, ReplicationScheduler
        logger.debug(f"ready: starting app {__name__}")
        # from .signals import signal_reload_shedule_jobs
        opts = sys.argv[1:]
        if "runserver" not in opts:
            return        
        ReplicationTaskRunner.launch_startup()
        ReplicationScheduler.launch_startup()

