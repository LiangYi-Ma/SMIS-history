from django.contrib import admin
from .models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, PositionClass
# Register your models here.
from django import forms


class EnterpriseModelForm(forms.ModelForm):
    introduction = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = EnterpriseInfo
        fields = "__all__"


class PositionModelForm(forms.ModelForm):
    job_content = forms.CharField(widget=forms.Textarea)
    requirement = forms.CharField(widget=forms.Textarea)
    extra_info = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Position
        fields = "__all__"


class PositionInLine(admin.TabularInline):
    model = Position
    extra = 1


class NumberOfStaffAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "min_number",
        "max_number",
    )


class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "enterprise",
        "name",
    )


class PositionClassAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_root",
        "name",
        "parent",
    )


class FieldAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_root",
        "name",
        "parent",
    )


class EnterpriseInfoAdmin(admin.ModelAdmin):
    inlines = [PositionInLine]
    form = EnterpriseModelForm
    list_display = (
        "id",
        "name",
        "field",
        "nature",
    )
    list_filter = ['field', 'nature', 'staff_size', 'tags', 'financing_status', 'establish_year']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u",".join(o.name for o in obj.tags.all())


class RecruitmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enterprise',
        'position',
    )


class ApplicationsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cv',
        'recruitment',
    )


admin.site.register(Field, FieldAdmin)
admin.site.register(PositionClass, PositionClassAdmin)
admin.site.register(NumberOfStaff, NumberOfStaffAdmin)
admin.site.register(EnterpriseInfo, EnterpriseInfoAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Recruitment, RecruitmentAdmin)
admin.site.register(Applications, ApplicationsAdmin)
