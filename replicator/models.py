from django.db import models
from django.urls import reverse
from django.utils import timezone
# import datetime
import logging
import traceback
import threading


logger = logging.getLogger(__name__)

from .base_functions import run_command, run_command_with_returncode



class Replication(models.Model):
	""""""
	name = models.CharField(max_length = 128, unique = True)
	src = models.CharField(max_length = 512, default = None)
	dest = models.CharField(max_length = 512, default = None)
	options = models.CharField(max_length = 512, default = "-axv --delete")
	dry_run = models.BooleanField(default = False)
	enabled = models.BooleanField(default = True)
	src_file_to_check = models.CharField(max_length = 512, default = None, blank = True, null = True)
	dst_file_to_check = models.CharField(max_length = 512, default = None, blank = True, null = True)
	retries = models.IntegerField(default = 3)
	pre_cmd = models.CharField(max_length = 512, default = None, blank = True, null = True)
	post_cmd = models.CharField(max_length = 512, default = None, blank = True, null = True)
	RSYNC_BIN = "rsync"


	def __str__(self):
		return f"Replication {self.name}"

	
	def get_absolute_url(self):
		rev_tmp = reverse("replicator:replication_detail", args = (self.id,))
		return rev_tmp
		
	
	@property
	def src_is_local(self):
		return self.src.startswith("/")
	
	
	@property
	def dest_is_local(self):
		return self.dest.startswith("/")
	
	
	@property
	def remote_host(self):
		if self.src_is_local and self.dest_is_local:
			return None
		if not self.src_is_local and not self.dest_is_local:
			logger.error(f"remote_host: unsupported configuration of replication: both are remote")
			raise NotImplemented
		if self.src_is_local and not self.dest_is_local:
			remote_part = self.dest
		if self.dest_is_local and not self.src_is_local:
			remote_part = self.src
		if "@" in remote_part:
			remote_host = remote_part.split(":")[0].split("@")[1]
		else:
			remote_host = remote_part.split(":")[0]
		logger.debug(f"remote_host: will return remote host {remote_host}")
		return remote_host
		
	
	@property
	def resulting_cmd(self):
		return f"{self.RSYNC_BIN} {self.options} {self.src} {self.dest}"



