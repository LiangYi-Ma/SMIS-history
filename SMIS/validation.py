import datetime
import re
from id_validator import validator
from django.contrib.sessions.models import Session

"""
{'type': '101', 'id': '37', 
'start': '2020-12-30', 'end': '2021-01-05', 
'enterprise': 'f', 'location': 's', 'position': 'sa', 'content': 'sa'}
"""


# 判断session 是否过期
def session_exist(request):
    # session_key = request.session.session_key
    session_key = request.META.get("HTTP_AUTHORIZATION")
    print("*****", request.META.get("HTTP_AUTHORIZATION"))
    # for k, v in request.META.items():
    #     print("> ", k, ":", v)
    back_dir = dict(code=1000, msg="", data=dict())
    try:
        is_existed = Session.objects.get(session_key__exact=session_key)
        # if is_existed and is_existed.expire_date <= datetime.datetime.now():
        #     back_dir["code"] = 0
        #     back_dir["msg"] = "session[" + is_existed.session_key + "]已失效"
        #     request.session.flush()
    except:
        if session_key:
            back_dir["code"] = 0
            back_dir["msg"] = "session[" + session_key + "]未被检测到"
        else:
            back_dir["code"] = 0
            back_dir["msg"] = "接收到的session_key为空"

    # 判断 session_key是否存在
    # if not is_existed:
    #     back_dir["code"] = 0
    #     back_dir["msg"] = "未检测到session或session已失效"
    #     request.session.flush()
    return back_dir


def is_number(num):
    """
    判断字符串是否为全由数字组成，包括整数和浮点数
    num：string类型
    """
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    try:
        result = pattern.match(num)
    except:
        result = pattern.match(str(num))
    if result:
        return True
    else:
        return False


def is_null(value):
    return value in ["", None, "null", "undefined"]


# global is_null


def is_instance(value):
    try:
        value = int(value)
        return isinstance(value, int)
    except:
        return False


def ValidateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def ValidateUrl(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url)


def ValidationIdNumber(id_number):
    return validator.is_valid(id_number)


def job_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    print("dict")
    print(dict)
    now = datetime.datetime.now()
    try:
        start = datetime.datetime.strptime(dict['start'], '%Y-%m-%d')
        end = datetime.datetime.strptime(dict['end'], '%Y-%m-%d')
    except:
        back_dic['code'] = 10012
        back_dic['msg'] = '请输入/选择正确格式的日期！'
        return back_dic
    if start > end:
        back_dic['code'] = 10010
        back_dic['msg'] = '这段工作的开始日期比结束日期还要晚！'
    elif start > now:
        back_dic['code'] = 10011
        back_dic['msg'] = '这段工作还没开始！'
    elif len(dict['enterprise']) == 0 or len(dict['enterprise']) > 18:
        back_dic['code'] = 10020
        back_dic['msg'] = '请将公司名称保持在18字以内哦'
    elif not (dict['position'] or dict['location']):
        back_dic['code'] = 10030
        back_dic['msg'] = '职位与岗位至少要填写一项'
    elif not is_number(dict["position"]):
        back_dic['code'] = 10031
        back_dic['msg'] = '请从备选选项中选择你的岗位类别'
    elif len(dict['content']) == 0 or len(dict['content']) > 15:
        back_dic['code'] = 10040
        back_dic['msg'] = "在填写您的工作内容时，请将长度保持在15字以内"

    return back_dic


"""
{'type': '201', 'id': '8', 'start': '2020-12-31', 'end': '2021-02-02', 
'school': 'xc', 'department': 'xc', 'major': 'xc', 'degree': '硕士', 'edu': '硕士研究生'}
"""

EDU_LIST = ['小学', '初中', '高中', '中专', '职校', '中技', '专科', '本科', '硕士研究生', '博士研究生', '-', '']
DEGREE_LIST = ['学士', '硕士', '博士', '-', '']


