# author: Mr. Ma
# datetime :2022/7/21
import uuid
from django.db import models
from user.models import User

STATES = {
    (0, "使用中"),
    (1, "已禁用"),
}


class SensitiveWordFieldClassify(models.Model):
    name = models.CharField(max_length=20, null=True, verbose_name='敏感词')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    state = models.IntegerField(default=0, choices=STATES)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = '敏感词类别表'


class SensitiveWordInfo(models.Model):
    uid = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=1000, null=True, verbose_name='敏感词')
    classify = models.ForeignKey(SensitiveWordFieldClassify, null=True, on_delete=models.CASCADE,
                                 verbose_name='敏感词类别id')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    state = models.IntegerField(choices=STATES, default=0)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = '敏感词'


class CommonWords(models.Model):
    word = models.CharField(max_length=200, verbose_name="常用语")
    user = models.ForeignKey(User, verbose_name="用户", on_delete=models.CASCADE)
    index = models.IntegerField(default=1, verbose_name="排序")
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')
    is_end = models.BooleanField(default=False, verbose_name='是否最后一条')

    def __str__(self):
        return str(self.word)

    class Meta:
        verbose_name_plural = "常用语表"