class ReplicationSchedule(models.Model):
	"""one row of Replication schedule
	
	will be supported schedules like:
	every hour at MM:SS
	everyday at HH:MM:SS
	every monday at HH:MM:SS
	every 10th day of month at HH:MM:SS
	every N days at HH:MM:SS
	at YYYY-MM-DD HH:MM:SS (one time in future)
	"""
	
	name = models.CharField(max_length = 128, unique = True, blank = True, null = True)
	replication = models.ForeignKey(Replication, on_delete = models.CASCADE)
	hour = models.IntegerField(default = None, blank = True, null = True)
	minute = models.IntegerField(default = None, blank = True, null = True)
	second = models.IntegerField(default = None, blank = True, null = True)
	every_n_days = models.IntegerField(default = None, blank = True, null = True)
	dom = models.IntegerField(default = None, blank = True, null = True)
	month = models.IntegerField(default = None, blank = True, null = True)
	year = models.IntegerField(default = None, blank = True, null = True)
	dow = models.IntegerField(default = None, blank = True, null = True)
	enabled = models.BooleanField(default = True)
	
	
	def get_absolute_url(self):
		rev_tmp = reverse("replicator:schedule_detail", args = (self.pk,))
	
	
	@property
	def is_hourly(self):
		if (self.hour is None and self.minute is not None 
			and not self.is_daily 
			and not self.is_weekly 
			and not self.is_monthly):
			return True
		return False
	
	
	@property
	def is_daily(self):
		if (self.hour is not None 
			and self.dom is None 
			and self.month is None 
			and self.year is None 
			and self.dow is None
			and not self.is_every_n_days):
			return True
		return False
	
	
	@property
	def is_weekly(self):
		if (self.dow is not None and self.dom is None 
			and not self.is_hourly 
			and not self.is_daily
			and not self.is_every_n_days):
			return True
		return False
	
	
	@property
	def is_monthly(self):
		if (self.dom is not None 
			and self.dow is None 
			and not self.is_hourly 
			and not self.is_daily
			and not self.is_every_n_days):
			return True
		return False	
	
	
	@property
	def is_every_n_days(self):
		# if (self.every_n_days is not None 
		# 	and not self.is_hourly 
		# 	and not self.is_daily):
		if (self.every_n_days is not None):
			return True
		return False
	
	
	@property
	def is_one_time_in_future(self):
		if (self.year is not None 
			and self.month is not None 
			and not self.is_monthly):
			return True
		return False
		
	
	@property
	def hr_schedule(self):
		import calendar
		calendar.setfirstweekday(calendar.MONDAY)
		seconds = "00" if self.second is None else f"{self.second:02}"
		try:
			if self.is_hourly:
				return f"hourly, at {self.minute:02}:{seconds}"
			elif self.is_daily:
				return f"daily, at {self.hour:02}:{self.minute:02}:{seconds}"
			elif self.is_weekly: # TODO: dow
				return f"weekly, at {calendar.day_name[self.dow]}, {self.hour:02}:{self.minute:02}:{seconds}"
			elif self.is_monthly:
				return f"monthly, at {self.dom} at {self.hour:02}:{self.minute:02}:{seconds}"
			elif self.is_every_n_days:
				return f"every {self.every_n_days} days, at {self.hour:02}:{self.minute:02}:{seconds}"
			elif self.is_one_time_in_future:
				return f"one time in future, at {self.year}-{self.month}-{self.dom} {self.hour:02}:{self.minute:02}:{seconds}"
			else:
				return "UNKNOWN"
		except Exception as e:
			logger.error(f"hr_schedule: got error {e}, traceback: {traceback.format_exc()}")
			return "UNKNOWN/INVALID"
	
	
	@property
	def related_tasks(self):
		related_tasks = ReplicationTask.objects.all().filter(schedule = self)
		logger.debug(f"related_tasks: loaded {len(related_tasks)} related tasks")
		return related_tasks
	
	
	def load_schedule_object(self):
		import schedule
		from .base import ReplicationTaskRunner
		
		def date_str_res():
			if self.second is None:
				_date_str = f"{self.hour:02}:{self.minute:02}:00"
			else:
				_date_str = f"{self.hour:02}:{self.minute:02}:{self.second:02}"
			return _date_str
		
		if self.is_daily:
			# if self.second is None:
			# 	date_str = f"{self.hour:02}:{self.minute:02}:00"
			# else:
			# 	date_str = f"{self.hour:02}:{self.minute:02}:{self.second:02}"
			self.job = schedule.every().day.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.is_hourly:
			if self.second is None:
				date_str = f"{self.minute:02}:00"
			else:
				date_str = f"{self.minute:02}:{self.second:02}"
			self.job = schedule.every().hour.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.is_weekly:
			# if self.second is None:
			# 	date_str = f"{self.hour:02}:{self.minute:02}:00"
			# else:
			# 	date_str = f"{self.hour:02}:{self.minute:02}:{self.second:02}"
			match self.dow:
				case 0:
					self.job = schedule.every().monday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 1:
					self.job = schedule.every().tuesday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 2:
					self.job = schedule.every().wednesday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 3:
					self.job = schedule.every().thursday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 4:
					self.job = schedule.every().friday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 5:
					self.job = schedule.every().saturday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 6:
					self.job = schedule.every().sunday.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.every_n_days:
			self.job = schedule.every(self.every_n_days).days.at(date_str_res()).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.is_monthly:
			raise NotImplemented
			# monthly is not supported by schedule
			# self.job = schedule.every().month.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
			pass
		elif self.is_one_time_in_future:
			raise NotImplemented		
		else:
			logger.error(f"load_schedule_object: unsupported schedule type, please check")
			return
				
		logger.debug(f"load_schedule_object: added job {self.job}")
	
	
	@property
	def descr(self):
		return "description"



