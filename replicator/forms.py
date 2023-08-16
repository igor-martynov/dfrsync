
from django import forms

from .models import Replication, ReplicationSchedule
# forms here


class ReplicationScheduleForm(forms.ModelForm):
	# model = ReplicationSchedule
	name = forms.CharField(label = "name", max_length = 128) #, widget = forms.TextInput)
	replication = forms.ModelChoiceField(label = "replication", queryset = Replication.objects.all().order_by("name"))
	# hour = forms.IntegerField(widget = forms.NumberInput)
	# minute = forms.IntegerField(widget = forms.NumberInput)
	# second = forms.IntegerField(widget = forms.NumberInput)
	# enabled = forms.


	class Meta:
		model = ReplicationSchedule
		fields = "__all__"