def edu_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    print("dict")
    print(dict)
    now = datetime.datetime.now()
    try:
        start = datetime.datetime.strptime(dict['start'], '%Y-%m-%d')
        end = datetime.datetime.strptime(dict['end'], '%Y-%m-%d')
    except:
        back_dic['code'] = 10012
        back_dic['msg'] = '请输入/选择正确格式的日期！'
        return back_dic

    if start > end:
        back_dic['code'] = 10010
        back_dic['msg'] = '这段教育经历的开始日期比结束日期还要晚！'
    elif start > now:
        back_dic['code'] = 10011
        back_dic['msg'] = '这段教育经历还没开始！'
    elif len(dict['school']) == 0 or len(dict['school']) >= 15:
        back_dic['code'] = 10020
        back_dic['msg'] = '请将学校名称保持在15字以内哦'
    elif len(dict['major']) == 0 or len(dict['major']) >= 15:
        back_dic['code'] = 10030
        back_dic['msg'] = '请将专业名称保持在15字以内哦'
    elif is_null(dict["edu"]):
        back_dic["code"] = 10040
        back_dic["msg"] = "请选择你在这段经历中所获得的学历"
    else:
        pass

    return back_dic


def tra_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    print("dict")
    print(dict)
    now = datetime.datetime.now()
    try:
        start = datetime.datetime.strptime(dict['start'], '%Y-%m-%d')
        end = datetime.datetime.strptime(dict['end'], '%Y-%m-%d')
    except:
        back_dic['code'] = 10012
        back_dic['msg'] = '请输入/选择正确格式的日期！'
        return back_dic
    if start > end:
        back_dic['code'] = 10010
        back_dic['msg'] = '这段培训经历的开始日期比结束日期还要晚！'
    elif start > now:
        back_dic['code'] = 10011
        back_dic['msg'] = '这段培训经历还没开始！'
    elif len(dict['team']) == 0 or len(dict['team']) >= 15:
        back_dic['code'] = 10020
        back_dic['msg'] = '请将培训机构名称保持在15字以内哦'
    elif len(dict['content']) == 0 or len(dict['content']) >= 15:
        back_dic['code'] = 10030
        back_dic['msg'] = '请将培训内容保持在15字以内哦'
    else:
        pass
    return back_dic


from cv.models import Industry

# INDUSTRY_LIST = ['矿业', '能源', '电讯', '服装', '航空航天', '化学', '建筑业', '金属冶炼', '造纸', '机械制造', '其他', '']
SKILL_LIST = ['一般', '了解', '中等', '熟悉', '精通', '-']


# INDUSTRY_LIST = Field.objects.filter(is_root=False).all()

def cv_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    print("dict:", dict)
    if is_null(dict['industry']):
        back_dic['code'] = 10010
        back_dic['msg'] = '请从备选选项中选择您的的行业（目前所在行业或即将进入的行业均可）'
    elif is_null(dict['major']) or len(dict['major']) > 15:
        back_dic['code'] = 10020
        back_dic['msg'] = '请填写专业名称，并将专业名称限制在15字以内'
    elif is_null(dict['course']) or len(dict['course']) > 50:
        back_dic['code'] = 10030
        back_dic['msg'] = '请将所修课程名称限制在50字以内'
    elif dict["type"] in ["402"]:
        if is_null(dict['intention']):
            back_dic['code'] = 10040
            back_dic['msg'] = '请从备选选项中选择你的求职意向'
        else:
            pass
    elif is_null(dict["english"]) or is_null(dict["computer"]):
        back_dic["code"] = 100560
        back_dic["msg"] = "请选择你的英语水平和计算机水平"
    elif not (is_number(dict['salary']) and is_instance(dict["salary"])):
        back_dic['code'] = 10070
        back_dic['msg'] = '请用数字输入你的最低期望薪资（单位：元）'
    elif is_null(dict['pro']) or len(dict['pro']) > 50:
        back_dic['code'] = 10080
        back_dic['msg'] = '请将你的专业技能限制在50字以内'
    elif is_null(dict['award']) or len(dict['award']) > 100:
        back_dic['code'] = 10090
        back_dic['msg'] = '请将你的历史荣誉、奖项、证书等限制在100字以内'
    elif is_null(dict['talent']) or len(dict['talent']) > 8:
        back_dic['code'] = 10100
        back_dic['msg'] = '请将你的特长/爱好限制在8字以内'

    return back_dic


