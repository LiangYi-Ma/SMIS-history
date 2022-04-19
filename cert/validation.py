"""
@file_intro: cert模块的合法性检查
@creation_date: 2022-2-7
@update_date: 2022-2-8
@author:Yaqi Meng
"""
from SMIS import constants
import re
import datetime
from SMIS.validation import ValidationIdNumber


def is_null(val):
    return val in ["", " ", None]


def tuple2list(tup):
    return list(zip(*tup))


def is_instance(num):
    return isinstance(num, int)


def is_float(num):
    return isinstance(num, float)


def is_number(num):
    return is_float(num) or is_instance(num)


def is_num_letters(s):
    """判断给定的字符串是否只包含字母、数字、中划线或者下划线中的一个或多个，并且以字母或数字开头"""
    s = str(s)
    if s == '':
        return False
    if len(s) < 2:
        if re.match('^[0-9a-zA-Z]+$', s[0]):
            return True
        else:
            return False
    else:
        if re.match('^[0-9a-zA-Z]+$', s[0]) and re.match('^[0-9a-zA-Z_-]+$', s[1:]):
            return True
        else:
            return False


def cert_is_valid(para):
    back_dic = dict(code=1000, msg="")
    if para["type"] == "2":
        if "cert_id" not in para.keys():
            back_dic["code"] = 10010
            back_dic["msg"] = "未监测到证书id"
        elif not is_instance(para["cert_id"]):
            back_dic["code"] = 10011
            back_dic["msg"] = "监测到证书id并非整型"

    if is_null(para["cert_name"]) or len(para["cert_name"]) > 32:
        back_dic["code"] = 10001
        back_dic["msg"] = "证书名称长度不合法"
    elif para["cert_level"] not in tuple2list(constants.CERTIFICATION_LEVEL)[0]:
        back_dic["code"] = 10002
        back_dic["msg"] = "证书等级不存在"
    elif is_null(para["issuing_unit"]) or len(para["issuing_unit"]) > 32:
        back_dic["code"] = 10003
        back_dic["msg"] = "发证单位长度不合法"
    elif is_null(para["cert_introduction"]) or len(para["cert_introduction"]) > 256:
        back_dic["code"] = 10004
        back_dic["msg"] = "证书简介长度不合法"
    elif para["testing_way"] not in tuple2list(constants.TESTING_WAYS)[0]:
        back_dic["code"] = 10005
        back_dic["msg"] = "考核方式不存在"
    elif is_null(para["aim_people"]) or len(para["aim_people"]) > 64:
        back_dic["code"] = 10006
        back_dic["msg"] = "针对人群长度不合法"
    elif is_null(para["cor_positions"]) or len(para["cor_positions"]) > 64:
        back_dic["code"] = 10007
        back_dic["msg"] = "相关岗位长度不合法"
    elif is_null(para["expiry_date"]) or len(para["expiry_date"]) > 16:
        back_dic["code"] = 10008
        back_dic["msg"] = "有效时限长度不合法"
    else:
        pass
    return back_dic


def student_info_is_valid(para):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    print(para)
    if is_null(para["name"]):
        back_dic["code"] = 1001
        back_dic["msg"] = "姓名不能为空"
    elif len(para["name"]) > 16:
        back_dic["code"] = 1002
        back_dic["msg"] = "姓名过长"
    elif (not is_number(para["phone"])) or len(str(para["phone"])) != 11:
        back_dic["code"] = 1003
        back_dic["msg"] = "请输入正确格式的手机号"
    elif is_null(para["wechat"]):
        back_dic["code"] = 1004
        back_dic["msg"] = "微信号不能为空"
    elif len(para["wechat"]) < 6 or len(para["wechat"]) > 20:
        back_dic["code"] = 1005
        back_dic["msg"] = "微信号长度不规范"
    elif len(para["id_number"]) != 18:
        back_dic["code"] = 1006
        back_dic["msg"] = "仅支持18位身份证号的输入"
    elif not ValidationIdNumber(para["id_number"]):
        back_dic["code"] = 1007
        back_dic["msg"] = "身份证号校验未通过，请检查并重新输入"

    return back_dic


