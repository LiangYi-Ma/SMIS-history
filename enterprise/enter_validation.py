import numpy
import re


def ValidateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def is_number(num):
    """
    判断字符串是否为全由数字组成，包括整数和浮点数
    num：string类型
    """
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    result = pattern.match(num)
    if result:
        return True
    else:
        return False


def enterprise_info_is_valid(para):
    back_dic = dict(
        code=1000,
        msg="",
        data=None,
    )
    #  {'name': '北京智能智造', 'nature': '4', 'field': '93', 'size': None, 'financial': '0',
    #  'establish_year': '2001'}
    if para["edit_type"] == 1:
        if len("name") == 0 or len("name") >= 18:
            back_dic["code"] = 10010
            back_dic["msg"] = "企业名称长度不规范！"
        elif not is_number(para["field"]):
            back_dic["code"] = 10011
            back_dic["msg"] = "请从领域待选选项中做出选择！"
        elif not is_number(para["nature"]):
            back_dic["code"] = 10012
            back_dic["msg"] = "请从待选选项中选择企业性质！"
        elif not is_number(para["size"]):
            back_dic["code"] = 10013
            back_dic["msg"] = "请从待选选项中选择企业规模！"
        elif not is_number(para["financial"]):
            back_dic["code"] = 10014
            back_dic["msg"] = "请从待选选项中选择金融状态！"
        elif not is_number(para["establish_year"]):
            back_dic["code"] = 10015
            back_dic["msg"] = "请从待选选项中选择创建时间！"
        else:
            back_dic["msg"] = "企业基本信息修改成功！"
    # elif para["edit_type"] == 2:
        # if

    return back_dic
