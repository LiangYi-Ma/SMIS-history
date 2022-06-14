from rest_framework import serializers


# 简历id校验
class CvIdSerializers(serializers.Serializer):
    cv_id = serializers.IntegerField(required=True, help_text="简历id")
