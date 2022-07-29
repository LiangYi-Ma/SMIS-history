# author: Mr. Ma
# datetime :2022/7/28

from rest_framework import serializers


class SensitiveWordReplaceSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, help_text='检测文本')
    replace_type = serializers.CharField(required=False, help_text='敏感词替换字符')


class SensitiveWordSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, help_text='检测文本')
