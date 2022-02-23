from django import forms
from main.models import Uploadfolder


class Uploadfileform(forms.ModelForm):
	class Meta:
		model=Uploadfolder
		fields=('File_to_upload',)