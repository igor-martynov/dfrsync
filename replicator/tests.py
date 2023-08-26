from django.test import TestCase
from .models import Replication, ReplicationTask, ReplicationSchedule

# Create your tests here.



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







