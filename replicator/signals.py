
from django.db.models.signals import post_save
from django.dispatch import receiver

import logging

from .models import ReplicationSchedule
from .base import ReplicationScheduler

logger = logging.getLogger(__name__)



@receiver(post_save, sender = ReplicationSchedule)
def signal_reload_shedule_jobs(sender, instance, created, **kwargs):
	logger.debug(f"signal_reload_shedule_jobs: signal called")
	ReplicationScheduler.reload_all_schedules()


