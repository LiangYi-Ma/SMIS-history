# author: Mr. Ma
# datetime :2022/7/28
from pip._internal.cli.cmdoptions import help_
from rest_framework import serializers

from SMIS.constants import LOCAL
from utils import models


class SensitiveWordReplaceSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, help_text='检测文本')
    replace_type = serializers.CharField(required=False, help_text='敏感词替换字符')


class OnlineStatusSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, help_text='用户id')


class CommonWordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CommonWords
        fields = '__all__'


class CommonWordsDeleteSerializer(serializers.Serializer):
    id = serializers.CharField(source=models.CommonWords, required=True, help_text="常用语id")


class CommonWordsPostSerializer(serializers.Serializer):
    word = serializers.CharField(max_length=200, required=True, help_text="常用语")


class CommonWordsPutSerializer(serializers.Serializer):
    id = serializers.CharField(source=models.CommonWords, required=True, help_text="常用语id")
    word = serializers.CharField(required=False, help_text="常用语")
    local = serializers.ChoiceField(required=False, help_text="前移/后移", choices=LOCAL)
