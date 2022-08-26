"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from abc import ABC

from django.db.models import Max
from openpyxl.workbook import child
from pip._internal.cli.cmdoptions import help_
from rest_framework import serializers
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from SMIS.constants import FINANCING_STATUS_CHOICES, NATURE_CHOICES, POSITIONNEW_STATUS, PROVINCES_CHOICES
from cv.models import CV_PositionClass
from enterprise import models
from cv import models as cv_models
from enterprise.models import NumberOfStaff, Field, PositionClass, PositionNew, PositionPost
from enterprise.utils.serializer_utile_queryset import UserUtile, PersonalInfoUtile, CVPositionClassUtile
from user.models import User, PersonalInfo, JobExperience, EducationExperience


class PositionClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PositionClass
        fields = ("id", "name")


class PositionListSerializer(serializers.ModelSerializer):
    """序列化外键值的方法：
    在序列化器中制作新的参数进入fields，
    source参数指向本model中的【外键命名.外键表中的值命名】"""
    position_name = serializers.CharField(source="pst_class.name")
    enterprise_name = serializers.CharField(source="enterprise.name")

    class Meta:
        # model模型名
        model = models.Position
        # fields值列表
        fields = ("id", "position_name", "enterprise_name")


class PositionDetailSerializer(PositionListSerializer):
    class Meta:
        model = models.Position
        fields = "__all__"


# 简历筛选
class PersonnelRetrievalForeignSerializer(serializers.ModelSerializer):
    # 外键序列化处理

    class Meta:
        user_id = serializers.CharField(source='User')
        industry = serializers.CharField(source='enterprise.Field')
        fields = ("user_id", "industry")


class PersonnelRetrievalSerializer(PersonnelRetrievalForeignSerializer):
    # 简历筛选
    class Meta:
        model = cv_models.CV
        fields = "__all__"


# 简历筛选前端传入参数校验
class PersonnelRetrievalDataSerializer(serializers.Serializer):
    Search_term = serializers.CharField(required=True, help_text='检索词')
    industry = serializers.CharField(source='enterprise.Field', required=False, help_text='目标行业领域')
    major = serializers.CharField(required=False, help_text='所学专业名称')
    courses = serializers.CharField(required=False, help_text='所修课程')
    english_skill = serializers.IntegerField(required=False, help_text='英语技能水平')
    computer_skill = serializers.IntegerField(required=False, help_text='计算机技能水平')
    expected_salary = serializers.IntegerField(required=False, help_text='最低期望薪资')
    professional_skill = serializers.CharField(required=False, help_text='掌握专业技能')


# 岗位筛选前端传入参数校验
class PositionDataSerializer(serializers.Serializer):
    Search_term = serializers.CharField(required=True, help_text='检索词')
    enterprise = serializers.CharField(source='models.CASCADE', required=False, help_text='企业')
    pst_class = serializers.CharField(source='PositionClass', required=False, help_text='岗位类别')
    fullname = serializers.CharField(required=False, help_text='岗位扩展名称（别称，默认为岗位类别）')
    job_content = serializers.CharField(required=False, help_text='工作内容')
    requirement = serializers.CharField(required=False, help_text='岗位基本要求')


# 收藏列表
class PositionCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PositionCollection
        fields = "__all__"


# 收藏添加和收藏取消前端参数校验
class PositionCollectionAddSerializer(serializers.Serializer):
    position_id = serializers.IntegerField(required=True, help_text="职位id")


class CooperationListSerializer(serializers.ModelSerializer):
    class Meta:
        # user = serializers.CharField(source='get_user_object()')

        model = models.EnterpriseCooperation
        fields = ("user_id", "join_date", "is_superuser", "is_active")


class CooperationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    enterprise_id = serializers.IntegerField(required=True)
    is_active = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    def create(self, validated_data):
        return models.EnterpriseCooperation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.user_id = validated_data.get("user_id", instance.user_id)
        instance.enterprise_id = validated_data.get("enterprise_id", instance.enterprise_id)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.is_superuser = validated_data.get("is_superuser", instance.is_superuser)
        instance.save()
        return instance

    class Meta:
        model = models.EnterpriseCooperation
        fields = "__all__"


class CollectionListSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.JobHuntersCollection
        fields = "__all__"


class CollectionSerializers(CollectionListSerializers):
    user_id = serializers.IntegerField(required=True)
    enterprise_id = serializers.IntegerField(required=True)
    collector = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return models.JobHuntersCollection.objects.create(**validated_data)


class RecruitmentListSerializer(serializers.ModelSerializer):
    class Meta:
        enterprise = serializers.CharField(source="enterprise")
        position = serializers.CharField(source="position")

        model = models.Recruitment
        fields = ("id", "enterprise", "position", "city")


class PositionAdd(serializers.Serializer):
    # 新增职位参数校验
    # 岗位表参数
    enterprise = serializers.CharField(source='EnterpriseInfo.id', required=True, help_text='企业')
    pst_class = serializers.CharField(source='PositionClass.id', required=False, help_text='岗位类别')
    fullname = serializers.CharField(required=False, help_text='岗位扩展名称（别称，默认为岗位类别）')
    job_content = serializers.CharField(required=False, help_text='工作内容')
    requirement = serializers.CharField(required=False, help_text='岗位基本要求')
    extra_info = serializers.CharField(required=False, help_text='补充说明')
    # 职位表参数
    number_of_employers = serializers.IntegerField(required=True, help_text='招聘人数')
    education = serializers.IntegerField(required=True, help_text='最低学历要求')
    city = serializers.IntegerField(required=True, help_text='工作地点')
    salary_min = serializers.IntegerField(required=True, help_text='最低入职工资')
    salary_max = serializers.IntegerField(required=True, help_text='最高入职工资')
    salary_unit = serializers.IntegerField(required=False, help_text='待遇水平单位')
    job_experience = serializers.IntegerField(required=False, help_text='工作经验要求')
    job_nature = serializers.IntegerField(required=False, help_text='工作性质')
    post_limit_time = serializers.DateField(required=True, help_text='发布截止时限')


class PositionUpdate(serializers.Serializer):
    # 修改职位参数校验
    position_id = serializers.IntegerField(required=True, help_text="职位id")
    pst_class = serializers.CharField(source='PositionClass', required=False, help_text='岗位类别')
    fullname = serializers.CharField(required=False, help_text='岗位扩展名称（别称，默认为岗位类别）')
    job_content = serializers.CharField(required=False, help_text='工作内容')
    requirement = serializers.CharField(required=False, help_text='岗位基本要求')
    extra_info = serializers.CharField(required=False, help_text='补充说明')
    # 职位表参数
    number_of_employers = serializers.IntegerField(required=False, help_text='招聘人数')
    education = serializers.IntegerField(required=False, help_text='最低学历要求')
    city = serializers.IntegerField(required=False, help_text='工作地点')
    salary_min = serializers.IntegerField(required=False, help_text='最低入职工资')
    salary_max = serializers.IntegerField(required=False, help_text='最高入职工资')
    salary_unit = serializers.IntegerField(required=False, help_text='待遇水平单位')
    job_experience = serializers.IntegerField(required=False, help_text='工作经验要求')
    job_nature = serializers.IntegerField(required=False, help_text='工作性质')
    post_limit_time = serializers.DateField(required=False, help_text='发布截止时限')


# 职位部分删除和查找
class PositionDataDelete(serializers.Serializer):
    # url参数职位参数校验，主要是为了方便进行是否存在性校验
    position_id = serializers.IntegerField(required=True, help_text="职位id")


# 职位详情专用
class PositionListZySerializer(serializers.ModelSerializer):
    pst_class_name = serializers.CharField(source="pst_class.name")
    enterprise_name = serializers.CharField(source="enterprise.name")

    class Meta:
        # model模型名
        model = models.Position
        # fields值列表
        fields = ("pst_class_name", "enterprise_name")


class PositionDetailZySerializer(PositionListZySerializer):
    class Meta:
        model = models.Position
        fields = "__all__"


# 招聘表序列化器
class RecruitmentSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(source="enterprise.name")

    class Meta:
        model = models.Recruitment
        fields = ("position_name", "enterprise_name")


