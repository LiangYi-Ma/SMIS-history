from __future__ import unicode_literals


from django.db import models
from django.contrib.auth.models import User
from SMIS.constants import USER_CLASSES
from SMIS.validation import tuple2list


# Create your models here.
# coding=UTF-8

from django.utils.translation import ugettext as _


class CreatorMixin:
    """
    实现创建者的 Model 基类。
    """
    def get_creator(self, obj):
        """
        获取对象的创建者，子类重写该方法实现创建者对象的获取。
        :return: 当前对象的创建者。
        """
        try:
            return obj.get_creator()
        except:
            return None

    def set_creator(self, user, obj):
        """
        设置对象的创建者，子类重写该方法实现创建者对象的设置。
        :param creator: 要设置为创建者的User对象。
        :return:
        """
        obj.set_creator(user=user)
        pass


class OwnerMixin:
    """
    实现所有者的 Model 基类。
    """
    def get_owner(self, obj):
        """
        获取对象的所有者，子类重写该方法实现所有者对象的获取。
        :return: 当前对象的所有者。
        """
        try:
            return obj.get_owner()
        except:
            return None

    def set_owner(self, user, obj):
        """
        设置对象的所有者，子类重写该方法实现所有者对象的设置。
        :param owner: 要设置为所有者的User对象。
        :return:
        """
        obj.set_owner(user=user)
        pass


class UserClass(models.Model):
    user_id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    # 默认类别是所有人
    user_class = models.IntegerField(choices=USER_CLASSES, default=0)

    def set_class(self, class_code):
        if class_code not in tuple2list(USER_CLASSES)[0]:
            return -1
        else:
            self.user_class = class_code
            self.save()
            return 1

    def get_class(self):
        return self.user_class

