"""
@file_intro: 定时任务：1.自动更新线上课时长
@creation_date: 20220322
@update_date: 20220322
@author:Yaqi Meng
"""
from cert.models import failedUpdateRecords, updateDateRecords, onlineStudyRecords, classInfo, studentInfo, \
    classStudentCon
import datetime
from cert.api_xet_client import XiaoeClient
from numpy import array


def get_study_info_by_list(user_list, date):
    """
    1.发送id列表，查询这些用户的昨日时长;
    :param date: str
    :param user_list: list
    :return: 请求结果，列表数据
    """
    user_list = list(filter(None, user_list))
    print(">>>>user list:", user_list)
    api_url = "https://api.xiaoe-tech.com/xe.learning_records.daily.get/1.0.0"
    params = {
        "date": date,
        "page": 1,
        "page_size": len(user_list),
        "user_id_list": array(user_list).tolist()
    }
    client = XiaoeClient()
    res = client.request("post", api_url, params)
    print(res)
    if res["code"] == 0:
        '''请求成功'''
        return True, res["data"]["list"]
    else:
        '''请求失败'''
        return False, None


def get_xet_list_by_class_id(class_id):
    """
    :param class_id: int
    :return: 小鹅通id列表：dict:{"xet_id": "class_student_id",}
    """
    xet_dic = {}
    students = classStudentCon.objects.using("db_cert").filter(class_id_id=class_id)
    for student in students:
        xet_id = student.student_id.xet_id
        xet_dic[xet_id] = student.class_student_id
    return xet_dic


def get_class_id_list_daily():
    """
    1.筛选状态为1进行中的班级，返回班级id列表
    :return: list
    """
    class_list = []
    class_queryset = classInfo.objects.using("db_cert").filter(class_status=1)
    for each_class in class_queryset:
        class_list.append(each_class.class_id)
    return class_list


def update_online_study_progress():
    """
    1.筛选所有班级状态为"1进行中"的班级，拿到班级id列表，遍历这个列表；
        2.对于每一个班级，拿到这个班级中所有学员的小鹅通id，形成小鹅通账号id列表；
        3.拿着小鹅通账号id列表去小鹅通服务器请求这些用户的昨日学习时长；
            4.如果请求成功，比对id并更新班级内学员的【学习时长】，【更新记录表】更新；
            5.如果请求失败，将失败信息存入更新【失败记录表】；
    :return: 无
    """
    class_list = get_class_id_list_daily()
    print(">>>>待更新班级：", class_list)
    for each_class in class_list:
        xet_student_dic = get_xet_list_by_class_id(each_class)
        xet_list = xet_student_dic.keys()
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        res, res_list = get_study_info_by_list(xet_list, date)
        if res:
            '''请求成功'''
            print(">>>yeah")
            for record in res_list:
                if record["user_id"] in xet_student_dic.keys():
                    c_s_id = xet_student_dic[record["user_id"]]
                    study_record = onlineStudyRecords.objects.using("db_cert").filter(
                        class_student__class_student_id=c_s_id)
                    if study_record.exists():
                        this_record = study_record.first()
                        this_record.accumulated_time += round(record["stay_time"]/60, 2)
                        this_record.latest_time = round(record["stay_time"]/60, 2)
                        this_record.save()
        else:
            '''请求失败'''
            print(">>>non")
            failed_date = datetime.datetime.now() - datetime.timedelta(days=1)
            failedUpdateRecords.objects.using("db_cert").create(class_id_id=each_class, failed_date=failed_date,
                                                                is_updated=0)
    return 0


def update_online_study_progress_by_hand(class_id, date):
    print(class_id, date)
    xet_student_dic = get_xet_list_by_class_id(class_id)
    print(xet_student_dic)
    xet_list = list(xet_student_dic.keys())
    res, res_list = get_study_info_by_list(xet_list, date)
    print(res, res_list)
    if res:
        '''请求成功'''
        for record in res_list:
            if record["user_id"] in xet_student_dic.keys():
                c_s_id = xet_student_dic[record["user_id"]]
                study_record = onlineStudyRecords.objects.using("db_cert").filter(
                    class_student__class_student_id=c_s_id)
                if study_record.exists():
                    this_record = study_record.first()
                    this_record.accumulated_time += round(record["stay_time"] / 60, 2)
                    this_record.latest_time = round(record["stay_time"] / 60, 2)
                    this_record.save()

        failed_record = failedUpdateRecords.objects.using("db_cert").filter(failed_date=date, class_id_id=class_id)
        print("$$$$$$$$", failed_record.exists())
        if failed_record.exists():
            failed_record = failed_record.first()
            failed_record.delete()

        return dict(code=1000, msg="补更新成功")
    else:
        '''请求失败'''
        return dict(code=10001, msg="补更新失败，请重试")