class RecruitmentDetailSerializer(RecruitmentSerializer):
    class Meta:
        model = models.Recruitment
        fields = "__all__"


# 候选人部分（GET)序列化器
# 管理者hr
class CandidatesGetGlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Applications
        fields = ['cv', 'progress', 'hr']


# 协作hr
class CandidatesGetXzSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Applications
        fields = ['cv', 'progress']


# put部份参数校验
class CandidatesPutSerializer(serializers.Serializer):
    progress = serializers.IntegerField(required=True, help_text="进度code")
    id = serializers.CharField(source='Applications', required=True, help_text="候选人记录id")


# 企业信息部分序列化器
class EnterpriseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnterpriseInfo
        fields = "__all__"


# 企业信息部分用于反序列化器
class EnterpriseInfoCdSerializer(serializers.Serializer):
    id = serializers.CharField(source='User', required=True)
    name = serializers.CharField(required=False, max_length=18, help_text='企业名称')
    field = serializers.CharField(required=False, source='Field', help_text='业务领域')
    staff_size = serializers.CharField(required=False, source='NumberOfStaff', help_text="企业规模（人）")
    address = serializers.CharField(required=False, max_length=50, help_text="公司地址")
    site_url = serializers.URLField(required=False, help_text="企业官网")
    logo = serializers.ImageField(required=False, help_text='企业logo')
    nature = serializers.ChoiceField(required=False, choices=NATURE_CHOICES, help_text='企业性质')
    financing_status = serializers.ChoiceField(required=False, choices=FINANCING_STATUS_CHOICES, help_text="上市/投融资状态")
    establish_year = serializers.IntegerField(required=False, help_text="企业成立年份")
    introduction = serializers.CharField(required=False, max_length=500, help_text="企业基本介绍")


class ApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Applications
        fields = '__all__'


# 删除候选人部分反序列化器
class DeleteApplicationSerializer(serializers.Serializer):
    application_id = serializers.IntegerField(required=True, help_text='候选人投递id')


class CvSerializer(serializers.ModelSerializer):
    class Meta:
        model = cv_models.CV
        fields = '__all__'


class MetroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Metro
        fields = ("line", "title")


# from taggit.serializers import (TagListSerializerField,
#                                 TaggitSerializer)

from SMIS.constants import *


def choice_mate(choice, flag):
    """
    功能： choices元素匹配（参数替换）
    choice：二维元组
    flag：要替换的参数
    """
    # choices元素匹配
    for i in choice:
        if i[0] == flag:
            return i[1]


class JobkeywordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JobKeywords
        fields = '__all__'


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Field
        fields = '__all__'


class PositionNewSerializer(TaggitSerializer, serializers.ModelSerializer):
    """ 职位查询 """
    pst_class_name = serializers.CharField(source="pst_class")
    enterprise_name = serializers.CharField(source="enterprise")
    tag = TagListSerializerField()
    field_name = serializers.SerializerMethodField()

    def get_field_name(self, obj):
        fd = obj.field.all()
        jon = FieldSerializer(instance=fd, many=True)
        return jon.data

    jobkeywords_name = serializers.SerializerMethodField()

    def get_jobkeywords_name(self, obj):
        jkw = obj.jobkeywords.all()
        jon = JobkeywordsSerializer(instance=jkw, many=True)
        return jon.data

    job_nature = serializers.SerializerMethodField()

    def get_job_nature(self, obj):
        return choice_mate(JOB_NATURE_CHOICES, obj.job_nature)

    education = serializers.SerializerMethodField()

    def get_education(self, obj):
        return choice_mate(EDUCATION_LEVELS, obj.education)

    job_experience = serializers.SerializerMethodField()

    def get_job_experience(self, obj):
        return choice_mate(YEAR_CHOICES, obj.job_experience)

    city = serializers.SerializerMethodField()

    def get_city(self, obj):
        return choice_mate(PROVINCES_CHOICES, obj.city)

    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return choice_mate(POSITIONNEW_STATUS, obj.status)

    post_time = serializers.SerializerMethodField()

    def get_post_time(self, obj):
        pp1 = PositionPost.objects.filter(position=obj.id).first()
        if pp1:
            return pp1.post_time
        else:
            return ''

    post_last_days = serializers.SerializerMethodField()

    def get_post_last_days(self, obj):
        pp1 = PositionPost.objects.filter(position=obj.id).first()
        if pp1:
            return pp1.post_last_days
        else:
            return ''

    class Meta:
        model = models.PositionNew
        fields = ["fullname", "job_nature", "job_content", "pst_class_name", "field_name", "education",
                  "job_experience", "jobkeywords_name", "city", "salary_min", "salary_max", "salary_unit",
                  "number_of_employers", "tag", "email", "certificationInfo_id", "status", "enterprise_name",
                  "create_time", "update_time", "like_str", "post_time", "post_last_days"]


