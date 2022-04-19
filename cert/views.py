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
from SMIS.validation import session_exist
from SMIS.data_utils import Utils


# Create your views here.


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
            # 班级的基本信息
            class_info = dict(
                class_id=each_class.class_id,
                class_name=each_class.class_name,
                class_type=each_class.class_type,
                class_period=each_class.class_period,
                start_date=str(each_class.class_start_date),
                end_date=str(each_class.class_end_date),
                has_exam=each_class.is_exam_exist,
                has_practice=each_class.is_practice_exist,
                has_cert=each_class.is_cert_exist,
                has_online_study=each_class.is_online_study_exist,
                class_status=each_class.class_status
            )
            class_not_closed_list.append(class_info)
        data["class_not_closed"] = class_not_closed_list

        '''关闭状态的班级'''
        class_closed = classInfo.objects.using("db_cert").filter(class_status=3)
        class_closed_list = []
        for each_class in class_closed:
            # 班级的基本信息
            class_info = dict(
                class_id=each_class.class_id,
                class_name=each_class.class_name,
                class_type=each_class.class_type,
                class_period=each_class.class_period,
                start_date=str(each_class.class_start_date),
                end_date=str(each_class.class_end_date),
                has_exam=each_class.is_exam_exist,
                has_practice=each_class.is_practice_exist,
                has_cert=each_class.is_cert_exist,
                has_online_study=each_class.is_online_study_exist,
                class_status=each_class.class_status
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
                        class_name=para["class_name"],
                        class_type=para["class_type"],
                        class_period=para["class_period"],
                        class_start_date=para["start_date"],
                        class_end_date=para["end_date"],
                        is_exam_exist=para["is_exam_exist"],
                        is_cert_exist=para["is_cert_exist"],
                        is_online_study_exist=para["is_online_study_exist"],
                        is_practice_exist=para["is_practice_exist"]
                    )
                    # 根据属性保存实训、线上课达标标准
                    if new_class.is_practice_exist:
                        new_class.min_practice_score = para["min_practice_score"]
                    if new_class.is_online_study_exist:
                        new_class.min_study_time = para["min_study_time"]
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
                    '''班级是否查重暂未确定，暂未查重'''

                    '''修改班级信息'''
                    this_class = this_class.first()
                    this_class.class_name = para["class_name"]
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

                    # 同步修改班级-学生连接的进度状态
                    class_student_cons = classStudentCon.objects.using("db_cert").filter(class_id=this_class)
                    for con in class_student_cons:
                        con.updateOther2Closed()
                        con.save()

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
            back_dic["msg"] = "该班级不存在"
            return JsonResponse(back_dic)

        # 用户类型检查
        data["is_staff"] = user.is_staff or user.is_superuser

        this_class = this_class.first()

        # 班级的基本信息
        class_info = dict(
            class_name=this_class.class_name,
            class_type=this_class.class_type,
            class_period=this_class.class_period,
            start_date=str(this_class.class_start_date),
            end_date=str(this_class.class_end_date),
            has_exam=this_class.is_exam_exist,
            has_practice=this_class.is_practice_exist,
            has_cert=this_class.is_cert_exist,
            has_online_study=this_class.is_online_study_exist,
            class_status=this_class.class_status
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

            dic = dict(
                course_id=this_course.course_id,
                course_name=this_course.course_name,
                course_direction=this_course.course_direction,
                course_type=this_course.course_type,
                course_price=this_course.course_price,
                course_true_price=this_course.course_true_price,
                ads_picture=str(this_course.ads_picture),
            )
            data["related_course"] = dic

            '''关联的证书'''
            this_cert = course_cert_obj.cert_id

            cert_dic = dict(
                cert_id=this_cert.cert_id,
                cert_name=this_cert.cert_name,
                cert_level=this_cert.cert_level,
                issuing_unit=this_cert.issuing_unit,
                cert_introduction=this_cert.cert_introduction,
                testing_way=this_cert.testing_way,
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
            #     在小鹅通接口拿考试详细信息，封装给data中返回前端
            api_url = 'https://api.xiaoe-tech.com/xe.examination.detail.get/1.0.0'
            client = XiaoeClient()
            params = {
                "id": exam_id
            }
            res = client.request("post", api_url, params)
            exam_list = {}
            if not res['data']:
                data['exam_info'] = []
            else:
                result = ['name', 'total_question', 'total_score', 'exam_time', 'exam_time', 'exam_end_time']
                exam_infos = res['data']['exam_info']
                for key in exam_infos.keys():
                    if key in result:
                        exam_list[key] = exam_infos[key]
                data['exam_info'] = exam_list
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
            exist_already = classTeacherCon.objects.using("db_cert").filter(class_id_id=class_id,
                                                                            teacher_id_id=this_teacher.teacher_id)
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
                examRecords.objects.using("db_cert").create(class_exam_id_id=this_exam_con.class_exam_id,
                                                            student_id_id=student_id)
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
                exam_record = examRecords.objects.using("db_cert").filter(
                    class_exam_id_id=this_class_exam_con.class_exam_id,
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


class studentDetailsByIDView(View):
    """
    仅限管理员访问，用学员ID查询学员详细信息
    """

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
        # 仅限管理员访问
        manager = AuthorityManager(user_obj=user)
        if not manager.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限访问"
            return JsonResponse(back_dic)

        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=student_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "该学生不存在，请检查url"
            return JsonResponse(back_dic)
        student_info = dict(
            student_id=this_student.student_id,
            name=this_student.student_name,
            phone_number=this_student.phone_number,
            wechat=this_student.wechat_openid,
            id_number=this_student.id_number,
            sex=this_student.sex
        )

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

        data["student_info"] = student_info

        data["joined_list"] = class_joined_list

        back_dic["data"] = data
        return JsonResponse(back_dic)


class studentDetailsBySessionView(View):
    """
    仅限学员自己访问，用session信息查询学员详细信息
    """

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
        student_id = user.id
        # 仅限管理员访问
        manager = AuthorityManager(user_obj=user)

        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=student_id)
        except:
            has_signed = False
            has_joined = False
            has_certificated = False
            data["has_signed"] = has_signed
            data["has_certificated"] = has_certificated
            data["has_joined"] = has_joined
            return JsonResponse(back_dic)

        student_info = dict(
            student_id=this_student.student_id,
            name=this_student.student_name,
            phone_number=this_student.phone_number,
            wechat=this_student.wechat_openid,
            id_number=this_student.id_number,
            sex=this_student.sex
        )

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

        data["student_info"] = student_info

        data["joined_list"] = class_joined_list

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
        try:
            this_class = classInfo.objects.using("db_cert").get(class_id=class_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "不存在的班级"
            return JsonResponse(back_dic)
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
            if this_class.is_exam_exist:
                class_exam = classExamCon.objects.using("db_cert").filter(class_id_id=class_id).first()
                exam_record = examRecords.objects.using("db_cert").filter(class_exam_id=class_exam,
                                                                          student_id=student.student_id).first()
                exam_tag = dict(
                    join_time=exam_record.join_time,
                    exam_score=exam_record.exam_score,
                    pass_line=class_exam.min_score,
                    is_passed=exam_record.is_passed(),
                )
                common_info["exam_tag"] = exam_tag
            if this_class.is_online_study_exist:
                study_record = onlineStudyRecords.objects.using("db_cert").filter(class_student=student).first()
                online_study_tag = dict(
                    accumulated_hour=study_record.accumulated_time,
                    lastest_hour=study_record.latest_time,
                    pass_line=this_class.min_study_time,
                    is_passed=study_record.is_passed(),
                )
                common_info["online_study_tag"] = online_study_tag
            if this_class.is_practice_exist:
                practice_record = practiceRecords.objects.using("db_cert").filter(class_student=student).first()
                practice_tag = dict(
                    practice_score=practice_record.practice_score,
                    available_times=practice_record.available_times,
                    deadline=practice_record.deadline,
                    pass_line=this_class.min_practice_score,
                    is_passed=practice_record.is_passed(),
                )
                common_info["practice_tag"] = practice_tag
            students_list.append(common_info)
        data["students_list"] = students_list

        '''更新失败时间'''
        failed_dates = []
        failed_update_date_queryset = failedUpdateRecords.objects.using("db_cert").filter(class_id_id=class_id,
                                                                                          is_updated=False)
        for failed_record in failed_update_date_queryset:
            failed_dates.append(failed_record.failed_date)
        data["failed_dates"] = failed_dates

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
        back_dic = dict(code=1000, msg="发送成功！", data=dict())
        para = json.loads(request.body.decode())
        number = para['number']
        text = para['text']
        message = f'联系电话：{number}\n' \
                  f'咨询内容：{text}'
        # 邮箱账号
        username = Utils.Customer_Service_User_name
        # 邮箱授权码
        authorization_code = Utils.Authorization_Code
        # 构建一个邮箱服务对象
        uuid = uuid4()
        server = zmail.server(username, authorization_code)
        # 邮件主体
        mail_body = {
            'subject': f'客服咨询(编号：{uuid})',
            'content_text': message,  # 纯文本或者HTML内容
        }
        # 收件人
        mail_to = Utils.Customer_Service_Mail_To
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
        back_dic = dict(code=1000, msg="数据更新成功", data=dict())
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
        print(class_id)
        # 通过班级id,查找出考试id
        class_exam = classExamCon.objects.using('db_cert').filter(class_id=class_id).first()
        if not class_exam:
            back_dic["code"] = 10003
            back_dic["msg"] = "班级暂无考试！"
            return JsonResponse(back_dic)
        else:
            exam_id = class_exam.exam_id
            # 访问小鹅通获取数据
            page_index = 1
            continue_flag = True
            client = XiaoeClient()
            exam_list = []
            print(exam_id)
            while continue_flag:
                params = {
                    "exam_id": exam_id,
                    "page_index": page_index,
                    "page_size": 5
                }
                res = client.request("post", api_url, params)
                print(res)
                if not res['data'] and page_index == 1:
                    back_dic["code"] = 10004
                    back_dic["msg"] = "小鹅通考试信息为空！"
                    return JsonResponse(back_dic)
                else:
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

            # 开始往学生成绩表更新数据
            for i in range(len(exam_list)):
                # 判断学生是否在考试涉及到的班级的学生列表中
                if exam_list[i]['user_id'] in student_list.keys():
                    # 因为考试结果表中的班级考试id不是考试的id，因此需要进行转换
                    try:
                        examRecords.objects.using('db_cert') \
                            .filter(class_exam_id_id=int(class_exam.class_exam_id),
                                    student_id_id=int(student_list[exam_list[i]['user_id']])) \
                            .update(join_time=exam_list[i]['commit_time'],
                                    exam_score=exam_list[i]['score'])
                    except Exception as e:
                        back_dic["code"] = 10002
                        back_dic["msg"] = '数据更新失败！'
                        return JsonResponse(back_dic)
            return JsonResponse(back_dic)


class checkIssuingQualificationByClassID(View):
    def check_one_student(self):
        res = False
        return res

    def get(self, request, *args, **kwargs):
        """
        1.拿到班级ID class_id
            1）检查班级是否发放证书，无关联证书则返回错误10200
        2.提取班级中的学生列表(from classStudentCon)
        3.根据班级属性检查学生的考试、线上课、实训达标情况，达标置为1；
        4.更新在学生列表中；
        5.检查是否已通过，通过则将证书状态置为1。
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

        # 权限校验
        manager = AuthorityManager(user_obj=user)
        if not manager.is_staff():
            back_dic["code"] = 10400
            back_dic["msg"] = "无权限访问"
            return JsonResponse(back_dic)

        # 1.班级id
        class_id = self.kwargs["class_id"]
        try:
            this_class = classInfo.objects.using("db_cert").get(class_id=class_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "不存在的班级"
            return JsonResponse(back_dic)

        if not this_class.is_cert_exist:
            back_dic["code"] = 10200
            back_dic["msg"] = "班级不涉及证书发放！"
            return JsonResponse(back_dic)

        # para = json.loads(request.body.decode())
        """main content of this method"""
        # 2.学生列表
        student_queryset = classStudentCon.objects.using("db_cert").filter(class_id_id=class_id)
        for student in student_queryset:
            student.updateCertStatus()
            student.save()

        back_dic["msg"] = "更新成功！"

        back_dic["data"] = data
        return JsonResponse(back_dic)


# 主页
class HomeCourseCertification(View):
    # 课程列表，证书列表，即将开班
    # 不需要session检测
    def get(self, request):
        back_dic = dict(code=1000, msg="数据查询成功！", data=dict())
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            back_dic["data"]["is_login"] = False
            back_dic["data"]["is_staff"] = None
        else:
            back_dic["data"]["is_login"] = True

            session_key = request.META.get("HTTP_AUTHORIZATION")
            session = Session.objects.get(session_key=session_key)
            uid = session.get_decoded().get('_auth_user_id')
            user = User.objects.get(pk=uid)

            manager = AuthorityManager(user)
            back_dic["data"]["is_staff"] = manager.is_staff()

        # 轮播图
        crs_list = [
            {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-01.jpg",
                "url": "https://apphtpxagtp7928.h5.xiaoeknow.com/p/decorate/homepage?"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-02.jpg",
                "url": "https://apphtpxagtp7928.pc.xiaoe-tech.com"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-03.jpg",
                "url": "https://wxaurl.cn/Il7kWsH4bzv"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-04.jpg",
                "url": "https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum&__biz=Mzg3NjY2NDAxMA==&scene=1&album_id=2319237584956440577&count=3#wechat_redirect"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-05.jpg",
                "url": "https://mp.weixin.qq.com/s/67pDb8_hy9dJMG4GSatU2Q"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-06.jpg",
                "url": "https://mp.weixin.qq.com/s/67pDb8_hy9dJMG4GSatU2Q"
            }, {
                "pic_path": "https://znzz.tech/static/img/sys-img/crs-cert/crs-cert-07.jpg",
                "url": "https://www.douyin.com/user/MS4wLjABAAAAXVWuIIqRFuVycS47qIyjTD1_39Hmf2fLy9X9gR3nRlo"
            }
        ]
        back_dic["data"]["crs_list"] = crs_list

        # 查找证书列表
        certification_query = certificationInfo.objects.using("db_cert").order_by('cert_name', 'cert_level').all()[:8]
        if certification_query:
            result = []
            for i in range(len(certification_query)):
                ls = dict()
                ls['cert_id'] = certification_query[i].cert_id
                ls['cert_name'] = str(certification_query[i].cert_name)
                ls['cert_sample'] = str(certification_query[i].cert_sample)
                result.append(ls)
            back_dic['data']['cert_list'] = result
        else:
            back_dic['data']['cert_list'] = []
        # 查找课程列表
        all_course = courseInfo.objects.using("db_cert").order_by("course_direction", "course_type").all()[:8]
        if all_course:
            result = []
            for i in range(len(all_course)):
                ls = {}
                ls['course_id'] = all_course[i].course_id
                ls['course_name'] = str(all_course[i].course_name)
                ls['course_price'] = str(all_course[i].course_price)
                ls['course_true_price'] = str(all_course[i].course_true_price)
                ls['ads_picture'] = str(all_course[i].ads_picture)
                result.append(ls)
            back_dic['data']['course_list'] = result
        else:
            back_dic['data']['course_list'] = []
        # 即将开班班级列表
        class_list = classInfo.objects.using("db_cert").filter(class_status=0).order_by('class_start_date').all()[:7]
        if class_list:
            result = []
            for i in range(len(class_list)):
                ls = {}
                # 在班级课程证书表查找课程和证书id
                classcoursecertcon = classCourseCertCon.objects.using("db_cert") \
                    .filter(class_id=class_list[i].class_id).first()
                if classcoursecertcon:
                    # 将证书id转化成证书名称
                    certificationinfo = certificationInfo.objects.using('db_cert').filter(
                        cert_id=classcoursecertcon.cert_id_id).first()
                    ls['cert_name'] = certificationinfo.cert_name
                    # 将课程id转化成课程名称
                    courseinfo = courseInfo.objects.using('db_cert').filter(
                        course_id=classcoursecertcon.course_id_id).first()
                    ls['course_name'] = courseinfo.course_name
                ls['class_id'] = class_list[i].class_id
                ls['class_name'] = class_list[i].class_name
                ls['class_start_date'] = str(class_list[i].class_start_date)
                ls['class_end_date'] = str(class_list[i].class_end_date)
                result.append(ls)
            back_dic['data']['class_list'] = result
        else:
            back_dic['data']['class_list'] = []
        return JsonResponse(back_dic)


class CertificationDetail(View):
    # 证书详情
    # 不进行用户身份检测,只做登陆检测
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="数据查找成功", data=dict())
        cert_id = self.kwargs["cert_id"]
        certificationinfo = certificationInfo.objects.using('db_cert').filter(cert_id=cert_id).first()
        if certificationinfo:
            back_dic['data']['cert_id'] = certificationinfo.cert_id
            back_dic['data']['cert_name'] = str(certificationinfo.cert_name)
            back_dic['data']['cert_level'] = str(certificationinfo.cert_level)
            back_dic['data']['issuing_unit'] = str(certificationinfo.issuing_unit)
            back_dic['data']['cert_introduction'] = str(certificationinfo.cert_introduction)
            back_dic['data']['testing_way'] = str(certificationinfo.testing_way)
            back_dic['data']['aim_people'] = str(certificationinfo.aim_people)
            back_dic['data']['cor_positions'] = str(certificationinfo.cor_positions)
            back_dic['data']['cert_sample'] = str(certificationinfo.cert_sample)
            back_dic['data']['expiry_date'] = str(certificationinfo.expiry_date)
        else:
            back_dic['code'] = 10005
            back_dic['msg'] = '证书信息不存在!'
        return JsonResponse(back_dic)


class CourseDetail(View):
    # 课程详情
    # 不进行用户身份检测,只做登陆检测
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="数据查找成功", data=dict())
        course_id = self.kwargs["course_id"]
        courseinfo = courseInfo.objects.using('db_cert').filter(course_id=course_id).first()
        if courseinfo:
            back_dic['data']['course_id'] = courseinfo.course_id
            back_dic['data']['course_name'] = courseinfo.course_name
            back_dic['data']['course_direction'] = courseinfo.course_direction
            back_dic['data']['course_type'] = courseinfo.course_type
            back_dic['data']['course_price'] = courseinfo.course_price
            back_dic['data']['course_true_price'] = courseinfo.course_true_price
            back_dic['data']['ads_picture'] = str(courseinfo.ads_picture)
        else:
            back_dic['code'] = 10006
            back_dic['msg'] = '课程信息不存在!'
        return JsonResponse(back_dic)


class TeacherDetail(View):
    """
    教师详情：检测登陆，不检测角色
    """

    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        back_dic = dict(code=1000, msg="数据查找成功", data=dict())
        teacher_id = self.kwargs["teacher_id"]
        try:
            this_teacher = teacherInfo.objects.using("db_cert").get(teacher_id=teacher_id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "教师不存在"
            return JsonResponse(back_dic)
        data = dict(
            teacher_id=this_teacher.teacher_id,
            name=this_teacher.teacher_name,
            phone=this_teacher.phone_number,
            wechat=this_teacher.wechat_openid,
            photo=str(this_teacher.photo),
            introduction=this_teacher.self_introduction,
            level=this_teacher.level,
            teaching_field=this_teacher.teaching_field
        )

        back_dic["data"] = data
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
