from django.db import models
from django.urls import reverse
from django.utils import timezone
# import datetime
import logging
import traceback
import threading


logger = logging.getLogger(__name__)

from .base_functions import run_command

# Create your models here.


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
	pass


	def __str__(self):
		return f"Replication {self.name}"

	
	def get_absolute_url(self):
		rev_tmp = reverse("replicator:replication_detail", args = (self.id,))
		# logger.debug(f"get_absolute_url: will_return: {rev_tmp}")
		# return reverse("replicator:replication_detail", args = (self.object.id,))
		return rev_tmp
	
	
	def parse_src_dest(self):
		"""here we parse source and dest"""
		src_is_local = self.src.startswith("/")
		dest_is_local = self.dest.startswith("/")
		if src_is_local and not dest_is_local:
			self._type = "local_to_remote"
		elif src_is_local and dest_is_local:
			self._type = "local_to_local"
		elif not src_is_local and dest_is_local:
			self._type = "remote_to_local"
		elif not src_is_local and not dest_is_local:
			# self._logger.error("parse_src_dest: remote to remote replication is not supported!")
			print("remote to remote replication is not supported!")
			sys.exit(1)
		
		# set remote_host 
		
		pass
		
	
	def check_connection_via_ICMP(self):
		def ping_f():
			return ping3.ping(self.remote_host)
		retries_left = self.retries
		ping = ping_f()
		while ping is None and retries_left > 0:
			# self._logger.info(f"check_connection: host {self.remote_host} unreachable by ICMP, retrying ({retries_left} left)...")
			time.sleep(self.RETRY_DELAY_S)
			ping = ping_f()
			retries_left -= 1
		if ping is not None:
			# OK host is reachable
			# self._logger.info(f"check_connection: host {self.remote_host} is reachable, retries left: {retries_left}")
			return True
		if ping is None:
			if retries_left == 0:
				# self._logger.error(f"check_connection: host {self.remote_host} unreachable and no retries left.")
				return False
	
	
	@property
	def resulting_cmd(self):
		return f"{self.RSYNC_BIN} {self.options} {self.src} {self.dest}"






class ReplicationSchedule(models.Model):
	"""one row of Replication schedule
	
	should be supported:
	everyday at hh:mm:ss
	every monday at hh:mm:ss
	every 10th day of month
	
	
	
	"""
	
	name = models.CharField(max_length = 128, unique = True, blank = True, null = True)
	replication = models.ForeignKey(Replication, on_delete = models.CASCADE)
	hour = models.IntegerField(default = None, blank = True, null = True)
	minute = models.IntegerField(default = None, blank = True, null = True)
	second = models.IntegerField(default = None, blank = True, null = True)
	dom = models.IntegerField(default = None, blank = True, null = True)
	month = models.IntegerField(default = None, blank = True, null = True)
	year = models.IntegerField(default = None, blank = True, null = True)
	dow = models.IntegerField(default = None, blank = True, null = True)
	enabled = models.BooleanField(default = True)
	pass
	
	
	def get_absolute_url(self):
		rev_tmp = reverse("replicator:schedule_detail", args = (self.pk,))
	
	
	@property
	def is_hourly(self):
		if self.hour is None and self.minute is not None and not self.is_daily and not self.is_weekly and not self.is_monthly:
			return True
		return False
	
	
	@property
	def is_daily(self):
		if self.hour is not None and self.dom is None and self.month is None and self.year is None and self.dow is None:
			return True
		return False
	
	
	@property
	def is_weekly(self):
		if self.dow is not None and self.dom is None and not self.is_hourly and not self.is_daily:
			return True
		return False
	
	
	@property
	def is_monthly(self):
		if self.dom is not None and self.dow is None and not self.is_hourly and not self.is_daily:
			return True
		return False	
	
	
	@property
	def is_one_time_in_future(self):
		if self.year is not None and self.month is not None and not self.is_monthly:
			return True
		return False
		
	
	@property
	def hr_schedule(self):
		if self.is_hourly:
			return f"hourly, at "
		elif self.is_daily:
			return f"dayly, at "
		elif self.is_weekly:
			return f"weekly, at "
		elif self.is_monthly:
			return f"monthly, at "
		elif self.is_one_time_in_future:
			return f"one time in future, at"
		else:
			return "UNKNOWN"
	
	
	@property
	def related_tasks(self):
		related_tasks = ReplicationTask.objects.all().filter(schedule = self)
		logger.debug(f"related_tasks: loaded {len(related_tasks)} related tasks")
		return related_tasks
		pass
	
	
	def load_schedule_object(self):
		import schedule
		from .base import ReplicationTaskRunner
		
		if self.is_daily:
			if self.second is None:
				date_str = f"{self.hour:02}:{self.minute:02}:00"
			else:
				date_str = f"{self.hour:02}:{self.minute:02}:{self.second:02}"
			self.job = schedule.every().day.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.is_hourly:
			if self.second is None:
				date_str = f"{self.minute:02}:00"
			else:
				date_str = f"{self.minute:02}:{self.second:02}"
			self.job = schedule.every().hour.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
		elif self.is_weekly:
			if self.second is None:
				date_str = f"{self.hour:02}:{self.minute:02}:00"
			else:
				date_str = f"{self.hour:02}:{self.minute:02}:{self.second:02}"
			match self.dow:
				case 0:
					self.job = schedule.every().sunday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 7:
					self.job = schedule.every().sunday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 1:
					self.job = schedule.every().monday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 2:
					self.job = schedule.every().tuesday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 3:
					self.job = schedule.every().wednesday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 4:
					self.job = schedule.every().thursday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 5:
					self.job = schedule.every().friday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
				case 6:
					self.job = schedule.every().saturday.at(date_str).do(ReplicationTaskRunner.add_task_for_replication, self.replication, schedule = self)
					
			
		
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
	
	pass
	
	
	def _set_thread(self, _thread):
		self._thread = _thread
	
		
	def _get_thread(self):
		return self._thread
	
	
	thread = property(_get_thread, _set_thread)
		
	
	def __str__(self):
		return f"ReplicationTask {self.id} for replica {self.replication}"
		
		
	def mark_start(self):
		self.start = timezone.now()
		self.running = True
	
	
	def mark_end(self):
		self.end = timezone.now()
		self.running = False
		self.complete = True
	
	
	def check_src(self):
		pass
	
	
	def check_dest(self):
		pass
	
	
	def check_options(self):
		pass
	
	
	def run_replication(self):
		logger.debug(f"run_replication: starting task for replication {self.replication}")
		rsync_cmd = self.replication.resulting_cmd
		self.mark_start()
		if not self.dry_run:
			try:
				logger.debug(f"run_replication: will run cmd: {rsync_cmd}")
				self.cmd_output_text = run_command(rsync_cmd)
				self.OK = True
				logger.debug(f"run_replication: replication complete - cmd executed")
			except Exception as e:
				self.error = True
				self.error_text = str(e)
				logger.error(f"run_replication: got error {e}, traceback: {traceback.format_exc()}")
			self.complete = True
			self.mark_end()
			self.save()
		else:
			logger.debug(f"run_replication: should run command: {rsync_cmd}, but DRY_RUN is enabled.")
			pass
		logger.debug(f"run_replication: replication complete, result is: {self.cmd_output_text}")
	
	
	def launch(self):
		self._set_thread(threading.Thread(target = self.run_replication))
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
	
	
	def run(self):
		logger.debug("run: starting replication")
		self.mark_start()
		
		
		self.check_connection_via_ICMP()
		
		
		self.mark_end()
		pass





