from bpmappers.djangomodel import ModelMapper
from bpmappers import Mapper, RawField
from user.models import User, PersonalInfo, JobExperience, TrainingExperience, \
    EducationExperience, Evaluation
from cv.models import CV, Industry, CV_PositionClass
from enterprise.models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, PositionClass, \
    TaggedWhatever, SettingChineseTag


class NumberOfStaffMapper(ModelMapper):
    class Meta:
        model = NumberOfStaff


class TaggedWhateverMapper(ModelMapper):
    class Meta:
        model = TaggedWhatever


class SettingChineseTagMapper(ModelMapper):
    class Meta:
        model = SettingChineseTag


class EnterpriseInfoMapper(ModelMapper):
    class Meta:
        model = EnterpriseInfo


class ApplicationsMapper(ModelMapper):
    is_working_years_match = RawField("is_workingYears_match")
    is_edu_match = RawField("is_edu_match")
    is_jobExp_match = RawField("is_jobExp_match")
    is_salary_match = RawField("is_salary_match")
    candidate_age = RawField("candidate_age")
    candidate_education_level = RawField("candidate_education_level")
    class Meta:
        model = Applications


class PositionMapper(ModelMapper):
    is_posting = RawField("is_posting")
    class Meta:
        model = Position


class RecruitmentMapper(ModelMapper):
    class Meta:
        model = Recruitment


class FieldMapper(ModelMapper):
    class Meta:
        model = Field


class EvaMapper(ModelMapper):
    class Meta:
        model = Evaluation


class CvMapper(ModelMapper):
    education_level = RawField("education_level")
    age = RawField("age")
    image = RawField("image")
    get_intention = RawField("get_intention")
    class Meta:
        model = CV


from django.contrib.auth.models import User
class UserMapper(ModelMapper):
    class Meta:
        model = User
        exclude = 'password'


class PersonalInfoMapper(ModelMapper):
    class Meta:
        model = PersonalInfo


class PositionClassMapper(ModelMapper):
    parent_id = RawField('parent_id')

    class Meta:
        model = PositionClass


class JobExMapper(ModelMapper):
    class Meta:
        model = JobExperience


class EduExMapper(ModelMapper):
    class Meta:
        model = EducationExperience


class TraExMapper(ModelMapper):
    class Meta:
        model = TrainingExperience

