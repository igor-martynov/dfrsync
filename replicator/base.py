#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import logging
import traceback
import threading
import schedule



from .models import ReplicationTask, ReplicationSchedule
from .base_functions import run_command

logger = logging.getLogger(__name__)


class MetaSingleton(type):
	"""Meta class for singleton"""
	
	_instances = {}
	
	def __call__(cls, *args, **kwargs):
		logger.debug(f"MetaSingleton: current _instances: {cls._instances}")
		print(f"MetaSingleton: current _instances: {cls._instances}")
		if cls not in cls._instances:
			cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
			logger.debug(f"MetaSingleton: singleton created. _instances: {cls._instances}")
		else:
			logger.debug(f"MetaSingleton: existing singleton returned")
		return cls._instances[cls]



class ReplicationTaskRunner(object, metaclass = MetaSingleton):
	"""manages running tasks"""
	running_tasks = []
	TASK_CHECK_DELAY = 1.0
	TASK_START_DELAY = 0.5
	LOOP_DELAY = 1.0
	LOOP_DELAY_ON_BLOCKER = 0.1
	MAX_TASKS_FOR_REPLICA = 2
	thread = None
	
	
	def __str__(self):
		return f"ReplicationTaskRunner"
	
	
	@staticmethod
	def create_new_task(replication, schedule = None):
		new_task = ReplicationTask.objects.create(replication = replication, dry_run = replication.dry_run, schedule = schedule)
		logger.info(f"create_new_task: created new task {new_task}")
		return new_task
	
	
	@classmethod
	def add_task_for_replication(cls, replication, schedule = None):
		new_task = cls.create_new_task(replication, schedule = schedule)
		cls.running_tasks.append(new_task)
		blockers = cls.find_blockers_for_replication_task(new_task)
		if len(blockers) >= cls.MAX_TASKS_FOR_REPLICA:
			logger.info(f"add_task_for_replication: will instantly cancel new task {new_task} because there are already 2 blocking tasks")
			new_task.comment = "Cancelled due to existing pending task"
			cls.cancel_replication_task(new_task)
			new_task.save()
		logger.info(f"add_task_for_replication: added new task {new_task}, schedule: {schedule}")
		return new_task
	
	
	@classmethod
	def get_job_for_schedule(cls, schedule):
		try:
			logger.debug(f"get_job_for_schedule: will return job for schedule {schedule}")
			def f():
				return cls.add_task_for_replication(schedule.replication, schedule = schedule)
			return f
		except Exception as e:
			logger.error(f"get_job_for_schedule: got error {e}, traceback: {traceback.format_exc()}")
	
	
	
	# TODO: under development
	@classmethod
	def cancel_replication_task(cls, task):
		logger.info(f"cancel_replication_task: task cancelled: {task}")
		if task in cls.running_tasks and not task.running:
			logger.debug(f"cancel_replication_task: will cancel task {task}")
			task.cancel()
			logger.debug(f"cancel_replication_task: task cancelled {task}")
	
	
	@classmethod
	def find_blockers_for_replication_task(cls, task):
		"""return first found blocker of running now tasks"""
		logger.debug(f"find_blockers_for_replication_task: starting")
		blockers = []
		for r_task in cls.running_tasks:
			if r_task.complete is True:
				logger.debug(f"find_blockers_for_replication_task: ignored complete task {r_task}")
				continue
			if r_task.cancelled is True:
				logger.debug(f"find_blockers_for_replication_task: ignored cancelled task {r_task}")
				continue
			if r_task == task:
				logger.debug(f"find_blockers_for_replication_task: ignored the same task {r_task}")
				continue
			if not r_task.running:
				if task.id > r_task.id:
					blockers.append(r_task)
					logger.debug(f"find_blockers_for_replication_task: added task {r_task} as blocking because its id is less than target task")
				else:
					logger.debug(f"find_blockers_for_replication_task: ignored not running task {r_task}")
					continue
			if task.replication.src.startswith(r_task.replication.src):
				logger.debug(f"find_blockers_for_replication_task: detected crossing of SRC of two tasks: {task} {task.replication.src} and {r_task} {r_task.replication.src} - blocker is wider than current")
				blockers.append(r_task)
				continue
			if r_task.replication.src.startswith(task.replication.src):
				logger.debug(f"find_blockers_for_replication_task: detected crossing of SRC of two tasks: {task} {task.replication.src} and {r_task} {r_task.replication.src} - current is wider than blocker")
				blockers.append(r_task)
				continue
		if len(blockers) == 0:
			logger.debug(f"find_blockers_for_replication_task: could not find blocking tasks for task {task}")
			return blockers
		else:
			logger.debug(f"find_blockers_for_replication_task: found {len(blockers)} blockers: {[str(b) for b in blockers]}")
			return blockers
	
	
	@classmethod
	def get_tasks_to_run(cls):
		tasks_to_run = []
		for task in cls.running_tasks:
			if task.complete or task.running or task.cancelled:
				continue
			tasks_to_run.append(task)
		return tasks_to_run
	
	
	@classmethod
	def launch_task(cls, task):
		if task.cancelled:
			logger.debug(f"launch_task: NOT launching task {task} - because it is cancelled")
			return
		logger.info(f"launch_task: launching task {task}")
		task.launch()
	
	
	@classmethod
	def _run_loop(cls):
		logger.info(f"_run_loop: starting loop ReplicationTaskRunner")
		while True:
			if len(cls.running_tasks) == 0:
				# logger.debug(f"_run_loop: running_tasks is empty")
				time.sleep(cls.LOOP_DELAY)
				continue
			tasks_to_run = cls.get_tasks_to_run()
			if len(tasks_to_run) == 0:
				# logger.debug(f"_run_loop: no task to run, all launched or all complete")
				time.sleep(cls.LOOP_DELAY)
				continue
			for task in tasks_to_run:
				blocker_task = cls.find_blockers_for_replication_task(task)
				if len(blocker_task) != 0:
					logger.debug(f"task {task} has blocker {blocker_task}")
					time.sleep(cls.LOOP_DELAY_ON_BLOCKER)
					continue
				cls.launch_task(task)
				time.sleep(cls.TASK_START_DELAY)
			# logger.debug(f"_run_loop: loop complete ReplicationTaskRunner")
			time.sleep(cls.LOOP_DELAY)
	
	
	@classmethod
	def start_loop_subthread(cls):
		if cls.thread is None:
			logger.info(f"start_loop_subthread: ReplicationTaskRunner thread is None, launching _run_loop")
			cls.thread = threading.Thread(target = cls._run_loop)
			cls.thread.start()
			return
		logger.debug(f"start_loop_subthread: ReplicationTaskRunner thread already running: {cls.thread}")


	@classmethod
	def launch_startup(cls):
		logger.info(f"launch_startup: starting ReplicationTaskRunner")
		cls.start_loop_subthread()

	

