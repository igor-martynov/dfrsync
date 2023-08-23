
from django import forms

from .models import Replication, ReplicationSchedule


class ReplicationForm(forms.ModelForm):
	
	class Meta:
		model = Replication
		fields = "__all__"



class ReplicationScheduleForm(forms.ModelForm):
	name = forms.CharField(label = "name", max_length = 128) #, widget = forms.TextInput)
	replication = forms.ModelChoiceField(label = "replication", queryset = Replication.objects.all().order_by("name"))
	

	class Meta:
		model = ReplicationSchedule
		fields = "__all__"

