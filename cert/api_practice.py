"""
@file_intro: 实训平台接口：1.学员认证接口； 2.实训入口； 3.更新实训记录
@creation_date: 20220323
@update_date:
@author:Yaqi Meng
"""
from cert.models import practiceRecords, classInfo, classStudentCon, studentInfo
from user.models import User
from django.views.generic.base import View
from cert.views import session_exist
from django.http import JsonResponse
from django.contrib.sessions.models import Session
import json
import requests
import datetime


class startPractice(View):
    PRACTICE_URL = ""

    def get(self, request, *args, **kwargs):
        """
        发送param和跳转链接给前端
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

        # para = json.loads(request.body.decode())
        class_id = self.kwargs["class_id"]
        """main content of this method"""
        try:
            this_student = studentInfo.objects.using("db_cert").get(student_id=user.id)
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "未注册为学员"
            return JsonResponse(back_dic)

        student_id = this_student.student_id
        class_student_con = classStudentCon.objects.using("db_cert").get(class_id_id=class_id, student_id=student_id)
        this_practice = practiceRecords.objects.using("db_cert").get(class_student=class_student_con)
        if this_practice.available_times <= 0:
            back_dic["code"] = 10001
            back_dic["msg"] = "没有剩余实训次数！"
            return JsonResponse(back_dic)
        param = {
            "student_id": class_student_con.class_student_id,
            "practice_id": this_practice.practice_id
        }
        data["url"] = self.PRACTICE_URL
        data["params"] = param
        back_dic["data"] = data
        return JsonResponse(back_dic)


class studentValidationCheck(View):
    def get(self, request, *args, **kwargs):
        """
        1.检查实训剩余次数；
        2.检查学生是否对应实训的学生。
        :return:
        """
        back_dic = dict(code=1000, msg="")
        # para = {
        #     "student_id": None,
        #     "practice_id": None
        # }
        para = json.loads(request.body.decode())
        '''检查实训记录是否存在'''
        try:
            this_practice = practiceRecords.objects.using("db_cert").get(practice_id=para["practice_id"])
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "不存在的实训记录"
            return JsonResponse(back_dic)
        '''检查实训次数是否合法'''
        if this_practice.available_times <= 0:
            back_dic["code"] = 10400
            back_dic["msg"] = "无剩余实训次数！"
            return JsonResponse(back_dic)
        '''检查实训id和学生是否匹配'''
        if this_practice.class_student.class_student_id != para["student_id"]:
            back_dic["code"] = 10400
            back_dic["msg"] = "无权参与其他学员的实训！"
            return JsonResponse(back_dic)

        back_dic["msg"] = "验证通过！"
        return JsonResponse(back_dic)


class updatePracticeRecord(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg="")
        para = json.loads(request.body.decode())
        '''
        para={
            "student_id",
            "practice_id",
            "data":{
                "score",
            }
        }
        '''
        try:
            this_practice = practiceRecords.objects.using("db_cert").get(practice_id=para["practice_id"])
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "实训记录不存在"
            return JsonResponse(back_dic)

        if this_practice.available_times <= 0:
            back_dic["code"] = 10400
            back_dic["msg"] = "无剩余实训次数!"
            return JsonResponse(back_dic)

        if not this_practice.practice_score or (para["data"]["score"] >= this_practice.practice_score):
            this_practice.practice_score = para["data"]["score"]
            this_practice.latest_update_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
            this_practice.available_times -= 1
            this_practice.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "最高实训成绩已更新"
            return JsonResponse(back_dic)
        else:
            this_practice.available_times -= 1
            this_practice.save()
            back_dic["code"] = 1000
            back_dic["msg"] = "实训完成，最高实训成绩未更新"
            return JsonResponse(back_dic)

