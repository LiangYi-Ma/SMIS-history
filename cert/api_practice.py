"""
@file_intro: 实训平台接口：1.学员认证接口； 2.实训入口； 3.更新实训记录； 4.查询实训过程数据； 5.检查教师合法性
@creation_date: 20220323
@update_date: 20220507
@author:Yaqi Meng
"""
from cert.models import practiceRecords, classInfo, classStudentCon, studentInfo, teacherInfo, PracticeProcessData
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
            this_practice = practiceRecords.objects.using("db_cert").get(class_student_id=para["student_id"])
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "no practice record!"
            return JsonResponse(back_dic)
        '''检查实训次数是否合法'''
        if this_practice.available_times <= 0:
            back_dic["code"] = 10400
            back_dic["msg"] = "not enough available times！"
            return JsonResponse(back_dic)
        # '''检查实训id和学生是否匹配'''
        # if this_practice.class_student.class_student_id != para["student_id"]:
        #     back_dic["code"] = 10400
        #     back_dic["msg"] = "无权参与其他学员的实训！"
        #     return JsonResponse(back_dic)

        back_dic["msg"] = "success！"
        return JsonResponse(back_dic)


class updatePracticeRecord(View):
    """更新学员实训过程数据、实训结果"""
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg="")
        para = json.loads(request.body.decode())
        '''
        para={
            "id",//学生ID
            "data":{
                ...//过程数据
                "score": 90
            }
        }
        '''
        try:
            this_practice = practiceRecords.objects.using("db_cert").get(class_student_id=para["id"])
        except:
            back_dic["code"] = 10200
            back_dic["msg"] = "student not exist"
            return JsonResponse(back_dic)

        if this_practice.available_times <= 0:
            back_dic["code"] = 10400
            back_dic["msg"] = "not enough available times"
            return JsonResponse(back_dic)

        class_student_id = para["id"]
        saved_process_data = PracticeProcessData.objects.using("db_cert").filter(class_student_id=class_student_id)
        if saved_process_data.count() >= 5:
            data_obj = saved_process_data.order_by("upload_time").first()
        else:
            data_obj = PracticeProcessData.objects.using("db_cert").create(class_student_id=class_student_id)
        data_obj.process_data = para["data"]
        data_obj.save()

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


class teacherValidationCheck(View):
    """
    检查教师的合法性
    1.拿到教师姓名、手机号；
    2.匹配数据库；
        3.存在教师。返回其所带班级(id, 班级名)，班级内学员姓名（id, 姓名）；
        "data": {
            "class_total" = 2,
            "class_data": [{
                "class_name": "技能提升班（01）",
                "total_student": 3,
                "student_data": [{
                    "student_id": 1,
                    "student_name": "任嘉明"
                },{
                    "student_id": 2,
                    "student_name": "任嘉明"
                },{
                    "student_id": 3,
                    "student_name": "任嘉明"
                }]
            }]
        }
        4.不存在教师。返回结果
    """
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg="")
        para = json.loads(request.body.decode())
        """
        para = {"teacher_name": "李世民", "phone_number": "13848838272"}
        """
        teacher_name = para["teacher_name"]
        phone = para["phone_number"]
        teacher_query_set = teacherInfo.objects.using("db_cert").filter(teacher_name=teacher_name, phone_number=phone)
        if not teacher_query_set.exists():
            back_dic["code"] = 10200
            back_dic["msg"] = "object(s) not exist"
            return JsonResponse(back_dic)

        teacher_obj = teacher_query_set.first()
        class_set = classInfo.objects.using("db_cert").filter(classteachercon__teacher_id__teacher_id=teacher_obj.teacher_id)
        data = dict(total_class=class_set.count(), data_class=[])
        data_class = []
        for class_obj in class_set:
            students = classStudentCon.objects.using("db_cert").filter(class_id_id=class_obj.class_id)
            class_data_dict = dict(
                class_id=class_obj.class_id,
                class_name=class_obj.class_name,
                total_student=students.count()
            )
            students_data = []
            for student_obj in students:
                student_dict = dict(
                    student_id=student_obj.class_student_id,
                    student_name=student_obj.student_id.student_name
                )
                students_data.append(student_dict)

            class_data_dict["data_students"] = students_data
            data_class.append(class_data_dict)

            data["data_class"] = data_class
        back_dic["data"] = data
        return JsonResponse(back_dic)


class getPracticeProgressData(View):
    """
    查询学生实训过程数据
    1.接收学生ID
    2.验证学生是否存在在相应班级（即接收class_student_id是否存在）
        3.存在的话。返回学生ID，实训数据存在总数，对于每条实训数据返回实训过程数据，提交时间；
        4.不存在的话。返回报告。
    """
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg="")
        student_id = self.kwargs["student_id"]
        is_exist = classStudentCon.objects.using("db_cert").filter(class_student_id=student_id)
        if not is_exist.exists():
            back_dic["code"] = 10200
            back_dic["msg"] = "object(s) not exist"
            return JsonResponse(back_dic)

        practice_records = PracticeProcessData.objects.using("db_cert").filter(class_student_id=student_id).order_by("-upload_time")
        res = dict(
            total=practice_records.count(),
            id=student_id,
            data=[]
        )
        for practice_obj in practice_records:
            process_dict = dict(
                process_data=practice_obj.process_data,
                upload_time=str(practice_obj.upload_time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            res["data"].append(process_dict)

        return JsonResponse(res)