class PositionNewMakeSerializer(serializers.Serializer):
    fullname = serializers.CharField(required=True, help_text='岗位名称')
    job_nature = serializers.IntegerField(required=True, help_text='工作性质')
    job_content = serializers.CharField(required=True, help_text='工作内容')
    pst_class = serializers.CharField(source='PositionClass', required=True, help_text='岗位类别')
    field = serializers.ListField(required=True, help_text='行业类型', min_length=1, child=serializers.IntegerField())
    education = serializers.IntegerField(required=True, help_text='最低学历要求')
    job_experience = serializers.IntegerField(required=True, help_text='工作经验要求')
    jobkeywords = serializers.ListField(required=False, help_text='岗位关键词', child=serializers.IntegerField())
    city = serializers.IntegerField(required=True, help_text='工作地点')
    salary_min = serializers.IntegerField(required=True, help_text='最低入职工资')
    salary_max = serializers.IntegerField(required=True, help_text='最高入职工资')
    salary_unit = serializers.IntegerField(required=True, help_text='待遇水平个数')
    tag = serializers.ListField(required=False, help_text='职位福利', child=serializers.IntegerField())
    number_of_employers = serializers.IntegerField(required=True, help_text='招聘人数')
    email = serializers.EmailField(required=True, help_text='简历邮箱')
    certificationInfo_id = serializers.IntegerField(required=False, help_text='资格证书')
    enterprise = serializers.CharField(source='EnterpriseInfo', required=True, help_text='企业')


class PositionNewPutSerializer(serializers.Serializer):
    id = serializers.CharField(source='PositionNew', required=True, help_text='岗位id')
    fullname = serializers.CharField(required=False, help_text='岗位名称')
    job_nature = serializers.IntegerField(required=False, help_text='工作性质')
    job_content = serializers.CharField(required=False, help_text='工作内容')
    pst_class = serializers.CharField(source='PositionClass', required=False, help_text='岗位类别')
    field = serializers.ListField(required=False, help_text='行业类型', min_length=1, child=serializers.IntegerField())
    education = serializers.IntegerField(required=False, help_text='最低学历要求')
    job_experience = serializers.IntegerField(required=False, help_text='工作经验要求')
    jobkeywords = serializers.ListField(required=False, help_text='岗位关键词', child=serializers.IntegerField())
    city = serializers.IntegerField(required=False, help_text='工作地点')
    salary_min = serializers.IntegerField(required=False, help_text='最低入职工资')
    salary_max = serializers.IntegerField(required=False, help_text='最高入职工资')
    salary_unit = serializers.IntegerField(required=False, help_text='待遇水平个数')
    tag = serializers.ListField(required=False, help_text='职位福利', child=serializers.IntegerField())
    number_of_employers = serializers.IntegerField(required=False, help_text='招聘人数')
    email = serializers.EmailField(required=False, help_text='简历邮箱')
    certificationInfo_id = serializers.IntegerField(required=False, help_text='资格证书')


class PositionNewMakeDeleteSerializer(serializers.Serializer):
    id = serializers.CharField(source='PositionNew', required=True, help_text='岗位id')


class PositionNewMakeGetSerializer(serializers.Serializer):
    enterprise_id = serializers.CharField(source='EnterpriseInfo', required=True, help_text='企业id')
    status = serializers.ChoiceField(required=True, help_text='状态', choices=POSITIONNEW_STATUS)
    fullname = serializers.CharField(required=False, help_text='职位名称')
    city = serializers.ChoiceField(required=False, help_text='发布城市', choices=PROVINCES_CHOICES)


