from django import forms  # 注意是django下的forms
from .models import PersonalInfo


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = PersonalInfo
        fields = ["image"]
