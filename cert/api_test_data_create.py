"""
@file_intro: 创建测试数据
@creation_date:
@update_date:
@author:Yaqi Meng
"""

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
import random as rd
from django.contrib.auth.hashers import make_password
from user.models import User, PersonalInfo, JobExperience, TrainingExperience, \
    EducationExperience, Evaluation, WxUserPhoneValidation
import requests
from django.views.generic.base import View
from django.http import HttpResponse, JsonResponse


class CreateTestData(View):

    def get_random_count(self):
        # return rd.randint(1, 10)
        return rd.randint(1, 10)

    def create_users(self):
        # 循环n次 创建用户
        creation_count = self.get_random_count()
        res = []
        msg = ""
        for _ in range(creation_count):
            username = "testuser" + str(rd.randint(1, 9999))
            password = make_password(username)
            is_exist = User.objects.filter(username=username, password=password)
            if not is_exist.exists():
                new_user = User.objects.create(username=username, password=password, email="")
                res.append(new_user.id)
                msg += ("create user" + str(new_user.id) + ". ")
        return res, msg

    def create_students_by_user_list(self, user_list, msg):
        for user_id in user_list:
            name = "学员" + str(user_id)
            phone = rd.randint(10000000000, 19999999999)
            wechat = "vx" + str(user_id)
            id_number = "111111199899998800"
            xet_list = ["u_61bd64a2b6342_bPemQYtw3w", "u_61b401f777cab_A90uiZ4mcN", "u_61b4014259280_AqcbXyrKJ5", "u_61b4012150315_9LJH0w7mmi",
                        "u_61b40116586a3_8kqKW4y6ps", "u_61b400c377be8_zgDClpBajj", "u_61b2b4904d7ce_gSn2tZJrUX", "u_61b2b47168a0d_jIGjlqfylm",
                        "u_61b2b46d4d7b7_nuFSrKzyxI", "u_61b2b4474e35a_F28I6LNQei", "u_61b2b447453f7_Es4VPrG2n7", "u_61b2b43163cf6_t1Wd05oSt8",
                        "u_61b2b3314d6f2_rh0jCUCRma", "u_61b2b31f8671e_WfhrXSZBiE"]
            new_student = studentInfo.objects.using("db_cert").create(student_id=user_id, student_name=name,
                                                                      phone_number=phone,
                                                                      wechat_openid=wechat,
                                                                      id_number=id_number,
                                                                      is_valid=1, xet_id=rd.sample(xet_list, 1)[0])
            new_student.update_sex()
            new_student.save()
            msg += ("create student" + str(new_student.student_id) + ". ")
        return msg

    def join_classes(self, student_list, msg):
        class_list = classExamCon.objects.using("db_cert").all()
        class_id_list = [c.class_id.class_id for c in class_list]
        for student_id in student_list:
            new_joined = classStudentCon.objects.using("db_cert").create(class_id_id=rd.sample(class_id_list,1)[0], student_id_id=student_id)
            this_class = new_joined.class_id
            # 根据班级设置检查更新初始进度
            if this_class.is_online_study_exist:
                new_joined.study_progress = 0
                onlineStudyRecords.objects.using("db_cert").create(class_student=new_joined)
            if this_class.is_practice_exist:
                new_joined.practice_progress = 0
                practiceRecords.objects.using("db_cert").create(class_student=new_joined)
            if this_class.is_exam_exist:
                new_joined.exam_progress = 0
                this_exam_con = classExamCon.objects.using("db_cert").filter(class_id_id=this_class.class_id)
                this_exam_con = this_exam_con.first()
                examRecords.objects.using("db_cert").create(class_exam_id_id=this_exam_con.class_exam_id,
                                                            student_id_id=student_id)
            if this_class.is_cert_exist:
                new_joined.cert_progress = 0
            new_joined.save()
            msg += ("student" + str(student_id) + "joint class" + str(this_class.class_id) + ". ")
        return msg

    def get(self, request, *args, **kwargs):
        res, msg = self.create_users()
        msg = self.create_students_by_user_list(res, msg)
        msg = self.join_classes(res, msg)

        return JsonResponse(dict(code=1000, msg=msg))
