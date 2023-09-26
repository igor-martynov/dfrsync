from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ReplicatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'replicator'
    
    
    def ready(self):
        from .base import ReplicationTaskRunner, ReplicationScheduler
        logger.debug(f"ready: starting app {__name__}")
        # from .signals import signal_reload_shedule_jobs
        
        ReplicationTaskRunner.launch_startup()
        ReplicationScheduler.launch_startup()
        
        pass