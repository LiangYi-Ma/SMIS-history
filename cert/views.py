import time

import zmail
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib import auth
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.views.generic.base import View
from django.utils.crypto import get_random_string
from numpy import unicode
from django.db.models import Q
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives
from uuid import uuid4

from user.models import User, PersonalInfo, JobExperience, TrainingExperience, \
    EducationExperience, Evaluation, WxUserPhoneValidation
from cv.models import CV, Industry, CV_PositionClass
from enterprise.models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, PositionClass
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from enterprise.models import SettingChineseTag, TaggedWhatever

import datetime
import json
from cv.views import calculate_age
import re
import random as rd
import numpy as np
from PIL import Image
import requests
import urllib

from SMIS import constants, mapper
from SMIS import validation as global_validation
from cert.models import studentInfo, teacherInfo, courseInfo, certificationInfo, classInfo, \
    classCourseCertCon, classTeacherCon, classStudentCon, classExamCon, practiceRecords, examRecords, \
    updateDateRecords, failedUpdateRecords, onlineStudyRecords
from cert.csv_file_process import process_student_file
from cert import csv_file_process
from cert import validation
from SMIS import settings
from cert.api_xet_client import XiaoeClient
from SMIS.api_authority_manager import AuthorityManager
from cert.api_crontab import update_online_study_progress_by_hand


# Create your views here.


# 判断session 是否过期
def session_exist(request):
    # session_key = request.session.session_key
    session_key = request.META.get("HTTP_AUTHORIZATION")
    print("*****", request.META.get("HTTP_AUTHORIZATION"))
    for k, v in request.META.items():
        print("> ", k, ":", v)
    back_dir = dict(code=1000, msg="", data=dict())
    try:
        is_existed = Session.objects.get(session_key__exact=session_key)
        # if is_existed and is_existed.expire_date <= datetime.datetime.now():
        #     back_dir["code"] = 0
        #     back_dir["msg"] = "session[" + is_existed.session_key + "]已失效"
        #     request.session.flush()
    except:
        if session_key:
            back_dir["code"] = 0
            back_dir["msg"] = "session[" + session_key + "]未被检测到"
        else:
            back_dir["code"] = 0
            back_dir["msg"] = "接收到的session_key为空"
    return back_dir


class registerStudentView(View):
    """注册为学员"""

    # 未启用get
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""

        # 暂时不需要，后续可以删掉这段
        sex_choice = []
        for idx, label in constants.SEX_CHOICE:
            sex_choice.append(dict(idx=idx, label=label))
        data["sex_choices"] = sex_choice

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        para = json.loads(request.body.decode())
        """main content of this method"""
        if para["type"] == "101":
            # new student registration
            valid_dic = validation.student_info_is_valid(para)
            if valid_dic["code"] != 1000:
                return JsonResponse(valid_dic)

            this_student = studentInfo.objects.using("db_cert").filter(student_id=user.id)
            if this_student.exists():
                back_dic["code"] = 10010
                back_dic["msg"] = "系统已检测到您的学员信息，无法新增"
                return JsonResponse(back_dic)

            new_student = studentInfo.objects.using("db_cert").create(student_id=user.id, student_name=para["name"],
                                                                      phone_number=para["phone"],
                                                                      wechat_openid=para["wechat"],
                                                                      id_number=para["id_number"],
                                                                      is_valid=0)
            new_student.update_sex()
            back_dic["code"] = 1000
            back_dic["msg"] = "学生" + para["name"] + "已注册成功，请尽快完成认证过程"
        elif para["type"] == "102":
            # edit student info
            valid_dic = validation.student_info_is_valid(para)
            if valid_dic["code"] != 1000:
                return JsonResponse(valid_dic)

            this_student = studentInfo.objects.using("db_cert").filter(student_id=user.id)
            if not this_student.exists():
                back_dic["code"] = 10010
                back_dic["msg"] = "未检测到您的学员信息"
                return JsonResponse(back_dic)
            elif len(this_student) > 1:
                back_dic["code"] = 10011
                back_dic["msg"] = "检测到多条学员信息，请刷新重试"
                return JsonResponse(back_dic)

            this_student = this_student.first()
            this_student.student_name = para["name"]
            this_student.phone_number = para["phone"]
            this_student.wechat_openid = para["wechat"]
            this_student.id_number = para["id_number"]
            this_student.update_sex()
            this_student.save()
            back_dic["msg"] = "学员信息已修改成功"

        back_dic["data"] = data
        return JsonResponse(back_dic)


class studentCertificationView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        this_student = studentInfo.objects.using("db_cert").filter(student_id=user.id)
        if not this_student.exists():
            back_dic["code"] = 10010
            back_dic["msg"] = "未检测到您的学员信息"
            return JsonResponse(back_dic)
        elif len(this_student) > 1:
            back_dic["code"] = 10011
            back_dic["msg"] = "检测到多条学员信息，请刷新重试"
            return JsonResponse(back_dic)

        this_student = this_student.first()
        validation_dis = "认证未开始"
        for idx, value in constants.XET_VALIDATION:
            if idx == this_student.is_valid:
                validation_dis = value

        data["student_name"] = this_student.student_name
        data["is_valid"] = validation_dis

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        this_student = studentInfo.objects.using("db_cert").filter(student_id=user.id)
        if not this_student.exists():
            back_dic["code"] = 10010
            back_dic["msg"] = "未检测到您的学员信息"
            return JsonResponse(back_dic)
        elif len(this_student) > 1:
            back_dic["code"] = 10011
            back_dic["msg"] = "检测到多条学员信息，请刷新重试"
            return JsonResponse(back_dic)

        this_student = this_student.first()

        para = json.loads(request.body.decode())
        """main content of this method"""
        if para["type"] == "101":
            if this_student.is_valid != 0:
                back_dic["code"] = 10012
                back_dic["msg"] = "检测到您已提交过认证信息"
            else:
                this_student.is_valid = 3
                this_student.save()
                back_dic["code"] = 1000
                back_dic["msg"] = "已提交认证信息，请耐心等待审核"

        back_dic["data"] = data
        return JsonResponse(back_dic)


