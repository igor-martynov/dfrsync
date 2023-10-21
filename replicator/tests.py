from django.test import TestCase
from .models import Replication, ReplicationTask, ReplicationSchedule



class ReplicationModelTests(TestCase):
	
	def test_remote_host_simple_hostname(self):
		test_replication = Replication(src = "root@hostname1:/tmp", dest = "/tmp2")
		self.assertEqual(test_replication.remote_host, "hostname1")
	

	def test_remote_host_standard_hostname(self):
		test_replication = Replication(src = "root@hostname.example.com:/tmp/2", dest = "/tmp2")
		self.assertEqual(test_replication.remote_host, "hostname.example.com")

	
	def test_remote_host_standard_hostname_without_user(self):
		test_replication = Replication(src = "hostname.example.com:/tmp3", dest = "/tmp2")
		self.assertEqual(test_replication.remote_host, "hostname.example.com")
	
	
	def test_remote_host_standard_no_host_so_local_only(self):
		test_replication = Replication(src = "/tmp/1", dest = "/tmp2")
		self.assertIs(test_replication.remote_host, None)

	
	def test_resulting_cmd_local_easy(self):
		test_replication = Replication(src = "/tmp/1/", dest = "/tmp2/", options = "-axv --delete")
		self.assertEqual(test_replication.resulting_cmd, "rsync -axv --delete /tmp/1/ /tmp2/")
	
	
	def test_resulting_cmd_remote_easy(self):
		test_replication = Replication(src = "/tmp/1/", dest = "username-1@hostname1.example:/tmp2/", options = "-axv --delete")
		self.assertEqual(test_replication.resulting_cmd, "rsync -axv --delete /tmp/1/ username-1@hostname1.example:/tmp2/")



class ReplicationScheduleModelTests(TestCase):
	
	def test_is_hourly_simple(self):
		import datetime
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rs = ReplicationSchedule(replication = test_r,
			time = datetime.time(hour = 1,minute = 10, second = 10),
			hourly = True,
			dom = 10)
		self.assertEqual(test_rs.is_hourly, True)
	
	
	def test_is_daily_simple(self):
		import datetime
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rs = ReplicationSchedule(replication = test_r,
			time = datetime.time(hour = 1,minute = 10, second = 10),
			hourly = False)
		self.assertEqual(test_rs.is_daily, True)
	
	
	def test_is_daily_simple_not(self):
		import datetime
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rs = ReplicationSchedule(replication = test_r,
			time = datetime.time(hour = 1,minute = 10, second = 10),
			hourly = False,
			dom = 10)
		self.assertEqual(test_rs.is_daily, False)

	
	def test_time_properties(self):
		import datetime
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rs = ReplicationSchedule(replication = test_r,
			time = datetime.time(hour = 1,minute = 2, second = 3),
			hourly = False)
		
		self.assertEqual(test_rs.hour, 1)
		self.assertEqual(test_rs.minute, 2)
		self.assertEqual(test_rs.second, 3)



class ReplicationTaskModelTest(TestCase):
	def test_returncode_is_ok(self):
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rt = ReplicationTask(replication = test_r, returncode = 0)
		self.assertIs(test_rt.returncode_is_ok, True)
	
	
	def test_returncode_is_not_ok(self):
		test_r = Replication(src = "/tmp/", dest = "/temp2/")
		test_rt = ReplicationTask(replication = test_r, returncode = 10)
		self.assertIs(test_rt.returncode_is_ok, False)
	

	def test_check_connection_via_ICMP_ok(self):
		test_r = Replication(src = "root@localhost:/tmp/", dest = "/temp2/")
		test_rt = ReplicationTask(replication = test_r)
		self.assertEqual(test_rt.check_connection_via_ICMP(), True)
	
	
	def test_check_connection_via_ICMP_not_ok(self):
		test_r = Replication(src = "root@localhost123123:/tmp/", dest = "/temp2/")
		test_rt = ReplicationTask(replication = test_r)
		self.assertEqual(test_rt.check_connection_via_ICMP(), False)
	
	
	def test_simple_replication_overall(self):
		from .base_functions import run_command
		import random
		import string
		import os
		try:
			src_test_dir = "/tmp/srctestdir_" + "".join(random.choices(string.ascii_lowercase, k = 8))
			dest_test_dir = "/tmp/desttestdir_" + "".join(random.choices(string.ascii_lowercase, k = 8))
			run_command(f"mkdir {src_test_dir}")
			run_command(f"mkdir {dest_test_dir}")
			run_command(f"touch " + os.path.join(src_test_dir, "file1"))
			run_command(f"touch " + os.path.join(src_test_dir, "file2"))
			run_command(f"touch " + os.path.join(src_test_dir, "file3"))
		except Exception as e:
			self.fail(f"ERROR: could not create test dir and files! error is: {e}")
		test_r = Replication(src = src_test_dir + "/", dest = dest_test_dir + "/")
		test_rt = ReplicationTask(replication = test_r)
		test_rt.run()
		try:
			run_command(f"rm -rf {src_test_dir}")
			run_command(f"rm -rf {dest_test_dir}")
		except Exception as e:
			self.fail(f"ERROR: could not dele test dirs")
		self.assertEqual(test_rt.returncode, 0)

	


