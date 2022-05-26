from django.shortcuts import render
from .systemgroups import get_user_systemgroups, get_user_systemgroups_for_obj
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from . import models
from cert.models import studentInfo
from user.models import PersonalInfo
from enterprise.models import EnterpriseInfo
from SMIS.models_utils import StandardResultSetPagination
import json
from user import serializers

# Create your views here.

SYSTEM_GROUP_EVERYONE = "Everyone"  # 所有人
SYSTEM_GROUP_ANONYMOUS = "Anonymous"  # 匿名用户
SYSTEM_GROUP_USERS = "Users"  # 用户
SYSTEM_GROUP_STAFFS = "Staffs"  # 职员
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


def get_group(user, obj=None):
    group = get_user_systemgroups(user)
    if obj:
        group.add(get_user_systemgroups_for_obj(user=user, obj=obj))
    return group


class InitialSystemGroup(APIView):
    def get(self, request):
        Group.objects.get_or_create(name=SYSTEM_GROUP_EVERYONE)
        Group.objects.get_or_create(name=SYSTEM_GROUP_ANONYMOUS)
        Group.objects.get_or_create(name=SYSTEM_GROUP_USERS)
        Group.objects.get_or_create(name=SYSTEM_GROUP_STAFFS)
        Group.objects.get_or_create(name=SYSTEM_GROUP_SUPER_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_ORG_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_OPE_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_ETP_ORG_SUPER_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_ETP_ORG_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_CLG_ORG_SUPER_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_CLG_ORG_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_SCT_ORG_SUPER_ADMIN)
        Group.objects.get_or_create(name=SYSTEM_GROUP_SCT_ORG_ADMIN)
        return Response({})


class InitialUserClassData(APIView):
    def get(self, request):
        user_qs = User.objects.all()
        for user_obj in user_qs:
            try:
                new_obj = models.UserClass.objects.get(user_id=user_obj)
            except:
                new_obj = models.UserClass.objects.create(user_id=user_obj)
            if user_obj.is_superuser:
                new_obj.user_class = 1001
            elif EnterpriseInfo.objects.filter(id=user_obj).exists():
                new_obj.user_class = 3
            elif studentInfo.objects.using("db_cert").filter(student_id=user_obj.id).exists():
                new_obj.user_class = 2
            elif PersonalInfo.objects.filter(id=user_obj).exists():
                new_obj.user_class = 1
            new_obj.save()
        return Response({})


class InitialUsersGroups(APIView):

    def get(self, request):
        all_user = User.objects.all()
        for user_obj in all_user:
            everyone_group = Group.objects.get(name=SYSTEM_GROUP_EVERYONE)
            everyone_group.user_set.add(user_obj)
            if user_obj.is_staff:
                staff_groups = Group.objects.get(name=SYSTEM_GROUP_STAFFS)
                staff_groups.user_set.add(user_obj)
                if user_obj.is_superuser:
                    superuser_group = Group.objects.get(name=SYSTEM_GROUP_SUPER_ADMIN)
                    superuser_group.user_set.add(user_obj)

        return Response({})


class Roles(APIView):

    def get(self, request, role_id=None):
        data = dict()
        if not role_id:
            query_set = User.objects.filter(userclass__user_class__gt=1000).order_by("-userclass__user_class")
            '''
            1.分页
            2.制作序列化器
            3.返回角色的信息
            '''
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(query_set, request)
            serializer = serializers.UserSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)
        else:
            '''
            返回某个角色的信息
            '''
            role = User.objects.get(id=role_id)
            serializer = serializers.UserSerializer(instance=role, many=False)

        return Response(serializer.data)

    def delete(self, request, role_id):
        data = dict()
        '''
        删除角色
        如果系统中只剩下唯一一个超级管理，不可以删除
        '''
        try:
            role = User.objects.get(id=role_id)
        except:
            return Response(status=404, data=dict(msg="user not exists."))
        if role.is_superuser:
            superuser_group = Group.objects.get(name=SYSTEM_GROUP_SUPER_ADMIN)
            if superuser_group.user_set.count() <= 1:
                return Response(status=404, data=dict(msg="At least one superuser needed."))

        role.delete()

        return Response(data)

    def add(self, request):
        json_data = json.loads(request.body.decode())
        data = dict()
        '''
        添加角色，给角色分组
        '''

        return Response(data)

    def put(self, request, role_id):
        json_data = json.loads(request.body.decode())
        data = dict()
        '''
        更新角色
        '''
        return Response(data)
