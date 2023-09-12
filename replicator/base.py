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
		same_replica_tasks = cls.get_same_replica_tasks(new_task)
		if len(same_replica_tasks) >= cls.MAX_TASKS_FOR_REPLICA:
			logger.info(f"add_task_for_replication: will instantly cancel new task {new_task} because there are already {cls.MAX_TASKS_FOR_REPLICA} same replication tasks")
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
		# logger.info(f"cancel_replication_task: task will be cancelled: {task}")
		if task in cls.running_tasks and not task.running:
			logger.debug(f"cancel_replication_task: will cancel task {task}")
			# task.set_cancel_required()
			task.cancel()
			task.save()
			logger.debug(f"cancel_replication_task: task cancelled {task}")
			return True
		else:
			logger.info(f"cancel_replication_task: could not cancel task {task} - it is already running or not in running_tasks list")
			return False
	
	
	@classmethod
	def find_blockers_for_task(cls, task):
		# logger.debug(f"find_blockers_for_task: starting")
		blockers = []
		for r_task in cls.running_tasks:
			if r_task.complete or r_task.cancelled or r_task == task:
				# logger.debug(f"find_blockers_for_task: ignoring task {r_task} as blocker for {task}")
				continue
			if not r_task.running and (task.id < r_task.id):
				# logger.debug(f"find_blockers_for_task: ignoring task {r_task} as blocker for {task} - it is newer")
				continue
			if r_task.running or (not r_task.running and (task.id > r_task.id)):
				# dest r_task overwrites task src
				if task.replication.src.startswith(r_task.replication.dest):
					# logger.debug(f"find_blockers_for_task: task {r_task} is blocker for {task} because its dest overwrites task src")
					blockers.append(r_task)
				# dest overwrites dest
				if task.replication.dest.startswith(r_task.replication.dest) or r_task.replication.dest.startswith(task.replication.dest):
					# logger.debug(f"find_blockers_for_task: task {r_task} is blocker for {task} because its dest overwrites task dest or vice versa")
					blockers.append(r_task)
		logger.debug(f"find_blockers_for_task: for task {task} found blockers {[str(b) for b in blockers]}")
		return blockers
				
		
	@classmethod
	def get_same_replica_tasks(cls, task):
		same_replica_tasks = []
		for r_task in cls.running_tasks:
			if r_task.cancelled or r_task.complete or task == r_task:
				logger.debug(f"get_same_replica_tasks: ignored task {r_task} for target task {task} as either cancelled or complete")
				continue
			if r_task.replication == task.replication:
				same_replica_tasks.append(r_task)
		logger.debug(f"get_same_replica_tasks: will return {[str(s) for s in same_replica_tasks]} for task {task}")
		return same_replica_tasks
				
	
	# TODO: under testing
	@classmethod
	def get_next_task_to_run(cls, task):
		"""return next task to run if task is not None, else first task to run"""
		# logger.debug(f"get_next_task_to_run: input_task: {task}, tasks: {[str(t.id) + '-' + t.state for t in cls.running_tasks]}")
		ind = cls.running_tasks.index(task) if task is not None else 0
		for task in cls.running_tasks[ind:]:
			if task.complete or task.running or task.cancelled:
				continue
			# logger.debug(f"get_next_task_to_run: input_task: {task}, returning {task}")
			return task
		return None
	
	
	@classmethod
	def launch_task(cls, task):
		if hasattr(task, "cancel_required"):
			logger.debug(f"launch_task: cancel_required: {task.cancel_required}")
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
			# TODO: check this!
			next_task = cls.get_next_task_to_run(None)
			while next_task is not None:
				blockers = cls.find_blockers_for_task(next_task)
				if len(blockers) != 0:
					logger.debug(f"task {next_task} has blockers {[str(b) for b in blockers]}, will try next task")
					time.sleep(cls.LOOP_DELAY_ON_BLOCKER)
					next_task = cls.get_next_task_to_run(next_task)
					continue
				else:
					logger.debug(f"_run_loop: task {next_task} has no blockers, launching")
					cls.launch_task(next_task)
					time.sleep(cls.TASK_START_DELAY)
					next_task = cls.get_next_task_to_run(next_task)
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
		all_schedules = ReplicationSchedule.objects.all().filter(enabled = True).filter(replication__enabled = True)
		logger.debug(f"load_all_schedules: all enabled schedules: {[str(s) for s in all_schedules]} (total: {len(all_schedules)})")
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
	
	
	
