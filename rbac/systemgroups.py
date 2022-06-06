"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
# coding=UTF-8
from __future__ import unicode_literals

from django.contrib.auth.models import Group

from .models import CreatorMixin, OwnerMixin


SYSTEM_GROUP_EVERYONE = "Everyone"      # 所有人
SYSTEM_GROUP_ANONYMOUS = "Anonymous"    # 匿名用户
SYSTEM_GROUP_USERS = "Users"            # 用户
SYSTEM_GROUP_STAFFS = "Staffs"          # 职员
# 超级管理员
SYSTEM_GROUP_SUPER_ADMIN = "Superusers"
# 系统运营
SYSTEM_GROUP_OPE_ADMIN = "Operation Admins"
# 系统组织
SYSTEM_GROUP_ORG_ADMIN = "Organization Admins"
# 企业超管
SYSTEM_GROUP_ETP_ORG_SUPER_ADMIN = "Enterprise Superusers"
# 企业管理
SYSTEM_GROUP_ETP_ORG_ADMIN = "Enterprise Admins"
# 学校
SYSTEM_GROUP_CLG_ORG_SUPER_ADMIN = "College Superusers"
SYSTEM_GROUP_CLG_ORG_ADMIN = "College Admins"
# 社会
SYSTEM_GROUP_SCT_ORG_SUPER_ADMIN = "Society Superusers"
SYSTEM_GROUP_SCT_ORG_ADMIN = "Society Admins"

SYSTEM_GROUP_CREATOR = "Creator"        # 创建者
SYSTEM_GROUP_OWNER = "Owner"            # 所有者


def get_user_systemgroups(user):
    """
    获取指定用户所属的系统组集合。
    :param user: 指定的用户。
    :return: set 表示的用户所属的系统组名称集合。
    """
    groups = set()
    groups.add(SYSTEM_GROUP_EVERYONE)
    if user.is_anonymous:
        groups.add(SYSTEM_GROUP_ANONYMOUS)
    else:
        groups.add(SYSTEM_GROUP_USERS)
        if user.is_staff:
            groups.add(SYSTEM_GROUP_STAFFS)
        if user.is_superuser:
            groups.add(SYSTEM_GROUP_SUPER_ADMIN)


    return groups


def get_user_systemgroups_for_obj(user, obj):
    """
    获取指定用户相对于指定的对象所属的系统组集合。
    :param user: 指定的用户。
    :param obj: 相对于指定的对象。
    :return: set 表示的用户所属的系统组名称集合。
    """
    groups = set()

    if CreatorMixin().get_creator(obj) == user:
        groups.add(SYSTEM_GROUP_CREATOR)
    if OwnerMixin().get_owner(obj) == user:
        groups.add(SYSTEM_GROUP_OWNER)
    return groups
