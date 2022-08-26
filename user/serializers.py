"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PrivacySetting


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class PrivacySettingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacySetting
        fields = "__all__"


class PrivacySettingUpdateSerializer(serializers.Serializer):
    phone_hidden = serializers.BooleanField(required=False, label='联系电话隐私设置')
    name_hidden = serializers.BooleanField(required=False, label='姓名隐私设置')
    email_hidden = serializers.BooleanField(required=False, label='邮件隐私设置')


class SendEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label="邮箱")
    code = serializers.IntegerField(required=True, label="验证码")


class SendEmailPostSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label="邮箱")


class NumberSerializer(serializers.Serializer):
    mobile = serializers.IntegerField(required=True, label="联系电话")


class NumberGetSerializer(serializers.Serializer):
    mobile = serializers.IntegerField(required=True, label="联系电话")
    code = serializers.IntegerField(required=True, label="验证码")


class WxSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, label="微信code")


class BindNumberSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, label="微信code")
    mobile = serializers.IntegerField(required=True, label="联系电话")
