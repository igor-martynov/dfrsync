
from django.urls import path

from . import views


app_name = "replicator"


urlpatterns = [
	path("", views.IndexView.as_view(), name = "index"),
	path("add_replication", views.ReplicationAddView.as_view(), name = "add_replication"),
	path("delete_replication/<int:replication_id>", views.delete_replication, name = "delete_replication"),
	path("<int:pk>/", views.ReplicationDetailView.as_view(), name = "replication_detail"),
	path("scheduler/", views.scheduler, name = "scheduler"),
	path("replication_task_runner/", views.replication_task_runner, name = "replication_task_runner"),
	path("replication_task_runner/run_replication_task/<int:replication_id>", views.run_replication_task, name = "run_replication_task"),
	# path("replication_task_runner/cancell_replication_task/<int:task_id>", views.cancel_replication_task, name = "cancel_replication_task"),
	path("replication_task_runner/<int:pk>", views.ReplicationTaskDetailView.as_view(), name = "replication_task_detail"),
	path("scheduler/<int:pk>", views.ReplicationScheduleDetailView.as_view(), name = "schedule_detail"),
	path("scheduler/add_schedule", views.ReplicationScheduleAddView.as_view(), name = "add_schedule"),
	path("scheduler/edit_schedule/<int:pk>", views.ReplicationScheduleEditView.as_view(), name = "edit_schedule"),
	path("scheduler/enable_schedule/<int:schedule_id>", views.enable_replication_schedule, name = "enable_schedule"),
	path("scheduler/disable_schedule/<int:schedule_id>", views.disable_replication_schedule, name = "disable_schedule"),
	path("scheduler/delete_schedule/<int:pk>", views.ReplicationScheduleDeleteView.as_view(), name = "delete_schedule"),
	path("show_log", views.show_log, name = "show_log"),
]

