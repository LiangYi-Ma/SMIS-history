# author: Mr. Ma
# datetime :2022/6/22
from enterprise.models import EnterpriseCooperation, Applications


def check_hr_enterprise(enterprise_id, user_id):
    """
        功能：检测hr是否是对应企业中的hr
        enterprise_id:企业id
        user_id:用户id
        return: boolean
        逻辑：检测在协作表（EnterpriseCooperation）中enterprise_id和user_id是否相对应，如果对应则该用户是hr
    """
    try:
        data = EnterpriseCooperation.objects.filter(enterprise_id=enterprise_id, user_id=user_id).first()
        if data:
            return True
        else:
            return False
    except Exception as e:
        raise e


def check_hr(uid):
    """
        功能 ：检查用户是否是hr，只检查身份不检查是否是对应企业中的hr
        uid：用户id
        逻辑：在协作表中查找是否有hr的id等于uid
        return : Boolean
    """
    try:
        enterprisecooperation = EnterpriseCooperation.objects.filter(user_id=uid).first()
        if enterprisecooperation:
            return True
        else:
            return False
    except Exception as e:
        # 如果有异常直接抛了，不返回值，不然可能会产生误导
        raise e


def hr_is_superuser(uid):
    """
        功能：检测hr的身份
        uid：用户id
        逻辑：首先检测用户是否是hr，其次查询用户的hr身份类型
        return：int (1：管理者。 0：协作者。 -1：用户不是hr)
    """
    try:
        bool = check_hr(uid)
        if bool:
            enterprisecooperations = EnterpriseCooperation.objects.filter(user_id=uid).first()
            is_superuser_data = enterprisecooperations.is_superuser
            if is_superuser_data == 0 or is_superuser_data == False:
                return 0
            else:
                return 1
        else:
            return -1
    except Exception as e:
        raise e


def hr_appliaction(uid, application_id):
    """
        功能：检测hr是否是对应候选人的hr（带检测用户是否是hr功能）
        uid：hr编号
        application_id：候选人编号
        return: Boolean，String
    """
    # 检测用户是否是hr
    bool_hr = check_hr(uid)
    if bool_hr:
        # 校验候选人编号是否存在
        application_data = Applications.objects.filter(id=application_id).first()
        if application_data:
            # 检测是否是对应的hr
            if application_data.hr.user_id == uid:
                return True, ""
            else:
                return False, "该hr不是对应候选人的hr"
        else:
            return False, "候选人不存在"
    else:
        return False, "用户不是hr"