def teacher_is_valid(para):
    back_dic = dict(code=1000, msg="")
    if para["type"] == "2":
        if "teacher_id" not in para.keys():
            back_dic["code"] = 10010
            back_dic["msg"] = "未监测到教师id"
        elif not is_instance(para["teacher_id"]):
            back_dic["code"] = 10011
            back_dic["msg"] = "监测到教师id并非整型"

    if is_null(para["teacher_name"]) or len(para["teacher_name"]) > 16:
        back_dic["code"] = 10001
        back_dic["msg"] = "教师名称长度不合法"
    elif len(str(para["phone_number"])) != 11:
        back_dic["code"] = 10002
        back_dic["msg"] = "请输入11位手机号码"
    elif not is_instance(para["phone_number"]):
        back_dic["code"] = 10002
        back_dic["msg"] = "手机号码应全部由整数组成"
    elif is_null(para['wechat_openid']) or len(para["wechat_openid"]) > 32:
        back_dic["code"] = 10003
        back_dic["msg"] = "微信号长度不合法"
    elif not is_num_letters(para["wechat_openid"]):
        back_dic["code"] = 10003
        back_dic["msg"] = "微信号应由数字、字母和下划线组成"
    elif para["teaching_field"] not in tuple2list(constants.TEACHING_FIELDS)[0]:
        back_dic["code"] = 10004
        back_dic["msg"] = "不存在的授课领域"
    elif is_null(para["self_introduction"]) or len((para["self_introduction"])) > 128:
        back_dic["code"] = 10005
        back_dic["msg"] = "教师简介长度不合法"
    elif para["level"] not in tuple2list(constants.TEACHER_LEVEL)[0]:
        back_dic["code"] = 10006
        back_dic["msg"] = "不存在的教师职称"
    else:
        pass
    return back_dic


def course_is_valid(para):
    print(">>> ", para)
    back_dic = dict(code=1000, msg="")
    if para["type"] in ["2", "0"]:
        if "course_id" not in para.keys():
            back_dic["code"] = 10010
            back_dic["msg"] = "未监测到课程id"
        elif not is_instance(para["course_id"]):
            back_dic["code"] = 10011
            back_dic["msg"] = "监测到课程id并非整型"

    if is_null(para["course_name"]) or len(para["course_name"]) > 32:
        back_dic["code"] = 10001
        back_dic["msg"] = "课程名称长度不合法"
    elif para["course_direction"] not in tuple2list(constants.COURSE_DIRECTION)[0]:
        back_dic["code"] = 10002
        back_dic["msg"] = "不存在的课程方向"
    elif para["course_type"] not in tuple2list(constants.COURSE_TYPE)[0]:
        back_dic["code"] = 10003
        back_dic["msg"] = "不存在的课程类别"
    elif not is_number(para["course_price"]):
        back_dic["code"] = 10004
        back_dic["msg"] = "课程售价应为数字（整数、小数均合法）"
    elif not is_number(para["course_true_price"]):
        back_dic["code"] = 10005
        back_dic["msg"] = "课程真实售价应为数字（整数、小数均合法）"
    else:
        pass

    return back_dic


def class_is_valid(para):
    print(">>> ", para)
    back_dic = dict(code=1000, msg="")
    if para["type"] in ["2", "0"]:
        if "class_id" not in para.keys():
            back_dic["code"] = 10010
            back_dic["msg"] = "未监测到班级id"
        elif not is_instance(para["class_id"]):
            back_dic["code"] = 10011
            back_dic["msg"] = "监测到班级id并非整型"

    if para["class_type"] not in tuple2list(constants.CLASS_TYPE)[0]:
        back_dic["code"] = 10001
        back_dic["msg"] = "不存在的班级类型。"
    elif para["class_period"] not in tuple2list(constants.CLASS_PERIOD)[0]:
        back_dic["code"] = 10002
        back_dic["msg"] = "不存在的周期类型"
    # 暂不确定是否要检查班级状态
    # elif para["class_status"] not in tuple2list(constants.CLASS_STATUS)[0]:
    #     back_dic["code"] = 10003
    #     back_dic["msg"] = "不存在的班级状态"

    now = datetime.datetime.now()
    try:
        start = datetime.datetime.strptime(para["start_date"], '%Y-%m-%d')
        end = datetime.datetime.strptime(para["end_date"], '%Y-%m-%d')
    except:
        back_dic['code'] = 10004
        back_dic['msg'] = '请输入/选择正确格式的日期！'
        return back_dic
    if start > end:
        back_dic['code'] = 10005
        back_dic['msg'] += '班级的预计开始日期比结束日期还要晚！'

    if not isinstance(para["is_exam_exist"], bool):
        back_dic["code"] = 10006
        back_dic["msg"] += "'是否包含考试'参数格式错误。"
    elif not isinstance(para["is_online_study_exist"], bool):
        back_dic["code"] = 10007
        back_dic["msg"] += "'是否包含线上课'参数格式错误。"
    elif not isinstance(para["is_practice_exist"], bool):
        back_dic["code"] = 10008
        back_dic["msg"] += "'是否包含实训'参数格式错误。"
    elif not isinstance(para["is_cert_exist"], bool):
        back_dic["code"] = 10009
        back_dic["msg"] += "'是否关联证书'参数格式错误。"

    return back_dic


def users_validation_check(user_object):
    if not (user_object.is_staff or user_object.is_superuser):
        return False
    return True
