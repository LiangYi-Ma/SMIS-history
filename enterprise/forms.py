from django import forms  # 注意是django下的forms
from .models import EnterpriseInfo


class EnterpriseInfoForm(forms.ModelForm):
    class Meta:
        model = EnterpriseInfo
        fields = ["tags"]