def enterprise_info_is_valid(para):
    from enterprise.models import SettingChineseTag, TaggedWhatever
    back_dic = dict(
        code=1000,
        msg="",
        data=None,
    )
    #  {'name': '北京智能智造', 'nature': '4', 'field': '93', 'size': None, 'financial': '0',
    #  'establish_year': '2001'}
    if para["edit_type"] == 1:
        if len(para["name"]) == 0 or len(para["name"]) >= 18:
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
            back_dic["msg"] = "成立时间应该是一个数字（年份）！"
        else:
            back_dic["msg"] = "企业基本信息修改成功！"
    # {'edit_type': 2, 'email': '115293093@qq.com',
    # 'address': '在这里', 'site': 'www.edffff.com', 'introduction': '我还行'}
    elif para["edit_type"] == 2:
        if not ValidateEmail(para["email"]):
            back_dic["code"] = 10020
            back_dic["msg"] = "企业邮箱格式不规范！"
        elif len(para["address"]) >= 50:
            back_dic["code"] = 10021
            back_dic["msg"] = "地址过长，请精简！"
        elif not ValidateUrl(para["site"]):
            back_dic["code"] = 10022
            back_dic["msg"] = "网站格式不正确！"
        elif len(para["introduction"]) == 0:
            back_dic["code"] = 10023
            back_dic["msg"] = "请输入企业简介！"
        elif len(para["introduction"]) >= 500:
            back_dic["code"] = 10024
            back_dic["msg"] = "企业简介过长，请保持在500字以内！"
        else:
            back_dic["msg"] = "企业联系信息修改成功！"
    # {'edit_type': 3, 'bonus': ''}
    elif para["edit_type"] == 3:
        if len(para["bonus"]) is 0:
            back_dic["code"] = 10030
            back_dic["msg"] = "标签不能为空"
        else:
            back_dic["msg"] = "企业自定义福利标签成功！"
    # json {"type": "301", "id": "12"}
    elif para["edit_type"] == 301:
        the_tag = SettingChineseTag.objects.filter(id=int(para["id"]))
        if not the_tag:
            back_dic["code"] = 1003010
            back_dic["msg"] = "该默认标签不存在，请刷新重试"
        else:
            back_dic["msg"] = "删除默认标签操作成功！"
    elif para["edit_type"] == 302:
        the_tag = SettingChineseTag.objects.filter(id=int(para["id"]))
        if not the_tag:
            back_dic["code"] = 1003020
            back_dic["msg"] = "该自定义标签不存在，请刷新重试"
        else:
            back_dic["msg"] = "删除自定义标签操作成功！"
    elif para["edit_type"] == 303:
        the_tag = SettingChineseTag.objects.filter(id=int(para["id"]))
        if not the_tag:
            back_dic["code"] = 1003030
            back_dic["msg"] = "该默认标签不存在，请刷新重试"
        else:
            back_dic["msg"] = "添加默认标签操作成功！"
    else:
        pass

    return back_dic