class ReplicationScheduler(object, metaclass = MetaSingleton):
	"""manages Replication schedule table, starts new tasks
	
	all ReplicationSchedule should be already created via ReplicationSchedule.objects.create()
	
	"""
	
	thread = None
	schedule = None
	LOOP_DELAY = 1.0
	

	@classmethod
	def _run_loop(cls):
		logger.info(f"_run_loop: starting ReplicationScheduler inner cycle")
		while True:
			schedule.run_pending()
			# logger.debug(f"run_pending: current jobs: {schedule.jobs}")
			time.sleep(cls.LOOP_DELAY)
	
	
	@classmethod
	def start_loop_subthread(cls):
		if cls.thread is None:
			logger.info(f"start_loop_subthread: ReplicationScheduler thread is None, launching _run_loop")
			cls.thread = threading.Thread(target = cls._run_loop)
			cls.thread.start()
			return
		logger.debug(f"start_loop_subthread: ReplicationScheduler thread already running: {cls.thread}")
	
	
	@classmethod
	def launch_startup(cls):
		logger.info(f"launch_startup: starting up ReplicationScheduler")
		cls.load_all_schedules()
		cls.start_loop_subthread()
	
	
	@classmethod
	def load_all_schedules(cls):
		all_schedules = ReplicationSchedule.objects.all().filter(enabled = True)
		logger.debug(f"load_all_schedules: all_schedules: {all_schedules}")
		for s in all_schedules:
			s.load_schedule_object()
		logger.info(f"load_all_schedules: all jobs loaded to scheduler. current jobs: {schedule.jobs}")
	
	
	@classmethod
	def clear_all_schedules(cls):
		schedule.clear()
		logger.info(f"clear_all_schedules: all jobs cleared")
	
	
	@classmethod
	def reload_all_schedules(cls):
		logger.debug(f"reload_all_schedules: starting ReplicationScheduler")
		cls.clear_all_schedules()
		cls.load_all_schedules()
	
	
	
