# author: Mr. Ma
# datetime :2022/6/28

"""
    本文件封装了人才筛选的各种筛选方法
"""
from cv.models import CV_PositionClass
from enterprise.models import PositionClass
from user.models import PersonalInfo


def screen_education(cv, education: int):
    """
    功能：通过教育经历筛选简历
    教育经历：user.models.PersonalInfo.get_degree可以知道用户的最高学历，用来做筛选（根据education）
    cv: list[cv] 简历对象列表（并不是整个简历而是筛选过后的简历列表）
    education：筛选条件，最低学历要求
    return: list[cv] 返回简历对象列表
    """
    result = []
    try:
        # 为了保险起见强转一下
        cv = list(cv)
        for i in cv:
            per_data = PersonalInfo.objects.filter(id=i.user_id).first()
            # 获取用户的最高学历
            edu_user = per_data.get_degree()
            # 用户的最高学历大于等于要求的最低学历就ok
            if int(education) <= int(edu_user):
                result.append(i)
    except Exception as e:
        raise e
    return result


def screen_experience(cv, experience: int):
    """
    功能：根据工作经验筛选简历
    cv: list[cv] 简历对象列表（并不是整个简历而是筛选过后的简历列表）
    experience：筛选条件，工作要求经验
    return: list[cv] 返回简历对象列表
    """
    result = []
    try:
        cv = list(cv)
        for i in cv:
            per_data = PersonalInfo.objects.filter(id=i.user_id).first()
            # 获取用户的最高学历
            exp_user = per_data.get_work_code()
            # 用户的经验大于等于要求的经验
            if int(experience) <= int(exp_user):
                result.append(i)
    except Exception as e:
        raise e
    return result


def screen_salary(cv, max_salary):
    """
    功能：根据薪资筛选简历
    cv: list[cv] 简历对象列表（并不是整个简历而是筛选过后的简历列表）
    max_salary：筛选条件，岗位薪资的范围最高值
    return: list[cv] 返回简历对象列表
    """
    result = []
    try:
        cv = list(cv)
        for i in cv:
            # 获取用户的最低薪资要求
            salary = i.expected_salary
            # 用户的经验大于等于要求的经验
            if max_salary >= salary:
                result.append(i)
    except Exception as e:
        raise e
    return result


def screen_salary(cv, max_salary):
    """
    功能：根据薪资筛选简历
    cv: list[cv] 简历对象列表（并不是整个简历而是筛选过后的简历列表）
    max_salary：筛选条件，岗位薪资的范围最高值
    return: list[cv] 返回简历对象列表
    """
    result = []
    try:
        cv = list(cv)
        for i in cv:
            # 获取用户的最低薪资要求
            salary = i.expected_salary
            # 用户的经验大于等于要求的经验
            if max_salary >= salary:
                result.append(i)
    except Exception as e:
        raise e
    return result


def cv_position_class(cv):
    """
    功能：查找简历对应的类别（之所以封装这个是为了调用一级查二级工具类时能统一格式调用，仅此而已）
    cv：简历模型
    return :int 返回类别的id
    """
    try:
        cvp = CV_PositionClass.objects.filter(cv_id=cv.id).first()
        id = cvp.position_class_id.id
        return id
    except Exception as e:
        raise e


def find_children_root(pc):
    """
    功能：由二级目录查出对应所有的一级目录
    pc：类别id
    return : int 返回一级类别的id
    """
    try:
        pc_child = PositionClass.objects.filter(id=pc).first()
        if pc_child.is_root:
            raise "异常操作：岗位类别为一级目录"
        return pc_child.parent.id
    except Exception as e:
        raise e


def screen_position_class(cv, pc_id: int):
    """
    功能：根据类别筛选
    cv: list[cv] 简历对象列表（并不是整个简历而是筛选过后的简历列表）
    pc_id：int 岗位类别要求
    逻辑：首先查出目标和简历对应的一级(对查找二级对应的一级进行封装)
         首先比对二级，如果一样直接满足，如果不一样则比对二者的一级，一样则满足
         直接做排序（首先插入判断二级相同的，则循环判断一级相同的，这样相当于排序了）
    return: list[cv] 返回简历对象列表
    """
    result = []
    try:
        cv = list(cv)
        cv_utils = list(cv)
        # 判断二级
        for i in cv:
            pc_id_cv = cv_position_class(i)
            if int(pc_id_cv) == int(pc_id):
                result.append(i)
                cv_utils.pop(cv.index(i))
        # 判断一级
        if len(cv_utils):
            for i in cv_utils:
                pc_id_cv = cv_position_class(i)
                pc_id_child = find_children_root(pc_id)
                pc_id_cv_child = find_children_root(pc_id_cv)
                if pc_id_child == pc_id_cv_child:
                    result.append(i)
    except Exception as e:
        raise e
    return result