# {'type': '202', 'id': 16, 'number': '9', 'education': 7,
# 'salary_1': '23', 'salary_2': '222', 'salary_unit': 0,
# 'city': 7, 'exp': 0, 'nature': 4, 'deadline': '2021-08-27'}
def position_post_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '/enterprise/positions/',
    }
    for k, v in dict.items():
        if is_null(v):
            back_dic["code"] = 1020
            back_dic["msg"] = "请填写所有字段"
            return back_dic

    if is_null(dict["number"]) or not (is_number(dict["number"]) and int(dict["number"]) >= 1):
        back_dic["code"] = 1021
        back_dic["msg"] = "请输入招聘人数，招聘人数应为一个数字(>=1)"
    elif not (is_number(dict["salary_1"]) and is_number(dict["salary_2"])):
        back_dic['code'] = 1022
        back_dic['msg'] = "薪资区间应为两个数字组成"
    elif datetime.datetime.strptime(dict["deadline"], "%Y-%m-%d") < datetime.datetime.now():
        back_dic["code"] = 1023
        back_dic["msg"] = "这个截止时间早于今天"
    elif dict["education"] in ["", None]:
        back_dic["code"] = 1024
        back_dic["msg"] = "请选择教育水平"
    elif dict["salary_unit"] in ["", None]:
        back_dic["code"] = 1025
        back_dic["msg"] = "请选择薪资单位"
    elif dict["city"] in ["", None]:
        back_dic["code"] = 1026
        back_dic["msg"] = "请选择工作地点"
    elif dict["exp"] in ["", None]:
        back_dic["code"] = 1027
        back_dic["msg"] = "请选择工作经验"
    elif dict["nature"] in ["", None]:
        back_dic["code"] = 1028
        back_dic["msg"] = "请选择工作性质"
    else:
        pass

    return back_dic


def position_info_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    if is_null(dict["content"]) or len(dict["content"]) > 150:
        back_dic["code"] = 1001
        back_dic["msg"] = "需填写工作内容（上限150字）"
    elif is_null(dict["requirement"]) or len(dict["requirement"]) > 150:
        back_dic["code"] = 1002
        back_dic["msg"] = "需填写岗位要求（上限150字）"
    elif dict["class"] in ["", None]:
        back_dic["code"] = 1004
        back_dic["msg"] = "请选择该岗位的类别"
    else:
        pass

    try:
        extra = dict["extra"]
        if (not is_null(dict["extra"])) and len(dict["extra"]) > 150:
            back_dic["code"] = 1005
            back_dic["msg"] = "补充说明内容过多（上限150字）"
    except:
        pass

    return back_dic


def student_info_is_valid(dict):
    back_dic = {
        'code': 1000,
        'msg': '已完成',
        'url': '',
    }
    if is_null(dict["name"]):
        back_dic["code"] = 1001
        back_dic["msg"] = "姓名不能为空"
    elif len(dict["name"]) > 16:
        back_dic["code"] = 1002
        back_dic["msg"] = "姓名过长"
    elif not is_number(dict["phone"]) or len(dict["phone"]) != 11:
        back_dic["code"] = 1003
        back_dic["msg"] = "请输入正确格式的手机号"
    elif is_null(dict["wechat"]):
        back_dic["code"] = 1004
        back_dic["msg"] = "微信号不能为空"
    elif len(dict["wechat"]) < 6 or len(dict["wechat"]) > 20:
        back_dic["code"] = 1005
        back_dic["msg"] = "微信号长度不规范"
    elif len(dict["id_number"]) != 18:
        back_dic["code"] = 1006
        back_dic["msg"] = "仅支持18位身份证号的输入"
    elif not ValidationIdNumber(dict["id_number"]):
        back_dic["code"] = 1007
        back_dic["msg"] = "身份证号校验未通过，请检查并重新输入"

    return back_dic


def split_q(q):
    length = len(list(q))
    splited_list = []
    for i in range(length):
        splited_list.append(q[0: i + 1])
        if q[i + 1:] != '':
            splited_list.append(q[i + 1:])
    return splited_list


def calculate_age(date):
    today_d = datetime.datetime.now().date()
    try:
        birth_t = date.replace(year=today_d.year)
        if today_d > birth_t:
            age = today_d.year - date.year
        else:
            age = today_d.year - date.year - 1
        return age
    except:
        return None
