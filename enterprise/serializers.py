"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from abc import ABC

from rest_framework import serializers

from SMIS.constants import FINANCING_STATUS_CHOICES, NATURE_CHOICES
from enterprise import models
from cv import models as cv_models
from enterprise.models import NumberOfStaff, Field
from user.models import User


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
