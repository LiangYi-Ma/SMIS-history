"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from rest_framework import serializers
from enterprise import models


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
