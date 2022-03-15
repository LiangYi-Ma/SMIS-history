from django.contrib import admin
from .models import PersonalInfo, EducationExperience, JobExperience, TrainingExperience, Evaluation, WxUserPhoneValidation
from django.contrib.auth.models import User

# Register your models here


class EduExpInLine(admin.TabularInline):
    model = EducationExperience
    extra = 1


class JobExpInLine(admin.TabularInline):
    model = JobExperience
    extra = 1


class TraExpInLine(admin.TabularInline):
    model = TrainingExperience
    extra = 1


class EvaluationInLine(admin.StackedInline):
    model = Evaluation


# class UserAdmin(admin.ModelAdmin):
#
#     inlines = [PersonalInfoAdmin, EduExpInLine, JobExpInLine, TraExpInLine, EvaluationInLine]
#     list_display = ('user_name_display',
#                     'user_class',
#                     'was_registered_within_30ds',
#                     )
#     list_filter = ['register_date', 'user_class']
#     date_hierarchy = 'register_date'


class DegreeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'degree_class',
        'degree_level',
    )
    list_filter = ['degree_class', 'degree_level']


class EducationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'education',
    )


class MartialStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'martial_status',
    )


class UserClassAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'class_name',
        'class_meaning',
    )


class PersonalInfoAdmin(admin.ModelAdmin):
    inlines = [EduExpInLine, JobExpInLine, TraExpInLine, EvaluationInLine]

    list_display = (
        'id',
        'name',
    )


class EvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'teacher_evaluation',
    )
# admin.site.register(User, UserAdmin)


class WxUserPhoneValidationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "valid_code",
        "is_expired",
        "valid_datetime",
    )


admin.site.register(PersonalInfo, PersonalInfoAdmin)
admin.site.register(EducationExperience)
admin.site.register(JobExperience)
admin.site.register(TrainingExperience)
admin.site.register(Evaluation, EvaluationAdmin)
admin.site.register(WxUserPhoneValidation, WxUserPhoneValidationAdmin)
