from rest_framework import serializers


# 简历id校验
class CvIdSerializers(serializers.Serializer):
    cv_id = serializers.IntegerField(required=True, help_text="简历id")


# 简历投递反序列化器
class DeliverCvSerializers(serializers.Serializer):
    recruitment_id = serializers.IntegerField(required=True, help_text="招聘表id")
    cv_id = serializers.IntegerField(required=True, help_text="简历id")


# 删除投递接口反序列化器
class DeleteCvDetail(serializers.Serializer):
    id = serializers.IntegerField(required=True, help_text="应聘行为表id")
