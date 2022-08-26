# author: Mr. Ma
# datetime :2022/8/23


""" PositionNewCvRetrieval人才检索接口专用工具类 """
from django.contrib.auth.models import User

from cv.models import CV_PositionClass
from user.models import EducationExperience, PersonalInfo, JobExperience


def age_utiles(cv, ages):
    """ 年龄要求 age  cv """
    try:
        for i in cv:
            age = i.age()
            if not (age >= ages[0] and age <= ages[1]):
                cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def educationexperience_utiles(cv, is_unified_recruit):
    """ 院校要求（是否统招）  """

    try:
        ee = EducationExperience.objects.filter(is_unified_recruit=is_unified_recruit)
        user_list = []
        for i in cv:
            user = i.user_id.id
            if user in user_list:
                continue
            else:
                pi = PersonalInfo.objects.filter(id=user)
                if not pi.exists():
                    u1 = User.objects.filter(id=user).first()
                    pi = PersonalInfo.objects.create(id=u1)
            if ee.filter(user_id=user).exists():
                user_list.append(user)
            else:
                cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def jobexperience_utils(cv, data):
    """工作年限  JobExperience -work_year_make()"""
    try:
        user_list = []
        for i in cv:
            user = i.user_id.id
            if user in user_list:
                continue
            else:
                pi = PersonalInfo.objects.filter(id=user)
                if not pi.exists():
                    u1 = User.objects.filter(id=user).first()
                    PersonalInfo.objects.create(id=u1)
            je = JobExperience.objects.filter(user_id=user)
            if je.exists():
                flag = 0
                for j in je.all():
                    years = j.working_years()
                    if data[0] == 0:
                        """处理无经验(如果要求无经验则匹配1年以下的简历)"""
                        if years < 1:
                            user_list.append(user)
                            user_list = list(set(user_list))
                            flag = 1
                            break
                    else:
                        if years >= data[0] and years <= data[1]:
                            user_list.append(user)
                            user_list = list(set(user_list))
                            flag = 1
                            break
                if flag == 0:
                    cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def personalinfo_utils_active(cv, data):
    """ 活跃日期 """
    try:
        for i in cv:
            user_id = i.user_id.id
            pi = PersonalInfo.objects.filter(id=user_id)
            if not pi.exists():
                u1 = User.objects.filter(id=user_id).first()
                pi = PersonalInfo.objects.create(id=u1)
                pi.online_status = pi.active_time()
                pi.save()
            else:
                pi = pi.first()
                if (not (pi.online_status == '' or pi.online_status == None)):
                    pi.online_status = pi.active_time()
                    pi.save()
            if pi.online_status != data:
                cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def personalinfo_utils_sex(cv, data):
    """ 性别 """
    try:
        for i in cv:
            user_id = i.user_id.id
            pi = PersonalInfo.objects.filter(id=user_id)
            if not pi.exists():
                u1 = User.objects.filter(id=user_id).first()
                pi = PersonalInfo.objects.create(id=u1)
                pi.online_status = pi.active_time()
                pi.save()
            pi = pi.first()
            if (not (pi.sex == '' or pi.sex == None)) and pi.sex != data:
                cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def personalinfo_utils_education(cv, data):
    """ 学历要求 """
    try:
        for i in cv:
            user_id = i.user_id.id
            pi = PersonalInfo.objects.filter(id=user_id)
            if not pi.exists():
                u1 = User.objects.filter(id=user_id).first()
                pi = PersonalInfo.objects.create(id=u1)
                pi.online_status = pi.active_time()
                pi.save()
            pi = pi.first()
            if (not (pi.education == '' or pi.education == None)) and pi.education not in data:
                cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def cv_positionclass_utils_position_class(cv, data):
    """ 期望职位"""
    try:
        for i in cv:
            cp = CV_PositionClass.objects.filter(cv_id=i.id)
            if cp.exists():
                list_cp = []
                for j in cp:
                    list_cp.append(j.position_class_id.id)
                cou = set(data).intersection(set(list_cp))
                if len(cou) == 0:
                    cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def cv_positionclass_utils_salary(cv, data):
    """ 薪资要求  """
    try:
        for i in cv:
            cp = CV_PositionClass.objects.filter(cv_id=i.id)
            if cp.exists():
                list_cp = []
                for j in cp:
                    if (not (j.salary_min == '' or j.salary_min == None)) and j.salary_min <= data[1]:
                        list_cp.append(j.position_class_id.id)
                    if j.salary_min == '' or j.salary_min == None:
                        list_cp.append(j.position_class_id.id)
                if len(list_cp) == 0:
                    cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv


def cv_positionclass_utils_city(cv, data):
    """ 期望城市 """
    try:
        for i in cv:
            cp = CV_PositionClass.objects.filter(cv_id=i.id)
            if cp.exists():
                list_cp = []
                for j in cp:
                    if (not (j.city == '' or j.city == None)) and str(j.city.second) == str(data):
                        list_cp.append(j.position_class_id.id)
                    if j.city == '' or j.city == None:
                        list_cp.append(j.position_class_id.id)
                if len(list_cp) == 0:
                    cv = cv.exclude(id=i.id)
    except Exception as e:
        raise e
    return cv