class ReplicationTask(models.Model):
	"""Replication task, will be saved to DB"""
	replication = models.ForeignKey(Replication, on_delete = models.CASCADE)
	schedule = models.ForeignKey(ReplicationSchedule, on_delete = models.CASCADE, default = None, blank = True, null = True)
	start = models.DateTimeField("start", blank = True, null = True)
	end = models.DateTimeField("end", blank = True, null = True)
	dry_run = models.BooleanField(default = False)
	bytes_copied = models.IntegerField(default = 0, blank = True, null = True)
	error = models.BooleanField(default = False)
	warning = models.BooleanField(default = False)
	running = models.BooleanField(default = False)
	OK = models.BooleanField(default = False)
	complete = models.BooleanField(default = False)
	cancelled = models.BooleanField(default = False)
	error_text = models.TextField(blank = True, null = True)
	cmd_output_text = models.TextField(blank = True, null = True)
	returncode = models.IntegerField(default = None, blank = True, null = True)
	
	RETRY_DELAY_S = 5.0
	
	
	def _set_thread(self, _thread):
		self._thread = _thread
	
		
	def _get_thread(self):
		return self._thread
	
	
	thread = property(_get_thread, _set_thread)
		
	
	def __str__(self):
		return f"ReplicationTask {self.id} for replica {self.replication}"
		
	
	# TODO: under testing and rewrite
	def check_connection_via_ICMP(self):
		"""check connection via ICMP.
		returns True if reachable, False if unreachable, None if there is no remote_host to connect (both src and dest are local
		)"""
		import time
		import ping3
		def ping_f():
			ping_res = ping3.ping(self.replication.remote_host)
			logger.debug(f"check_connection_via_ICMP: ping_f: ping_res is {ping_res}")
			return ping_res
		if self.replication.remote_host is None:
			logger.info(f"check_connection_via_ICMP: skipping connection because both src {self.replication.src} and dest {self.replication.dest} are local.")
			return None
		logger.debug(f"check_connection_via_ICMP: will check connection to {self.replication.remote_host}")
		retries_left = self.replication.retries
		ping = ping_f()
		while (ping is False or ping is None) and retries_left > 0:
			logger.info(f"check_connection_via_ICMP: host {self.replication.remote_host} unreachable by ICMP, retrying ({retries_left} left)...")
			time.sleep(self.RETRY_DELAY_S)
			ping = ping_f()
			retries_left -= 1
		if ping is not False and ping is not None:
			# OK host is reachable
			logger.info(f"check_connection_via_ICMP: host {self.replication.remote_host} is reachable, retries left: {retries_left}")
			return True
		if ping is False or ping is None:
			if retries_left == 0:
				logger.error(f"check_connection_via_ICMP: host {self.replication.remote_host} unreachable and no retries left.")
				return False
		if ping is True:
			return True
	
	
	def mark_start(self):
		self.start = timezone.now()
		self.running = True
		self.save()
	
	
	def mark_end(self):
		self.end = timezone.now()
		self.running = False
		self.complete = True
		self.save()
		
	
	def check_src(self):
		pass
	
	
	def check_dest(self):
		pass
	
	
	def check_options(self):
		pass
	
	
	def returncode_is_ok(self, returncode):
		if returncode == 0:
			return True
		else:
			return False
	
	
	def run_replication(self):
		logger.debug(f"run_replication: starting task for replication {self.replication}")
		rsync_cmd = self.replication.resulting_cmd
		self.mark_start()
		if not self.dry_run:
			try:
				logger.debug(f"run_replication: will run cmd: {rsync_cmd}")
				self.cmd_output_text, returncode = run_command_with_returncode(rsync_cmd)
				logger.debug(f"run_replication: cmd executed. returncode is {returncode}")
				if self.returncode_is_ok(returncode):
					self.OK = True
					logger.info(f"run_replication: replication is complete, OK")
				else:
					self.OK = False
					self.error = True
					self.add_error_text(f"Got non-zero returncode {returncode}" + "\n")
					logger.info(f"run_replication: replication is complete, NOT OK")
			except Exception as e:
				self.error = True
				self.error_text = str(e)
				logger.error(f"run_replication: got error {e}, traceback: {traceback.format_exc()}")
			self.mark_end()
			self.save()
		else:
			logger.debug(f"run_replication: should run command: {rsync_cmd}, but DRY_RUN is enabled.")
			pass
		logger.debug(f"run_replication: replication complete, result is: {self.cmd_output_text}")
	
	
	def launch(self):
		self._set_thread(threading.Thread(target = self.run))
		self._thread.start()
		logger.info(f"launch: subthread launced for task{self}")
	
	
	@property		
	def state(self):
		if self.start is not None and self.running:
			if not self.error:
				return "running"
			else:
				return "running, error"
		if self.start is None and not self.running:
			return "pending"
		if not self.running and self.complete and (self.start is not None) and (self.end is not None):
			if not self.error:
				return "complete, OK"
			else:
				return "complete, FAIL"
		return "UNKNOWN"
	
	
	def add_error_text(self, text):
		if self.error_text is None:
			self.error_text = text + "\n"
		else:
			self.error_text += text + "\n"
	
	
	def run(self):
		logger.debug("run: starting replication")
		self.mark_start()
		reachable = self.check_connection_via_ICMP()
		if self.replication.remote_host is None:
			logger.info(f"run: running local replication")
			self.run_replication()
		else:
			if reachable is not False and reachable is not None:
				logger.info(f"run: running remote replication")
				self.run_replication()
			else:
				logger.error(f"run: replication is remote, but could not reach {self.replication.remote_host}, will not replicate")
				self.error = True
				self.add_error_text(f"Replication is remote, but could not reach {self.replication.remote_host}, will not replicate")
		self.mark_end()





