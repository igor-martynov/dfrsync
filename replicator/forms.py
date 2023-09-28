
from django import forms

from .models import Replication, ReplicationSchedule, Settings


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
		widgets = {"time": forms.TimeInput(attrs = {"type": "time"}, format = '%H:%M:%S')}



class SettingsForm(forms.ModelForm):
	class Meta:
		model = Settings
		fields = "__all__"




