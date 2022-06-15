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
    phone_hidden = serializers.BooleanField(required=False, label='联系电话隐私设置', allow_null=True)
    name_hidden = serializers.BooleanField(required=False, label='姓名隐私设置')
    email_hidden = serializers.BooleanField(required=False, label='邮件隐私设置')