class PositionPostPostSerializer(serializers.Serializer):
    id = serializers.CharField(source='PositionNew', required=True, help_text='岗位id')
    times = serializers.IntegerField(required=True, help_text='上线持续时间')


class PositionCollectionListsSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        pp1 = User.objects.filter(id=obj.user_id).values('username').first()
        if pp1:
            return pp1['username']
        else:
            return ''

    age = serializers.SerializerMethodField()

    def get_age(self, obj):
        ages = PersonalInfo.objects.filter(id=obj.user_id)
        if ages.exists():
            if ages.first().date_of_birth != '' or ages.first().date_of_birth != 'null':
                return ages.first().age()
            else:
                return ''
        else:
            PersonalInfo.objects.create(id=User.objects.get(id=obj.user_id))
            return ''

    work_date = serializers.SerializerMethodField()

    def get_work_date(self, obj):
        jes = JobExperience.objects.filter(user_id=obj.user_id)
        if jes.exists():
            je = jes.order_by('-start_date').first()
            return je.work_year_make()
        else:
            return ''

    job_experience = serializers.SerializerMethodField()

    def get_job_experience(self, obj):
        jes = JobExperience.objects.filter(user_id=obj.user_id)

        if jes.exists():
            res = jes.order_by('-start_date').first()
            return f'{res.position.name}  {res.enterprise}'
        else:
            return ''

    eduction = serializers.SerializerMethodField()

    def get_eduction(self, obj):
        ee = EducationExperience.objects.filter(user_id=obj.user_id)
        if ee.exists():
            es = ee.order_by('-end_date').first()
            ed = choice_mate(EDUCATION_LEVELS, es.education)
            res = f'{es.school}  {ed}'
            return res
        else:
            return ''

    class Meta:
        model = models.JobHuntersCollection
        fields = ['id', 'user_name', 'age', 'work_date', 'job_experience', 'eduction', 'join_date']


class PositionCollectionDeleteSerializer(serializers.Serializer):
    id = serializers.CharField(source='JobHuntersCollection', required=True, help_text='收藏人才表id')


class PositionNewCvRetrievalSerializers(serializers.Serializer):
    """ V2.0原型企业端：人才检索"""
    education = serializers.ListField(required=False, help_text='学历要求', min_length=1)
    is_unified_recruit = serializers.BooleanField(required=False, help_text='是否统招')
    age = serializers.ListField(required=False, child=serializers.IntegerField(), min_length=2, max_length=2)
    position_class = serializers.ListField(required=False, help_text='期望岗位', min_length=1)
    work_years = serializers.ListField(required=False, child=serializers.IntegerField(), min_length=2, max_length=2)
    candidate_status = serializers.IntegerField(required=False, help_text="工作状态")
    salary = serializers.ListField(required=False, child=serializers.IntegerField(), min_length=2, max_length=2)
    active = serializers.IntegerField(required=False, help_text="活跃日期")
    sex = serializers.IntegerField(required=False, help_text="性别")
    city = serializers.CharField(required=False, help_text="期望城市")
    search_term = serializers.CharField(required=False, help_text='关键词')


user_data = ''
personinfo_data = ''
CV_PositionClass_data = ''


def utils(user_id, cv_id):
    user_data = UserUtile(user_id)
    personinfo_data = PersonalInfoUtile(user_id)
    CV_PositionClass_data = CVPositionClassUtile(cv_id)


class PositionCollectionReturnSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        try:
            return obj.user_id.username
        except Exception as e:
            return ''

    online_status = serializers.SerializerMethodField()

    def get_online_status(self, obj):
        try:
            pp1 = PersonalInfo.objects.get(id=obj.user_id.id)
            status = pp1.online_status
        except Exception as e:
            pi = PersonalInfo.objects.create(id=obj.user_id)
            pi.online_status = pi.active_time()
            pi.save()
            status = pi.online_status
        return {'id': status, "name": choice_mate(ONLINE_STATUS, status)}

    age = serializers.SerializerMethodField()

    def get_age(self, obj):
        try:
            pp1 = PersonalInfo.objects.get(id=obj.user_id.id)
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        return pp1.age()

    work_date = serializers.SerializerMethodField()

    def get_work_date(self, obj):
        jes = JobExperience.objects.filter(user_id=obj.user_id.id)
        if jes.exists():
            je = jes.order_by('-start_date').first()
            return je.work_year_make()
        else:
            return ''

    education = serializers.SerializerMethodField()

    def get_education(self, obj):
        try:
            pp1 = PersonalInfo.objects.get(id=obj.user_id.id)
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        if pp1.education:
            return {"id": pp1.education, "name": choice_mate(EDUCATION_LEVELS, pp1.education)}
        return {}

    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return {"id": obj.status, "name": choice_mate(CANDIDATE_STATUS, obj.status)}

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        try:
            pp1 = PersonalInfo.objects.get(id=obj.user_id.id)
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        return str(pp1.image)

    position_class_data = serializers.SerializerMethodField()

    def get_position_class_data(self, obj):
        # 根据city，薪资来确定匹配那个意向
        cp = CV_PositionClass.objects.filter(cv_id=obj.id)
        ps_list = []
        if cp.exists():
            for i in cp:
                ps_list.append(i.position_class_id.id)
        else:
            return {
                "position_class": {
                    "id": '',
                    "name": ''
                },
                "city": {
                    'id': '',
                    "name": ''
                },
                "salary": []
            }
        context_list = self.context.get("position_class")
        if context_list != '':
            cou = set(ps_list).intersection(set(context_list))
            cps = cp.filter(position_class_id__id=list(cou)[0]).first()
        else:
            cps = cp.filter(id=ps_list[0]).first()
        return {
            "position_class": {
                "id": cps.position_class_id.id,
                "name": cps.position_class_id.name
            },
            "city": {
                'id': cps.city.id,
                "name": cps.city.second
            },
            "salary": [cps.salary_min, cps.salary_max]
        }

    job_keywords = serializers.SerializerMethodField()

    def get_job_keywords(self, obj):
        try:
            PersonalInfo.objects.filter(id=obj.user_id.id).exists()
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        jobkeywords_data = []
        keys_list = []
        jes = JobExperience.objects.filter(user_id=obj.user_id.id)
        if jes.exists():
            for i in jes:
                jws = i.jobkeywords.all()
                for j in jws:
                    if j.id not in keys_list:
                        jobkeywords_data.append(
                            {
                                "id": j.id,
                                "name": j.name
                            }
                        )
                        keys_list.append(j.id)
        return jobkeywords_data

    job_experience = serializers.SerializerMethodField()

    def get_job_experience(self, obj):
        try:
            PersonalInfo.objects.filter(id=obj.user_id.id).exists()
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        jobexperience_data = []
        try:
            jes = JobExperience.objects.filter(user_id=obj.user_id.id)
            if jes.exists():
                for j in jes:
                    jobexperience_data.append(
                        {
                            "enterprise": j.enterprise,
                            "position": j.position.name,
                            "start_date": j.start_date,
                            "end_date": j.end_date
                        }
                    )
            return jobexperience_data
        except Exception as e:
            raise e

    education_experience = serializers.SerializerMethodField()

    def get_education_experience(self, obj):
        try:
            PersonalInfo.objects.filter(id=obj.user_id.id).exists()
        except Exception as e:
            pp1 = PersonalInfo.objects.create(id=obj.user_id)
            pp1.online_status = pp1.active_time()
            pp1.save()
        education_data = []
        try:
            jes = EducationExperience.objects.filter(user_id=obj.user_id.id)
            if jes.exists():
                for j in jes:
                    education_data.append(
                        {
                            "school": j.school,
                            "major": j.major,
                            "start_date": j.start_date,
                            "end_date": j.end_date
                        }
                    )
            return education_data
        except Exception as e:
            raise e

    class Meta:
        model = models.JobHuntersCollection
        fields = ['user_name', 'online_status', 'age', 'work_date', 'education', 'status', 'image',
                  "position_class_data", "job_keywords", "job_experience", "education_experience"]



