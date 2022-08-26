# author: Mr. Ma
# datetime :2022/8/22
from cv.models import CV_PositionClass
from user.models import User, PersonalInfo, JobExperience

""" 此处的目的是利用ORM自身的缓存机制，减少数据库访问次数 """


def UserUtile(user_id):
    try:
        pp1 = User.objects.get(id=user_id)
    except Exception as e:
        print(e)
        return ''
    return pp1


def PersonalInfoUtile(user_id):
    try:
        pp1 = PersonalInfo.objects.get(id=user_id)
    except Exception as e:
        print(e)
        return ''
    return pp1


def CVPositionClassUtile(cv_id):
    try:
        pp1 = CV_PositionClass.objects.filter(cv_id=cv_id).order_by('-create_time').first()
    except Exception as e:
        print(e)
        return ''
    return pp1
