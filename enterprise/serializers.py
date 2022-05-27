"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from rest_framework import serializers
from enterprise import models
from cv import models as cv_models
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