class bindingXetUser(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        this_student = studentInfo.objects.using("db_cert").get(student_id=user.id)

        # para = json.loads(request.body.decode())
        """main content of this method"""

        # student_phone = para["phone"]
        student_phone = this_student.phone_number
        api_url = "https://api.xiaoe-tech.com/xe.user.info.get/1.0.0"
        params = {
            "data": {
                "phone": student_phone,
                "field_list": [
                    "name"
                ]
            }
        }
        client = XiaoeClient()
        res = client.request("post", api_url, params)
        """
        res = {"code": 0,
               "msg": "ok",
               "data": {
                   "app_id": "appHTPxaGTp7928", "name": "阿白", "nickname": "阿白",
                   "user_id": "u_lp_1646624034_62257d2288179_fx4guN", "wx_open_id": "od0Ahs4drDFcw66MX-BmYJj0OPNw",
                   "wx_union_id": null}
               }
        """
        if res["code"] == 0:
            '''查询到用户'''
            this_student.xet_id = res["data"]["user_id"]
            this_student.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "绑定小鹅通账号成功"
            return JsonResponse(back_dic)
        else:
            '''未查询到用户'''
            back_dic["code"] = 10200
            back_dic["msg"] = "未在店铺内检测到您的账号，请检查：1.手机号是否正确输入；2.是否已关注店铺"
            return JsonResponse(back_dic)


class registerXetUser(View):
    """收集用户信息，为用户注册小鹅通账号，还没写"""

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        para = json.loads(request.body.decode())
        """main content of this method"""

        back_dic["data"] = data
        return JsonResponse(back_dic)


class updateStudentValidationViaFile(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""
        # 优先列
        data["first_line"] = csv_file_process.MOBILE_FIRST_LINE
        data["second_line"] = csv_file_process.MOBILE_SECOND_LINE
        # 等待认证的学员总数
        student_waiting_list = studentInfo.objects.using("db_cert").filter(is_valid=3)
        data["students_in_waiting_list"] = student_waiting_list.count()

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        user_valid = validation.users_validation_check(user)
        if not user_valid:
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限"
            return JsonResponse(back_dic)

        """main content of this method"""

        # 拿到csv文件
        student_certification_file = request.FILES.get("student_file")
        # 该文件中包含的合法手机号
        valid_mobiles_in_this_file = process_student_file(student_certification_file)
        if valid_mobiles_in_this_file is -1:
            back_dic["code"] = 1001
            back_dic["msg"] = "文件格式不合法，请检查该文件的后缀是否为.csv，以及表头是否包含提示中的所有处理依据。"
            return JsonResponse(back_dic)
        # valid_mobiles_in_this_file.append("11111311111")
        # data["valid_mobile"] = valid_mobiles_in_this_file
        update_count = 0
        student_waiting_list = studentInfo.objects.using("db_cert").filter(is_valid=3)
        for student in student_waiting_list:
            if student.phone_number in valid_mobiles_in_this_file.keys():
                student.is_valid = 1
                update_count += 1
                student.xet_id = valid_mobiles_in_this_file[student.phone_number]
                student.save()
        back_dic["msg"] = "已更新完成。请知悉：本次更新成功认证学生共" + str(
            update_count) + "人。"
        back_dic["code"] = 1000
        back_dic["data"] = data
        # 等待认证的学生
        data["waiting_student"] = student_waiting_list.count()
        # 认证成功的学生
        '''目前并未将等待认证但没有认证成功的学生设定为"认证失败"状态'''
        data["confirmed_student_this_time"] = update_count
        return JsonResponse(back_dic)


class updateStudentExamStatusViaFile(View):
    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        user_valid = validation.users_validation_check(user)
        if not user_valid:
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限"
            return JsonResponse(back_dic)

        """main content of this method"""
        class_id = self.kwargs["class_id"]
        this_class = classInfo.objects.using("db_cert").filter(class_id=class_id)
        if not this_class.exists():
            back_dic["code"] = 10200
            back_dic["msg"] = "该班级不存在，请检查url"
            return JsonResponse(back_dic)
        this_class = this_class.first()
        if not this_class.is_exam_exist:
            back_dic["code"] = 10001
            back_dic["msg"] = "该班级不包含考试考核，无法上传"
            return JsonResponse(back_dic)

        exam_file = request.FILES.get("exam_file")
        # 拿到成绩字典
        exam_grade = csv_file_process.process_exam_file(exam_file)

        back_dic["data"] = data
        return JsonResponse(back_dic)


class certEditionView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""
        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        # 当前证书列表，优先按照名称分组，组内按照级别排序，
        certification_query = certificationInfo.objects.using("db_cert").all().order_by('cert_name', 'cert_level')
        data["certification_count"] = certification_query.count()

        certification_info = []
        # 证书信息
        for each_cert in certification_query:
            cert_level = ""
            for k, v in constants.CERTIFICATION_LEVEL:
                if k == each_cert.cert_level:
                    cert_level = v

            testing_way = ""
            for k, v in constants.TESTING_WAYS:
                if k == each_cert.testing_way:
                    testing_way = v

            cert_dic = dict(
                cert_id=each_cert.cert_id,
                cert_name=each_cert.cert_name,
                cert_level=cert_level,
                issuing_unit=each_cert.issuing_unit,
                cert_introduction=each_cert.cert_introduction,
                testing_way=testing_way,
                aim_people=each_cert.aim_people,
                cor_positions=each_cert.cor_positions,
                expiry_date=each_cert.expiry_date,
                cert_sample=unicode(each_cert.cert_sample)
            )
            certification_info.append(cert_dic)
        data["certification_info"] = certification_info

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        """证书编辑：添加/删除/修改（证书样图的修改在另一个单独的方法）"""
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        """main content of this method"""
        try:
            para = json.loads(request.body.decode())
            edit_type = para["type"]
        except:
            back_dic["code"] = 10100
            back_dic["msg"] = "数据传输异常，请检查传递内容/方法"
            return JsonResponse(back_dic)

        if edit_type is "0":
            '''证书删除'''
            try:
                this_cert_query = certificationInfo.objects.using("db_cert").get(cert_id=para["cert_id"])
                this_cert_query.delete()
                back_dic["code"] = 1000
                back_dic["msg"] = "该证书已删除"
            except:
                back_dic["code"] = 10200
                back_dic["msg"] = "删除失败，请刷新重试"
        else:
            '''证书新增/修改'''
            if edit_type is "1":
                valid_res = validation.cert_is_valid(para)
                if valid_res["code"] == 1000:
                    '''执行新增'''

                    '''查重（名称、等级均相同为重复），返回错误'''
                    is_exist = certificationInfo.objects.using("db_cert").filter(
                        cert_name=para["cert_name"],
                        cert_level=para["cert_level"]
                    )
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "该证书已存在，无法继续创建，如需修改请点击编辑"
                        return JsonResponse(back_dic)

                    '''新增证书'''
                    new_cert = certificationInfo.objects.using("db_cert").create(
                        cert_name=para["cert_name"],
                        cert_level=para["cert_level"],
                        issuing_unit=para["issuing_unit"],
                        cert_introduction=para["cert_introduction"],
                        testing_way=para["testing_way"],
                        aim_people=para["aim_people"],
                        cor_positions=para["cor_positions"],
                        expiry_date=para["expiry_date"]
                    )

                    # 新证书的等级，返回用
                    cert_level_des = ""
                    for k, v in constants.CERTIFICATION_LEVEL:
                        if k == para["cert_level"]:
                            cert_level_des = v

                    back_dic["code"] = 1000
                    back_dic["msg"] = "证书《" + new_cert.cert_name + "(" + cert_level_des + ")》已创建"
                    return JsonResponse(back_dic)
                else:
                    '''未通过合法性验证'''
                    back_dic = valid_res
                    return JsonResponse(back_dic)
            elif edit_type is "2":
                '''证书信息修改'''
                valid_res = validation.cert_is_valid(para)
                if valid_res["code"] == 1000:
                    '''执行修改'''
                    this_cert_query = certificationInfo.objects.using("db_cert").filter(cert_id=para["cert_id"])
                    # 证书不存在
                    if not this_cert_query.exists():
                        back_dic["code"] = 10200
                        back_dic["msg"] = "不存在的证书，无法进行修改操作。请刷新重试"
                        return JsonResponse(back_dic)

                    '''查重（修改后的信息与其他数据重复），返回错误'''
                    is_exist = certificationInfo.objects.using("db_cert").filter(
                        cert_name=para["cert_name"],
                        cert_level=para["cert_level"],
                    ).exclude(cert_id=para["cert_id"]).all()
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "存在与修改后的证书相同的数据，请前往相应证书位置进行修改"
                        return JsonResponse(back_dic)

                    # 修改证书
                    this_cert = this_cert_query.first()
                    this_cert.cert_name = para["cert_name"]
                    this_cert.cert_level = para["cert_level"]
                    this_cert.issuing_unit = para["issuing_unit"]
                    this_cert.cert_introduction = para["cert_introduction"]
                    this_cert.testing_way = para["testing_way"]
                    this_cert.aim_people = para["aim_people"]
                    this_cert.cor_positions = para["cor_positions"]
                    this_cert.expiry_date = para["expiry_date"]
                    this_cert.save()

                    back_dic["code"] = 1000
                    back_dic["msg"] = "证书已修改"
                    return JsonResponse(back_dic)
                else:
                    '''合法验证不通过'''
                    back_dic = valid_res
                    return JsonResponse(back_dic)

        back_dic["data"] = data
        return JsonResponse(back_dic)


def editCertificationSample(request, cert_id):
    session_dict = session_exist(request)
    if session_dict["code"] != 1000:
        return JsonResponse(session_dict)
    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    valid_res = AuthorityManager(user_obj=user)
    if not valid_res.is_staff():
        back_dic["code"] = 10400
        back_dic["msg"] = "无权限查看"
        return JsonResponse(back_dic)

    this_cert = certificationInfo.objects.using("db_cert").filter(cert_id=cert_id)
    if not this_cert.exists():
        back_dic["code"] = 10200
        back_dic["msg"] = "该证书不存在。"
        return JsonResponse(back_dic)

    this_cert = this_cert.first()
    data["cert_sample"] = unicode(this_cert.cert_sample)

    """main content of this method"""
    if request.method == "POST":
        file_obj = request.FILES.get('cert_sample')
        if not file_obj:
            back_dic["code"] = 1002
            back_dic["msg"] = "未接收到证书样例图片，请检查上传文件格式。"
            return JsonResponse(back_dic)

        this_cert.cert_sample = file_obj
        this_cert.save()
        back_dic["msg"] = "上传成功，请刷新查看。"

    back_dic["data"] = data
    return JsonResponse(back_dic)


class teacherEditionView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        """main content of this method"""
        teacher_query = teacherInfo.objects.using("db_cert").order_by("-level", "teaching_field").all()
        teacher_count = teacher_query.count()
        data["teacher_count"] = teacher_count

        teacher_list = []
        for each_teacher in teacher_query:
            teach_field = ""
            for k, v in constants.TEACHING_FIELDS:
                if k == each_teacher.teaching_field:
                    teach_field = v

            teacher_level = ""
            for k, v in constants.TEACHER_LEVEL:
                if k == each_teacher.level:
                    teacher_level = v

            teacher_info = dict(
                teacher_id=each_teacher.teacher_id,
                teacher_name=each_teacher.teacher_name,
                phone_number=each_teacher.phone_number,
                wechat=each_teacher.wechat_openid,
                teaching_field=teach_field,
                self_introduction=each_teacher.self_introduction,
                teacher_level=teacher_level,
                photo=str(each_teacher.photo)
            )
            teacher_list.append(teacher_info)

        data["teacher_list"] = teacher_list
        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        """main content of this method"""
        try:
            para = json.loads(request.body.decode())
            edit_type = para["type"]
        except:
            back_dic["code"] = 10100
            back_dic["msg"] = "数据传输异常，请检查传递内容/方法"
            return JsonResponse(back_dic)

        if edit_type is "0":
            '''教师删除'''
            try:
                this_teacher = teacherInfo.objects.using("db_cert").get(teacher_id=para["teacher_id"])
                this_teacher.delete()
                back_dic["code"] = 1000
                back_dic["msg"] = "该教师已删除"
            except:
                back_dic["code"] = 10200
                back_dic["msg"] = "删除失败，请刷新重试"
        else:
            '''教师新增/修改，教师照片的修改在另一个方法里'''
            if edit_type is "1":
                '''新增教师'''
                valid_res = validation.teacher_is_valid(para)
                if valid_res["code"] == 1000:
                    '''查重，姓名+电话'''
                    is_exist = teacherInfo.objects.using("db_cert").filter(teacher_name=para["teacher_name"],
                                                                           phone_number=para["phone_number"])
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "该教师 " + para["teacher_name"] \
                                          + "(" + str(para["phone_number"]) + ")已存在，请前往编辑，无法新增。"
                        return JsonResponse(back_dic)

                    new_teacher = teacherInfo.objects.using("db_cert").create(
                        teacher_name=para["teacher_name"],
                        phone_number=para["phone_number"],
                        wechat_openid=para["wechat_openid"],
                        teaching_field=para["teaching_field"],
                        self_introduction=para["self_introduction"],
                        level=para["level"]
                    )
                    back_dic["code"] = 1000
                    back_dic["msg"] = "教师 " + new_teacher.teacher_name \
                                      + "(" + str(new_teacher.phone_number) + ")已新增成功。"
                    return JsonResponse(back_dic)
                else:
                    back_dic = valid_res
                    return JsonResponse(back_dic)
            elif edit_type is "2":
                valid_res = validation.teacher_is_valid(para)
                if valid_res["code"] == 1000:
                    '''查重，修改后的内容有电话+姓名与其他数据相同的，视为重复'''
                    is_exist = teacherInfo.objects.using("db_cert").filter(
                        teacher_name=para["teacher_name"],
                        phone_number=para["phone_number"],
                    ).exclude(teacher_id=para["teacher_id"])
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "该教师信息已存在，请前往相应教师信息处修改。"
                        return JsonResponse(back_dic)

                    '''检查数据存在与否'''
                    this_teacher = teacherInfo.objects.using("db_cert").filter(teacher_id=para["teacher_id"])
                    if not this_teacher.exists():
                        back_dic["code"] = 10200
                        back_dic["msg"] = "该教师不存在，无法进行修改。"
                        return JsonResponse(back_dic)

                    # 修改教师
                    this_teacher = this_teacher.first()
                    this_teacher.teacher_name = para["teacher_name"]
                    this_teacher.phone_number = para["phone_number"]
                    this_teacher.wechat_openid = para["wechat_openid"]
                    this_teacher.teaching_field = para["teaching_field"]
                    this_teacher.self_introduction = para["self_introduction"]
                    this_teacher.level = para["level"]
                    this_teacher.save()
                    back_dic["code"] = 1000
                    back_dic["msg"] = "教师信息已修改"
                    return JsonResponse(back_dic)
                else:
                    back_dic = valid_res
                    return JsonResponse(back_dic)
        back_dic["data"] = data
        return JsonResponse(back_dic)


def editTeacherPhoto(request, teacher_id):
    session_dict = session_exist(request)
    if session_dict["code"] != 1000:
        return JsonResponse(session_dict)
    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    valid_res = AuthorityManager(user_obj=user)
    if not valid_res.is_staff():
        back_dic["code"] = 10400
        back_dic["msg"] = "无权限查看"
        return JsonResponse(back_dic)

    '''检查该教师是否存在'''
    this_teacher = teacherInfo.objects.using("db_cert").filter(teacher_id=teacher_id)
    if not this_teacher.exists():
        back_dic["code"] = 10200
        back_dic["msg"] = "该教师不存在，请检查url是否正确"
        return JsonResponse(back_dic)

    this_teacher = this_teacher.first()

    """main content of this method"""
    if request.method == "POST":
        file_obj = request.FILES.get("teacher_photo")
        '''未接收到图片'''
        if not file_obj:
            back_dic["code"] = 1002
            back_dic["msg"] = "未接收到照片，请检查：1.变量名；2.文件格式；3.数据传递方式"
            return JsonResponse(back_dic)

        '''修改图片'''
        this_teacher.photo = file_obj
        this_teacher.save()
        back_dic["code"] = 1000
        back_dic["msg"] = "图片已成功上传"

    back_dic["data"] = data
    return JsonResponse(back_dic)


class courseEditionView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        """main content of this method"""
        # 所有课程，按照课程方向分组，课程类别排序
        all_course = courseInfo.objects.using("db_cert").order_by("course_direction", "course_type").all()
        # 课程数量
        course_count = all_course.count()
        # 课程列表
        course_list = []
        for each_course in all_course:
            course_direction = ""
            for k, v in constants.COURSE_DIRECTION:
                if k == each_course.course_direction:
                    course_direction = v
            course_type = ""
            for k, v in constants.COURSE_TYPE:
                if k == each_course.course_type:
                    course_type = v
            dic = dict(
                course_id=each_course.course_id,
                course_name=each_course.course_name,
                course_direction=course_direction,
                course_type=course_type,
                course_price=each_course.course_price,
                course_true_price=each_course.course_true_price,
                ads_picture=str(each_course.ads_picture),
            )
            course_list.append(dic)

        data["course_count"] = course_count
        data["course_list"] = course_list

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        para = json.loads(request.body.decode())
        """main content of this method"""
        try:
            para = json.loads(request.body.decode())
            edit_type = para["type"]
        except:
            back_dic["code"] = 10100
            back_dic["msg"] = "数据传输异常，请检查传递内容/方法"
            return JsonResponse(back_dic)

        if edit_type is "0":
            is_exist = courseInfo.objects.using("db_cert").filter(course_id=para["course_id"])
            if is_exist.exists():
                this_course = is_exist.first()
                this_course.delete()
                back_dic["code"] = 1000
                back_dic["msg"] = "该课程已删除"
                return JsonResponse(back_dic)
            else:
                back_dic["code"] = 10200
                back_dic["msg"] = "无法删除该课程，请重试"
                return JsonResponse(back_dic)
        elif edit_type in ["1", "2"]:
            valid_res = validation.course_is_valid(para)
            if valid_res["code"] == 1000:
                if edit_type is "1":
                    '''新增课程'''
                    '''查重，课程名+方向+类别相同为重复'''
                    is_exist = courseInfo.objects.using("db_cert").filter(
                        course_name=para["course_name"],
                        course_type=para["course_type"],
                        course_direction=para["course_direction"])
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "该课程已存在，无法新增"
                        return JsonResponse(back_dic)

                    new_course = courseInfo.objects.using("db_cert").create(
                        course_name=para["course_name"],
                        course_direction=para["course_direction"],
                        course_type=para["course_type"],
                        course_price=para["course_price"],
                        course_true_price=para["course_true_price"]
                    )
                    back_dic["code"] = 1000
                    back_dic["msg"] = "课程'" + new_course.course_name + "'已新增"
                    return JsonResponse(back_dic)
                else:
                    '''修改课程'''
                    '''判断该课程是否存在'''
                    this_course = courseInfo.objects.using("db_cert").filter(course_id=para["course_id"])
                    if not this_course.exists():
                        back_dic["code"] = 10200
                        back_dic["msg"] = "不存在的课程"
                        return JsonResponse(back_dic)
                    '''查重，修改后课程名+类型+方向相同为重复'''
                    is_exist = courseInfo.objects.using("db_cert").filter(
                        course_name=para["course_name"],
                        course_type=para["course_type"],
                        course_direction=para["course_direction"]).exclude(course_id=para["course_id"])
                    if is_exist.exists():
                        back_dic["code"] = 10300
                        back_dic["msg"] = "课程信息重复，该课程已存在，请前往相应课程处进行修改"
                        return JsonResponse(back_dic)

                    this_course = this_course.first()
                    this_course.course_name = para["course_name"]
                    this_course.course_type = para["course_type"]
                    this_course.course_direction = para["course_direction"]
                    this_course.course_price = para["course_price"]
                    this_course.course_true_price = para["course_true_price"]
                    this_course.save()
                    back_dic["code"] = 1000
                    back_dic["msg"] = "课程已修改"
                    return JsonResponse(back_dic)
            else:
                back_dic = valid_res
                return JsonResponse(back_dic)
        else:
            back_dic["code"] = 10099
            back_dic["msg"] = "无法识别的编辑类型，请检查所发送的数据"

        back_dic["data"] = data
        return JsonResponse(back_dic)


def editCourseAdsPicture(request, course_id):
    session_dict = session_exist(request)
    if session_dict["code"] != 1000:
        return JsonResponse(session_dict)
    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    valid_res = AuthorityManager(user_obj=user)
    if not valid_res.is_staff():
        back_dic["code"] = 10400
        back_dic["msg"] = "无权限查看"
        return JsonResponse(back_dic)

    '''检查该课程是否存在'''
    this_course = courseInfo.objects.using("db_cert").filter(course_id=course_id)
    if not this_course.exists():
        back_dic["code"] = 10200
        back_dic["msg"] = "该课程不存在，请检查url是否正确"
        return JsonResponse(back_dic)

    this_course = this_course.first()

    """main content of this method"""
    if request.method == "POST":
        file_obj = request.FILES.get("course_ads_picture")
        '''未接收到图片'''
        if not file_obj:
            back_dic["code"] = 1002
            back_dic["msg"] = "未接收到图片，请检查：1.变量名；2.文件格式；3.数据传递方式"
            return JsonResponse(back_dic)

        '''修改图片'''
        this_course.ads_picture = file_obj
        this_course.save()
        back_dic["code"] = 1000
        back_dic["msg"] = "图片已成功上传"

    back_dic["data"] = data
    return JsonResponse(back_dic)


class classEditionView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        #
        # valid_res = AuthorityManager(user_obj=user)
        # if not valid_res.is_staff():
        #     back_dic["code"] = 10400
        #     back_dic["msg"] = "无权限查看"
        #     return JsonResponse(back_dic)

        """main content of this method"""
        '''状态不为关闭的班级'''
        class_not_closed = classInfo.objects.using("db_cert").filter(~Q(class_status=3))
        class_not_closed_list = []
        for each_class in class_not_closed:
            class_type = ""
            for k, v in constants.CLASS_TYPE:
                if each_class.class_type == k:
                    class_type = v

            class_period = ""
            for k, v in constants.CLASS_PERIOD:
                if each_class.class_period == k:
                    class_period = v

            class_status = ""
            for k, v in constants.CLASS_STATUS:
                if each_class.class_status == k:
                    class_status = v

            # 班级的基本信息
            class_info = dict(
                class_id=each_class.class_id,
                class_type=class_type,
                class_period=class_period,
                start_date=str(each_class.class_start_date),
                end_date=str(each_class.class_end_date),
                has_exam=each_class.is_exam_exist,
                has_practice=each_class.is_practice_exist,
                has_cert=each_class.is_cert_exist,
                has_online_study=each_class.is_online_study_exist,
                class_status=class_status
            )
            class_not_closed_list.append(class_info)
        data["class_not_closed"] = class_not_closed_list

        '''关闭状态的班级'''
        class_closed = classInfo.objects.using("db_cert").filter(class_status=3)
        class_closed_list = []
        for each_class in class_closed:
            class_type = ""
            for k, v in constants.CLASS_TYPE:
                if each_class.class_type == k:
                    class_type = v

            class_period = ""
            for k, v in constants.CLASS_PERIOD:
                if each_class.class_period == k:
                    class_period = v

            class_status = ""
            for k, v in constants.CLASS_STATUS:
                if each_class.class_status == k:
                    class_status = v

            # 班级的基本信息
            class_info = dict(
                class_id=each_class.class_id,
                class_type=class_type,
                class_period=class_period,
                start_date=str(each_class.class_start_date),
                end_date=str(each_class.class_end_date),
                has_exam=each_class.is_exam_exist,
                has_practice=each_class.is_practice_exist,
                has_cert=each_class.is_cert_exist,
                has_online_study=each_class.is_online_study_exist,
                class_status=class_status
            )
            class_closed_list.append(class_info)
        data["class_closed"] = class_closed_list

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        valid_res = AuthorityManager(user_obj=user)
        if not valid_res.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限查看"
            return JsonResponse(back_dic)

        """main content of this method"""
        try:
            para = json.loads(request.body.decode())
            edit_type = para["type"]
        except:
            back_dic["code"] = 10100
            back_dic["msg"] = "数据传输异常，请检查传递内容/方法"
            return JsonResponse(back_dic)

        if edit_type is "0":
            is_exist = classInfo.objects.using("db_cert").filter(class_id=para["class_id"])
            if is_exist.exists():
                this_class = is_exist.first()
                this_class.delete()
                back_dic["code"] = 1000
                back_dic["msg"] = "该班级已删除"
                return JsonResponse(back_dic)
            else:
                back_dic["code"] = 10200
                back_dic["msg"] = "无法删除该班级，请重试"
                return JsonResponse(back_dic)
        elif edit_type in ["1", "2"]:
            '''是新增或是修改，需查重、查存在性、校验数据合法性'''
            valid_res = validation.class_is_valid(para)
            if valid_res["code"] == 1000:
                '''数据校验通过'''
                if edit_type is "1":
                    '''班级新增'''
                    '''班级是否查重暂未确定，暂未查重'''
                    new_class = classInfo.objects.using("db_cert").create(
                        class_type=para["class_type"],
                        class_period=para["class_period"],
                        class_start_date=para["start_date"],
                        class_end_date=para["end_date"],
                        is_exam_exist=para["is_exam_exist"],
                        is_cert_exist=para["is_cert_exist"],
                        is_online_study_exist=para["is_online_study_exist"],
                        is_practice_exist=para["is_practice_exist"]
                    )
                    # 根据得到的日期信息更新班级状态
                    new_class.update_class_status()
                    new_class.save()
                    # 对于有笔试要求的班级，创建班级-考试关联记录
                    if new_class.is_exam_exist:
                        classExamCon.objects.using("db_cert").create(class_id=new_class)
                    back_dic["code"] = 1000
                    back_dic["msg"] = "新增班级成功"
                    return JsonResponse(back_dic)
                elif edit_type is "2":
                    this_class = classInfo.objects.using("db_cert").filter(class_id=para["class_id"])
                    if not this_class.exists():
                        back_dic["code"] = 10200
                        back_dic["msg"] = "不存在的班级，无法编辑，请重试。"
                        return JsonResponse(back_dic)
                    '''这里也没有查重，理由同上，未确定怎么查'''

                    '''修改班级信息'''
                    this_class = this_class.first()
                    this_class.class_type = para["class_type"]
                    this_class.class_period = para["class_period"]
                    this_class.class_start_date = para["start_date"]
                    this_class.class_end_date = para["end_date"]
                    this_class.is_exam_exist = para["is_exam_exist"]
                    this_class.is_cert_exist = para["is_cert_exist"]
                    this_class.is_online_study_exist = para["is_online_study_exist"]
                    this_class.is_practice_exist = para["is_practice_exist"]
                    this_class.update_class_status()
                    this_class.save()
                    back_dic["code"] = 1000
                    back_dic["msg"] = "已修改班级信息。"
                    return JsonResponse(back_dic)
            else:
                '''数据校验未通过'''
                back_dic = valid_res
                return JsonResponse(back_dic)
        elif edit_type in ["201", "202"]:
            '''查询传递内容'''
            if not para["class_id"]:
                back_dic["code"] = 10100
                back_dic["msg"] = "未检测到班级id，请检查传递内容"
                return JsonResponse(back_dic)
            '''查询存在性'''
            this_class = classInfo.objects.using("db_cert").filter(class_id=para["class_id"])
            if not this_class.exists():
                back_dic["code"] = 10200
                back_dic["msg"] = "该班级不存在"
                return JsonResponse(back_dic)

            this_class = this_class.first()
            if edit_type == "201":
                print("here")
                '''关闭班级'''
                this_class.class_status = 3
                this_class.save()
                back_dic["code"] = 1000
                back_dic["msg"] = "已关闭该班级"
                return JsonResponse(back_dic)
            elif edit_type == "202":
                '''撤销关闭'''
                this_class.update_class_status()
                this_class.save()
                back_dic["code"] = 1000
                back_dic["msg"] = "已撤销该班级的关闭状态"
                return JsonResponse(back_dic)
            else:
                back_dic["code"] = 10099
                back_dic["msg"] = "无法识别的编辑类型，请检查所发送的数据"
                return JsonResponse(back_dic)
        else:
            back_dic["code"] = 10099
            back_dic["msg"] = "无法识别的编辑类型，请检查所发送的数据"
            return JsonResponse(back_dic)

        back_dic["data"] = data
        return JsonResponse(back_dic)


class classDetailsView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""
        class_id = kwargs["class_id"]
        '''存在性检查'''
        this_class = classInfo.objects.using("db_cert").filter(class_id=class_id)
        if not this_class.exists():
            back_dic["code"] = 10200
            back_dic["msg"] = "该课程不存在"
            return JsonResponse(back_dic)

        # 用户类型检查
        data["is_staff"] = user.is_staff or user.is_superuser

        this_class = this_class.first()
        class_type = ""
        for k, v in constants.CLASS_TYPE:
            if this_class.class_type == k:
                class_type = v

        class_period = ""
        for k, v in constants.CLASS_PERIOD:
            if this_class.class_period == k:
                class_period = v

        class_status = ""
        for k, v in constants.CLASS_STATUS:
            if this_class.class_status == k:
                class_status = v

        # 班级的基本信息
        class_info = dict(
            class_type=class_type,
            class_period=class_period,
            start_date=str(this_class.class_start_date),
            end_date=str(this_class.class_end_date),
            has_exam=this_class.is_exam_exist,
            has_practice=this_class.is_practice_exist,
            has_cert=this_class.is_cert_exist,
            has_online_study=this_class.is_online_study_exist,
            class_status=class_status
        )
        data["class_info"] = class_info

        '''与该班级相关的教师'''
        teacher_list = []
        teacher_set = classTeacherCon.objects.using("db_cert").filter(class_id=class_id)
        for teacher in teacher_set:
            teacher_info = dict(
                teacher_id=teacher.teacher_id.teacher_id,
                name=teacher.teacher_id.teacher_name,
                picture=str(teacher.teacher_id.photo),
                responsibility=teacher.teacher_responsibility,
            )
            teacher_list.append(teacher_info)
        data["teacher_list"] = teacher_list

        '''与该班级关联的证书、课程'''
        course_cert_set = classCourseCertCon.objects.using("db_cert").filter(class_id=class_id)
        if not course_cert_set.exists():
            data["has_cert_and_course"] = False
        else:
            data["has_cert_and_course"] = True
            course_cert_obj = course_cert_set.first()
            '''关联的课程'''
            this_course = course_cert_obj.course_id
            course_direction = ""
            for k, v in constants.COURSE_DIRECTION:
                if k == this_course.course_direction:
                    course_direction = v
            course_type = ""
            for k, v in constants.COURSE_TYPE:
                if k == this_course.course_type:
                    course_type = v
            dic = dict(
                course_id=this_course.course_id,
                course_name=this_course.course_name,
                course_direction=course_direction,
                course_type=course_type,
                course_price=this_course.course_price,
                course_true_price=this_course.course_true_price,
                ads_picture=str(this_course.ads_picture),
            )
            data["related_course"] = dic

            '''关联的证书'''
            this_cert = course_cert_obj.cert_id
            cert_level = ""
            for k, v in constants.CERTIFICATION_LEVEL:
                if k == this_cert.cert_level:
                    cert_level = v

            testing_way = ""
            for k, v in constants.TESTING_WAYS:
                if k == this_cert.testing_way:
                    testing_way = v

            cert_dic = dict(
                cert_id=this_cert.cert_id,
                cert_name=this_cert.cert_name,
                cert_level=cert_level,
                issuing_unit=this_cert.issuing_unit,
                cert_introduction=this_cert.cert_introduction,
                testing_way=testing_way,
                aim_people=this_cert.aim_people,
                cor_positions=this_cert.cor_positions,
                expiry_date=this_cert.expiry_date,
                cert_sample=str(this_cert.cert_sample)
            )
            data["related_cert"] = cert_dic

        """与该班级关联的考试"""
        has_related_exam = classExamCon.objects.using("db_cert").filter(class_id_id=class_id)
        if has_related_exam.exists():
            data["has_exam_related"] = True
            '''未做考试信息展示'''
            related_exam = has_related_exam.first()
            exam_id = related_exam.exam_id

        else:
            data["has_exam_related"] = False

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=user.id)
        except:
            this_student = False
        para = json.loads(request.body.decode())
        class_id = kwargs["class_id"]
        '''存在性检查'''
        this_class = classInfo.objects.using("db_cert").filter(class_id=class_id)
        if not this_class.exists():
            back_dic["code"] = 10200
            back_dic["msg"] = "该班级不存在"
            return JsonResponse(back_dic)
        this_class = this_class.first()
        """main content of this method"""

        edit_type = para["type"]
        if edit_type == "101":
            '''新增教师'''
            this_teacher = teacherInfo.objects.using("db_cert").get(teacher_id=para["teacher_id"])
            exist_already = classTeacherCon.objects.using("db_cert").filter(class_id_id=class_id, teacher_id_id=this_teacher.teacher_id)
            if exist_already.exists():
                back_dic["code"] = 10300
                back_dic["msg"] = "该教师已关联过该班级，无法重复关联"
                return JsonResponse(back_dic)
            classTeacherCon.objects.using("db_cert").create(class_id_id=class_id, teacher_id_id=this_teacher.teacher_id,
                                                            teacher_responsibility=para["responsibility"])
            back_dic["code"] = 1000
            back_dic["msg"] = "为该班级新增教师成功"
            return JsonResponse(back_dic)
        elif edit_type == "100":
            '''删除教师'''
            try:
                this_con = classTeacherCon.objects.using("db_cert").get(teacher_id_id=para["teacher_id"],
                                                                        class_id_id=class_id)
            except:
                back_dic["code"] = 10200
                back_dic["msg"] = "该教师未参与该班级，请重试"
                return JsonResponse(back_dic)
            this_con.delete()
            back_dic["code"] = 1000
            back_dic["msg"] = "已移除教师"
            return JsonResponse(back_dic)
        elif edit_type == "201":
            '''新增关联证书和课程'''
            this_con = classCourseCertCon.objects.using("db_cert").filter(class_id=class_id)
            if this_con.exists():
                '''已存在关联应报错'''
                back_dic["code"] = 10300
                back_dic["msg"] = "该班级关联已存在，请重试"
                return JsonResponse(back_dic)
            new_con = classCourseCertCon.objects.using("db_cert").create(class_id_id=class_id,
                                                                         cert_id_id=para["cert_id"],
                                                                         course_id_id=para["course_id"])
            back_dic["code"] = 1000
            back_dic["msg"] = "已关联"
            return JsonResponse(back_dic)
        elif edit_type == "202":
            '''修改关联'''
            this_con = classCourseCertCon.objects.using("db_cert").filter(class_id=class_id)
            if not this_con.exists():
                '''不存在关联应报错'''
                back_dic["code"] = 10200
                back_dic["msg"] = "该班级关联不存在，无法修改"
                return JsonResponse(back_dic)
            this_con = this_con.first()
            this_con.cert_id_id = para["cert_id"]
            this_con.course_id_id = para["course_id"]
            this_con.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "已修改"
            return JsonResponse(back_dic)
        elif edit_type == "200":
            '''解除关联'''
            this_con = classCourseCertCon.objects.using("db_cert").filter(class_id_id=class_id)
            if not this_con.exists():
                '''不存在关联应报错'''
                back_dic["code"] = 10200
                back_dic["msg"] = "该班级关联不存在，无法删除"
                return JsonResponse(back_dic)
            this_con = this_con.first()
            this_con.delete()
            back_dic["code"] = 1000
            back_dic["msg"] = "已删除"
            return JsonResponse(back_dic)
        elif edit_type == "301":
            '''学员报名'''
            # 新增学员-班级con
            student_id = user.id
            '''重复报名检查'''
            is_exist = classStudentCon.objects.using("db_cert").filter(class_id_id=class_id, student_id_id=student_id)
            if is_exist.exists():
                back_dic["code"] = 10300
                back_dic["msg"] = "您已报名该课程，无法重复报名"
                return JsonResponse(back_dic)
            # 执行报名
            new_joined = classStudentCon.objects.using("db_cert").create(class_id_id=class_id, student_id_id=student_id)
            # 根据班级设置检查更新初始进度
            if this_class.is_online_study_exist:
                new_joined.study_progress = 0
                onlineStudyRecords.objects.using("db_cert").create(class_student=new_joined)
            if this_class.is_practice_exist:
                new_joined.practice_progress = 0
                practiceRecords.objects.using("db_cert").create(class_student=new_joined)
            if this_class.is_exam_exist:
                new_joined.exam_progress = 0
                this_exam_con = classExamCon.objects.using("db_cert").filter(class_id_id=class_id)
                this_exam_con = this_exam_con.first()
                examRecords.objects.using("db_cert").create(class_exam_id_id=this_exam_con.class_exam_id, student_id_id=student_id)
            if this_class.is_cert_exist:
                new_joined.cert_progress = 0
            new_joined.save()

            back_dic["code"] = 1000
            back_dic["msg"] = "报名成功"
            return JsonResponse(back_dic)
        elif edit_type == "300":
            '''学员取消报名'''
            try:
                is_joined = classStudentCon.objects.using("db_cert").get(class_id=this_class, student_id_id=user.id)
            except:
                back_dic["code"] = 10200
                back_dic["msg"] = "无法取消报名，可能是由于您并未报名，请刷新重试"
                return JsonResponse(back_dic)
            '''检查班级状态，当为1进行中，2已结束时不可取消报名'''
            if this_class.class_status == 1:
                back_dic["code"] = 10001
                back_dic["msg"] = "已开课，无法取消报名"
                return JsonResponse(back_dic)
            elif this_class.class_status == 2:
                back_dic["code"] = 10001
                back_dic["msg"] = "班级已结束，无法取消报名"
                return JsonResponse(back_dic)

            # 执行取消报名
            is_joined.delete()
            # 删除考试记录，线上课记录、实训记录自动级联删除
            if this_class.is_exam_exist:
                this_class_exam_con = classExamCon.objects.using("db_cert").get(class_id_id=class_id)
                exam_record = examRecords.objects.using("db_cert").filter(class_exam_id_id=this_class_exam_con.class_exam_id,
                                                                          student_id_id=user.id)
                exam_record.delete()
            back_dic["code"] = 1000
            back_dic["msg"] = "取消报名成功"
            return JsonResponse(back_dic)
        elif edit_type == "402":
            '''修改考试关联（只有修改，新建在创建班级时创建，没有删除）'''
            try:
                this_con = classExamCon.objects.using("db_cert").get(class_id=this_class)
            except:
                back_dic["code"] = 10200
                back_dic["msg"] = "该班级不可关联考试"
                return JsonResponse(back_dic)

            if not validation.is_number(para["min_score"]):
                back_dic["code"] = 10001
                back_dic["msg"] = "请输入数字"
                return JsonResponse(back_dic)

            this_con.exam_id = para["exam_id"]
            this_con.min_score = para["min_score"]
            this_con.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "已绑定考试"
            return JsonResponse(back_dic)
        elif edit_type == "900":
            '''学员咨询，需要一个代发邮箱（settings中设置）和一个接收邮箱'''
            sender = settings.EMAIL_HOST_USER
            receiver_list = ["receiver_mail"]
            reply_phone = para["phone"]
            if reply_phone in [None, ""] and not this_student:
                reply_phone = this_student.phone_number
            question = para["question"]
            message = "咨询内容【" + question + "】, 回访电话【" + reply_phone + "】。"
            res = send_mail(subject="新的学员报名咨询！", message=message, from_email=sender, recipient_list=receiver_list)
            if res == 1:
                back_dic["code"] = 1000
                back_dic["msg"] = "发送成功，请等待客服回访"
                return JsonResponse(back_dic)
            else:
                back_dic["code"] = 10001
                back_dic["msg"] = "发送咨询信息失败，请重试"
                return JsonResponse(back_dic)
        back_dic["data"] = data
        return JsonResponse(back_dic)


class examListSearch(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        para = json.loads(request.body.decode())
        """main content of this method"""
        '''权限检查'''
        MANAGER = AuthorityManager(user_obj=user)
        if not MANAGER.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限访问"
            return JsonResponse(back_dic)

        api_url = "https://api.xiaoe-tech.com/xe.examination.list.get/1.0.0"
        search_content = para["search_content"]
        page_index = 1
        continue_flag = True
        client = XiaoeClient()
        exam_list = []
        while continue_flag:
            params = {
                "search_content": search_content,
                "page_index": page_index,
                "page_size": 5
            }
            res = client.request("post", api_url, params)
            sub_exam_list = res["data"]["exam_list"]
            exam_list.extend(sub_exam_list)
            if len(exam_list) == res["data"]["total_count"]:
                # 跳出循环
                continue_flag = False
            else:
                # 翻页，继续循环
                page_index += 1
        """res结构示例
        res = {"code": 0,
               "msg": "操作成功",
               "data": {
                   "exam_list": [
                       {"app_id": "appHTPxaGTp7928", "comment_count": 1, "commit_count": 1,
                        "created_at": "2022-03-08 15:14:08",
                        "id": "ex_62270240863d5_wdX6sx18", "name": "考试测试20220308", "participate_count": 1, "state": 1,
                        "total_question": 2, "total_score": 4}],
                   "total_count": 8}}
        """
        '''制作考试列表'''
        required_keys = ["id", "name", "created_at"]
        exam_info_list = []
        for each_exam in exam_list:
            exam_info = {key: val for key, val in each_exam.items() if key in required_keys}
            exam_info["operation"] = 0 if each_exam["state"] in [2, 3] else 1
            exam_info_list.append(exam_info)
        data["exam_info_list"] = exam_info_list
        # data["exam_list"] = exam_list
        back_dic["data"] = data
        return JsonResponse(back_dic)


class studentDetailsView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""
        student_id = self.kwargs["student_id"]
        if (not user.is_staff) and (user.id != student_id):
            back_dic["code"] = 10400
            back_dic["msg"] = "你无法查看其他学员的信息"
            return JsonResponse(back_dic)

        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=student_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "该学生不存在，请检查url"
            return JsonResponse(back_dic)

        # 已经完成注册（当然）
        has_signed = True

        # 已完成小鹅通认证
        if this_student.is_valid == 1:
            has_certificated = True
        else:
            has_certificated = False

        # 已报名
        """需要检查class-student表"""
        joined_list = classStudentCon.objects.using("db_cert").filter(student_id_id=student_id)
        if joined_list.exists():
            has_joined = True
        else:
            has_joined = False

        # 报名列表
        class_joined_list = []
        if has_joined:
            for each_joined in joined_list:
                info = dict()
                info["class_id"] = each_joined.class_id_id
                class_student_con_id = each_joined.class_student_id
                class_status = ""
                for k, v in constants.CLASS_STATUS:
                    if k == each_joined.class_id.class_status:
                        class_status = v

                info["class_info"] = dict(
                    start_date=each_joined.class_id.class_start_date,
                    end_date=each_joined.class_id.class_end_date,
                    class_status=class_status,
                )

                study_progress = ""
                exam_progress = ""
                cert_progress = ""
                practice_progress = ""
                for k, v in constants.CERT_PROGRESS_OPTIONS:
                    if each_joined.practice_progress == k:
                        practice_progress = v
                    if each_joined.cert_progress == k:
                        cert_progress = v
                    if each_joined.exam_progress == k:
                        exam_progress = v
                    if each_joined.study_progress == k:
                        study_progress = v

                info["study_progress"] = study_progress
                info["practice_progress"] = practice_progress
                info["exam_progress"] = exam_progress
                info["cert_progress"] = cert_progress
                info["class_details_url"] = "cert/" + str(each_joined.class_id_id) + "/class_details/"

                class_joined_list.append(info)

        data["has_signed"] = has_signed
        data["has_certificated"] = has_certificated
        data["has_joined"] = has_joined

        data["joined_list"] = class_joined_list

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        student_id = self.kwargs["student_id"]
        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=student_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "该学生不存在，请检查url"
            return JsonResponse(back_dic)

        para = json.loads(request.body.decode())
        edit_type = para["type"]

        """main content of this method"""

        back_dic["data"] = data
        return JsonResponse(back_dic)


class classStudentsManagementView(View):
    admin_request = True

    def validation_check(self, user_object):
        if self.admin_request:
            if not (user_object.is_staff or user_object.is_superuser):
                return False
        return True

    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        """main content of this method"""
        class_id = self.kwargs["class_id"]
        '''管理员检查'''
        if not self.validation_check(user):
            back_dic["code"] = 10400
            back_dic["msg"] = "用户无相关权限"
            return JsonResponse(back_dic)
        '''制作学员列表'''
        students_queryset = classStudentCon.objects.using("db_cert").filter(class_id_id=class_id)
        data["students_count"] = students_queryset.count()
        students_list = []
        for student in students_queryset:
            common_info = dict(
                student_id=student.student_id.student_id,
                student_name=student.student_id.student_name,
                phone=student.student_id.phone_number,
                id_number=student.student_id.id_number,
                wechat=student.student_id.wechat_openid,
                sex=student.student_id.sex,
                is_valid=student.student_id.is_valid,
                exam_progress=student.exam_progress,
                cert_progress=student.cert_progress,
                practice_progress=student.practice_progress,
                online_study_progress=student.study_progress,
            )
            students_list.append(common_info)
        data["students_list"] = students_list

        # 对照映射
        validation_map = []
        for idx, label in constants.XET_VALIDATION:
            validation_map.append(dict(idx=idx, label=label))
        data["validation_map"] = validation_map

        progress_map = []
        for idx, label in constants.CERT_PROGRESS_OPTIONS:
            progress_map.append(dict(idx=idx, label=label))
        data["progress_map"] = progress_map

        sex_map = []
        for idx, label in constants.SEX_CHOICE:
            sex_map.append(dict(idx=idx, label=label))
        data["sex_map"] = sex_map

        back_dic["data"] = data
        return JsonResponse(back_dic)

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        if not self.validation_check(user):
            back_dic["code"] = 10400
            back_dic["msg"] = "用户无相关权限"
            return JsonResponse(back_dic)

        students_queryset = classStudentCon.objects.using("db_cert").filter(class_id_id=self.kwargs["class_id"])
        para = json.loads(request.body.decode())
        """main content of this method"""
        """
            100/101/102/103——修改进度信息：状态不为2，可以修改状态为0，可以改为1；状态为1，可以改为0
            200——修改认证信息：状态为3，可以改为1；其他情况下，不可以再改
            300——删除学员
            301——新增学员（暂未做）
        """
        edit_type = para["type"]
        if edit_type == "100":
            '''线上学习进度'''
            this_student_query = students_queryset.get(student_id_id=para["student_id"])
            if this_student_query.study_progress == 0:
                this_student_query.study_progress = 1
            elif this_student_query.study_progress == 1:
                this_student_query.study_progress = 0
            else:
                back_dic["code"] = 10400
                back_dic["msg"] = "状态不可改，请重试"
                return JsonResponse(back_dic)
            this_student_query.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "修改成功"
            return JsonResponse(back_dic)
        elif edit_type == "101":
            '''实训进度'''
            this_student_query = students_queryset.get(student_id_id=para["student_id"])
            if this_student_query.practice_progress == 0:
                this_student_query.practice_progress = 1
            elif this_student_query.practice_progress == 1:
                this_student_query.practice_progress = 0
            else:
                back_dic["code"] = 10400
                back_dic["msg"] = "状态不可改，请重试"
                return JsonResponse(back_dic)
            this_student_query.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "修改成功"
            return JsonResponse(back_dic)
        elif edit_type == "102":
            '''考试进度'''
            this_student_query = students_queryset.get(student_id_id=para["student_id"])
            if this_student_query.exam_progress == 0:
                this_student_query.exam_progress = 1
            elif this_student_query.exam_progress == 1:
                this_student_query.exam_progress = 0
            else:
                back_dic["code"] = 10400
                back_dic["msg"] = "状态不可改，请重试"
                return JsonResponse(back_dic)
            this_student_query.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "修改成功"
            return JsonResponse(back_dic)
        elif edit_type == "103":
            '''证书进度'''
            this_student_query = students_queryset.get(student_id_id=para["student_id"])
            if this_student_query.cert_progress == 0:
                this_student_query.cert_progress = 1
            elif this_student_query.cert_progress == 1:
                this_student_query.cert_progress = 0
            else:
                back_dic["code"] = 10400
                back_dic["msg"] = "状态不可改，请重试"
                return JsonResponse(back_dic)
            this_student_query.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "修改成功"
            return JsonResponse(back_dic)
        elif edit_type == "200":
            '''检查是否可改'''
            this_student = studentInfo.objects.using("db_cert").get(student_id=para["student_id"])
            if this_student.is_valid == 3:
                this_student.is_valid = 1
            else:
                back_dic["code"] = 10400
                back_dic["msg"] = "认证状态不可改，请重试"
                return JsonResponse(back_dic)
            '''修改认证信息'''
            this_student.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "修改成功"
            return JsonResponse(back_dic)
        elif edit_type == "300":
            '''删除学员'''
            this_student_query = students_queryset.get(student_id_id=para["student_id"])
            this_student_query.delete()
            back_dic["code"] = 1000
            back_dic["msg"] = "本班级内删除学员成功"
            return JsonResponse(back_dic)
        back_dic["data"] = data
        return JsonResponse(back_dic)


class updateOnlineStudyRecordsByHand(View):
    def get(self, request, *args, **kwargs):
        """
        手动更新线上课更新失败的记录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        MANAGER = AuthorityManager(user_obj=user)
        if not MANAGER.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限访问"
            return JsonResponse(back_dic)

        """main content of this method"""
        class_id = self.kwargs["class_id"]
        para = json.loads(request.body.decode())
        failed_date = para["date"]

        res = update_online_study_progress_by_hand(class_id, failed_date)
        back_dic = res

        return JsonResponse(back_dic)


# 客服咨询
class CustomerServiceConsultation(View):
    def post(self, request):
        # 身份令牌检测
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        # 配置数据返回格式
        back_dic = dict(code=1000, msg="", data=dict())
        para = json.loads(request.body.decode())
        number = para['number']
        text = para['text']
        message = f'联系电话：{number}\n' \
                  f'咨询内容：{text}'
        # 邮箱账号
        username = 'service@shiyenet.com.cn'
        # 邮箱授权码
        authorization_code = 'Hrjd332211'
        # 构建一个邮箱服务对象
        uuid = uuid4()
        server = zmail.server(username, authorization_code)
        # 邮件主体
        mail_body = {
            'subject': f'客服咨询(编号：{uuid})',
            'content_text': message,  # 纯文本或者HTML内容
        }
        # 收件人
        mail_to = 'talent@shiyenet.com.cn'
        try:
            # 发送邮件
            server.send_mail(mail_to, mail_body)
            print("发送成功")
        except Exception as e:
            print(e)
            print("发送失败")
        return JsonResponse(back_dic)


# 学生考试信息更新（通过考试id，接第三方平台返回数据更新）
'''
    1:接收班级id
    2:通过班级id查出所有的考试id
    3:通过考试id接第三方平台拿数据
    4:拿出该班级所有的学生信息
    5:将每个考试id查出来的学生与这进行比对，更新数据库
'''


class StudentExamUpdate(View):
    def post(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="", data=dict())
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        # 权限校验
        manager = AuthorityManager(user_obj=user)
        if not manager.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限访问"
            return JsonResponse(back_dic)
        # 请求参数
        para = json.loads(request.body.decode())
        api_url = "https://api.xiaoe-tech.com/xe.examination.result.list/1.0.0"
        class_id = para["class_id"]
        # 通过班级id,查找出考试id
        class_exam = classExamCon.objects.using('db_cert').filter(class_id=class_id).first()
        if not class_exam:
            back_dic["code"] = 10003
            back_dic["msg"] = "班级暂无考试！"
            return JsonResponse(back_dic)
        else:
            print(class_exam.class_exam_id)
            print(class_exam.exam_id)
            exam_id = class_exam.exam_id
            # 访问小鹅通获取数据
            page_index = 1
            continue_flag = True
            client = XiaoeClient()
            exam_list = []
            while continue_flag:
                params = {
                    "exam_id": exam_id,
                    "page_index": page_index,
                    "page_size": 5
                }
                res = client.request("post", api_url, params)
                sub_exam_list = res["data"]["list"]
                exam_list.extend(sub_exam_list)
                if len(exam_list) == res["data"]["total"]:
                    # 跳出循环
                    continue_flag = False
                else:
                    # 翻页，继续循环
                    page_index += 1

            # 通过班级id增加数据更新时间表
            now_time = time.strftime('%Y-%m-%d', time.localtime())
            # 往数据更新时间表中插入数据
            try:
                udr = updateDateRecords()
                udr.class_id_id = class_id
                udr.exam_update_date = now_time
                udr.save(using='db_cert')
            except Exception as e:
                back_dic["code"] = 10002
                back_dic["msg"] = '数据新增失败！'
                return JsonResponse(back_dic)
            # 通过班级id查找该班级学生
            students = classStudentCon.objects.using('db_cert').filter(class_id=class_id).all()
            # 将班级中的学生筛出来
            student_list = {}
            for j in range(len(students)):
                # 因此此时的学生id和学生在小鹅通中的学生id不一致所以需要转变
                stu = studentInfo.objects.using('db_cert').filter(student_id=students[j].student_id_id).first()
                # 防止列表学生重复
                if stu.xet_id not in student_list.keys():
                    student_list[stu.xet_id] = students[j].student_id_id

            # 开始往学生成绩表插入数据
            for i in range(len(exam_list)):
                # 判断学生是否在考试涉及到的班级的学生列表中
                if exam_list[i]['user_id'] in student_list.keys():
                    # 首先判断一下，这条数据是不是已经插入了，如果没有则插入，条件为：班级考试id,和学生id
                    datas = examRecords.objects.using('db_cert') \
                        .filter(class_exam_id_id=int(class_exam.class_exam_id),
                                student_id_id=int(student_list[exam_list[i]['user_id']])).first()
                    if datas:
                        continue
                    else:
                        # 因为考试结果表中的班级考试id不是考试的id，因此需要进行查找转换，上边的拼接就是为了此处不再进行再次查询
                        try:
                            examRecords.objects.using('db_cert') \
                                .create(class_exam_id_id=int(class_exam.class_exam_id),
                                        student_id_id=int(student_list[exam_list[i]['user_id']]),
                                        join_time=exam_list[i]['commit_time'],
                                        exam_score=exam_list[i]['score'])
                        except Exception as e:
                            back_dic["code"] = 10002
                            back_dic["msg"] = '数据新增失败！'
                            return JsonResponse(back_dic)
            return JsonResponse(back_dic)


def default_sentences(self, request, *args, **kwargs):
    session_dict = session_exist(request)
    if session_dict["code"] != 1000:
        return JsonResponse(session_dict)
    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    para = json.loads(request.body.decode())
    """main content of this method"""

    back_dic["data"] = data
    return JsonResponse(back_dic)
