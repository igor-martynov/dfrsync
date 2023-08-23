from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views import generic
from django.urls import reverse

import logging


from .models import Replication, ReplicationSchedule, ReplicationTask
from .base import ReplicationTaskRunner
from .forms import ReplicationForm, ReplicationScheduleForm


logger = logging.getLogger(__name__)



class IndexView(generic.ListView):
	template_name = "replicator/index.html"
	
	
	def get_queryset(self):
		return Replication.objects.all()



class ReplicationDetailView(generic.edit.UpdateView):
	model = Replication
	template_name = "replicator/replication_detail.html"
	form_class = ReplicationForm
	
	
	def get_success_url(self):
		return reverse("replicator:replication_detail", args = (self.object.id,))
	
	
	
class ReplicationAddView(generic.edit.CreateView):
	model = Replication
	template_name = "replicator/replication_add.html"
	form_class = ReplicationForm


	def get_success_url(self):
		return reverse("replicator:index")



# TODO: rewrite this as class-based View
def delete_replication(request, replication_id):
	replication = get_object_or_404(Replication, pk = replication_id)
	context = {"replication": replication}
	if request.method == "POST":
		replication.delete()
		logger.debug(f"delete_replication: replication {replication} deleted")
		context = {"message": f"object deleted: {replication}"}
		return render(request, "replicator/blank_page.html", context = context)
	context["message"] = f"really delete replication {replication}?"
	return render(request, "replicator/blank_page_with_button.html", context = context)


def replication_task_runner(request):
	all_replications = Replication.objects.filter(enabled = True)
	context = {"all_replications": all_replications, "running_tasks": ReplicationTaskRunner.running_tasks}
	return render(request, "replicator/replication_task_runner.html", context = context)


def run_replication_task(request, replication_id):
	replication = get_object_or_404(Replication, pk = replication_id)
	logger.debug(f"run_replication_task: will add task for replication {replication.name}")
	ReplicationTaskRunner.start_loop_subthread()
	ReplicationTaskRunner.add_task_for_replication(replication)
	return HttpResponseRedirect(reverse("replicator:replication_task_runner"))


def cancel_replication_task(request, task_id):
	task = get_object_or_404(ReplicationTask, pk = task_id)
	logger.debug(f"cancel_replication_task: requested cancel of replication task: {task}")
	ReplicationTaskRunner.cancel_replication_task(task)
	return HttpResponseRedirect(reverse("replicator:replication_task_runner"))



class ReplicationTaskDetailView(generic.detail.DetailView):
	model = ReplicationTask
	template_name = "replicator/replication_task_detail.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		return context



def scheduler(request):
	context = {"schedules": ReplicationSchedule.objects.all(), }
	return render(request, "replicator/scheduler.html", context = context)



class ReplicationScheduleAddView(generic.edit.CreateView):
	model = ReplicationSchedule
	form_class = ReplicationScheduleForm
	

	def get_success_url(self):
		return reverse("replicator:scheduler")


class ReplicationScheduleDetailView(generic.detail.DetailView):
	model = ReplicationSchedule
	form_class = ReplicationScheduleForm
	template_name = "replicator/replication_schedule_detail.html"
	
	
	def get_success_url(self):
		return reverse("replicator:scheduler")



class ReplicationScheduleEditView(generic.edit.UpdateView):
	model = ReplicationSchedule
	form_class = ReplicationScheduleForm
	template_name = "replicator/replicationschedule_form.html"
	
	
	def get_success_url(self):
		return reverse("replicator:scheduler")



class ReplicationScheduleDeleteView(generic.edit.DeleteView):
	model = ReplicationSchedule
	
	
	def get_success_url(self):
		return reverse("replicator:scheduler")
	

def enable_replication_schedule(request, schedule_id):
	schedule = get_object_or_404(ReplicationSchedule, pk = schedule_id)
	schedule.enabled = True
	schedule.save()
	logger.info(f"enable_replication_schedule: schedule {schedule} enabled")
	return HttpResponseRedirect(reverse("replicator:scheduler"))
	

def disable_replication_schedule(request, schedule_id):
	schedule = get_object_or_404(ReplicationSchedule, pk = schedule_id)
	schedule.enabled = False
	schedule.save()
	logger.info(f"disable_replication_schedule: schedule {schedule} disabled")
	return HttpResponseRedirect(reverse("replicator:scheduler"))






