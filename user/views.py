from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib import auth
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.views.generic.base import View
from django.utils.crypto import get_random_string
from .models import User, PersonalInfo, JobExperience, TrainingExperience, \
    EducationExperience, Evaluation, WxUserPhoneValidation
from cv.models import CV, Industry, CV_PositionClass
from enterprise.models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, PositionClass
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from enterprise.models import SettingChineseTag, TaggedWhatever

import datetime
import json
from cv.views import calculate_age
import re
import random as rd
import numpy as np
from PIL import Image
import requests
import urllib

from SMIS.validation import job_is_valid, edu_is_valid, tra_is_valid, cv_is_valid
from SMIS.constants import EDUCATION_LEVELS, JOB_NATURE_CHOICES, NATURE_CHOICES, FINANCING_STATUS_CHOICES, \
    PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, PROGRESS_CHOICES, SEX_CHOICE, NATIONS, MARTIAL_CHOICES, \
    SKILL_CHOICES
from SMIS.mapper import PositionClassMapper, UserMapper, PersonalInfoMapper, EvaMapper, CvMapper, JobExMapper, \
    EduExMapper, TraExMapper, FieldMapper, RecruitmentMapper, EnterpriseInfoMapper, ApplicationsMapper, PositionMapper, \
    NumberOfStaffMapper
from SMIS.validation import is_null


# Create your views here.


# 判断session 是否过期
def session_exist(request):
    # session_key = request.session.session_key
    session_key = request.META.get("HTTP_AUTHORIZATION")
    print("*****", request.META.get("HTTP_AUTHORIZATION"))
    for k, v in request.META.items():
        print("> ", k, ":", v)
    back_dir = dict(code=1000, msg="", data=dict())
    try:
        is_existed = Session.objects.get(session_key__exact=session_key)
        if is_existed and is_existed.expire_date <= datetime.datetime.now():
            back_dir["code"] = 0
            back_dir["msg"] = "session[" + is_existed.session_key + "]已失效"
            request.session.flush()
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


def index(request):
    back_dir = dict(code=1000, msg="", data=dict())
    # all_parent_pst_classes = PositionClass.objects.filter(is_root=True).all()
    all_pst_classes = PositionClass.objects.filter().all()
    is_log_in = False
    try:
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        print("当前登陆用户：", user.username)
        is_log_in = True
    except:
        JsonResponse(dict(code=10, msg="匿名用户"))

    pst_all = []
    for pst in all_pst_classes:
        pst_all.append(PositionClassMapper(pst).as_dict())

    if is_log_in:
        user_dic = UserMapper(user).as_dict()
    else:
        user_dic = {}

    post_list = Recruitment.objects.filter(post_limit_time__lte=datetime.datetime.now()).order_by("-post_limit_time")
    if post_list.count() >= 7:
        post_list = post_list[:7]

    position_list = []
    for rcm in post_list:
        # 这个职位的发布公司的选择的标签
        post = rcm.position
        enterprise_id = post.enterprise.id
        tags_chosen = TaggedWhatever.objects.filter(object_id=int(enterprise_id.id))
        tags_existed_ids = [tg.tag.slug for tg in tags_chosen]
        tags_rd = rd.sample(tags_existed_ids, 3)
        pst_dict = dict()

        pst_dict["id"] = rcm.id
        pst_dict["image"] = str(post.enterprise.logo)
        pst_dict["pst_title"] = post.name()
        for idx, label in JOB_NATURE_CHOICES:
            if rcm.job_nature is idx:
                nature = label
        for idx, label in YEAR_CHOICES:
            if rcm.job_experience is idx:
                exp = label
        pst_dict["sub_title"] = str(nature) + "|" + str(exp)
        pst_dict["labels"] = tags_rd

        position_list.append(pst_dict)

    import os
    for root_name, b, children in os.walk("static/img/sys-img/ptn/"):
        partner_logo = dict(root_name=root_name, children=children)

    carousel = ["/static/img/sys-img/crs-01.jpg", "/static/img/sys-img/crs-02.jpg",
                "/static/img/sys-img/crs-03.jpg"]

    code = ["/static/img/sys-img/code-video.jpeg", "/static/img/sys-img/code-pub.jpeg"]

    site_logo = "/static/img/logo_favicon.png"

    footer = dict(logo="/static/img/1631606466375_.pic_hd.jpg", code="11010802033541", desc="京公网安备 11010802033541号")

    back_dir["data"] = dict(all_pst_classes=pst_all, user=user_dic, is_log_in=is_log_in, rec_pst_list=position_list,
                            partner_logo=partner_logo, carousel=carousel, QR_code=code, site_logo=site_logo,
                            footer=footer)
    # return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})
    return JsonResponse(back_dir)
    from django.views.generic import TemplateView

    # return render(request, "index.html", locals())


class ContactUsView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = dict()
        data["beijing"] = dict(location="北京",
                               phone="18610218901",
                               address="北京市海淀区东升科技园B2-103",
                               image="/static/img/sys-img/build-beijing.jpg",
                               url="www.zhinengzhizaoedu.com",
                               coordinates=[116.362698, 40.051569])
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


class TrainingPage(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = dict()
        data["QRcode"] = "/static/img/sys-img/code-pub.jpeg"
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


class AboutUsView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = dict()
        data[
            "简介"] = "北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。是一家致力于为中国智能制造产业4亿技能型人才提供职业技能培训+专业人力资源全链条服务的综合型教育服务、人力资源服务平台。"
        data["愿景"] = "打造中国最大的产业工人培训平台"
        data["初心"] = "让中国技术人才享受国际化职教培训，为“中国制造2025”提供技术人才保障"
        data["使命"] = "以职业教育助力人力资源 以人力资源指导职业教育"
        data[
            "长简介"] = "本公司依托FESCO优质的客户资源，依据企业用工共性需求，引进德国先进职业教育课程体系。以产教融合、工学融合为指导思想，以服务当地产业为目标。积极联合核心品牌企业、用人企业，吸收现代教育理念，应用现代教育技术，优化课程体系设计与实施，创新培养模式，实现应用型融合式教学。通过适应性本土化改造，让企业、院校及个人接受最贴近实际应用的先进职业培训，并帮助学生实现对口的高质量实习及就业，达到“职业教育培训+人力资源全流程服务”的矩阵集合效果。公司在职业技术人才培训领域持续发力，为合作地区乃至全国输送急缺的高水平、实用性人才，缩小技术人才缺口，为“中国制造2025”及智能制造产业结构升级提供了有力的技术人才保障。"
        data["projects"] = [
            {
                "name": "山西省退役军人职业技能培训",
                "image": "/static/img/sys-img/project/TYJR.jpg",
                "introduction": "根据山西省《关于开展自主就业退役士兵职业技能省级异地培训有关问题的通知》（晋退役军人发〔2020〕36"
                                "号）文件精神，北京智能智造联合外企培训中心承办山西省退役军人职业技能培训的工业机器人专业和软件编程专业。"},
            {
                "name": "智能制造技能人才培养",
                "image": "/static/img/sys-img/project/ZNZZJNRCPY.jpg",
                "introduction": "定岗培训与人才输送，岗位面向：工业机器人方向、智能智造方向、工业互联网方向。并与企业签订就业合作协议，把我们培训出来的学员送到相对应的企业里面去。"},
            {
                "name": "北京市延庆区人社局“服务冬奥世园”大培训项目",
                "image": "/static/img/sys-img/project/FWDASY.jpg",
                "introduction": "根据《延庆区“服务冬奥世园、促进绿色发展”大培训行动方案》（京延办发〔2018〕26"
                                "号），为了满足服务保障冬奥会世园会及延庆绿色发展对技能人才的需求，丰富人才培养的课程资源，提高人才培养质量，北京智能智造联合外企培训中心共同承办该项目的工业机器人系统操作员培训。"},
            {
                "name": "北京市十大高精尖产业技能培训",
                "image": "/static/img/sys-img/project/GJJ.png",
                "introduction": "北京智能智造联合外企培训中心共同承办北京市高精尖产业技能培训中的人工智能、智能装备企业培训。为北汽福田、电控集团等企业提供员工技能培训及后续人才供给。"},
            {
                "name": "公共实训基地建设及运营",
                "image": "/static/img/sys-img/project/GGSXJD.png",
                "introduction": "政府采购公共实训认证基地，综合性、实用性、专业性于一身的新型产业服务平台，面向各地区省内外行业企业、院校和社会培训机构等各类组织，实现高端技能人才培训、工程技术人员继续教育、失业人员再培训、退役军人技能提升培训。"},
            {
                "name": "校企合作-专业共建",
                "image": "/static/img/sys-img/project/XQHZ.jpg",
                "introduction": "北京智能智造与学校对学生进行联合培养，把学校里的学生送到企业里面去。",
            },
            {
                "name": "在职员工技能提升——江铃新能源",
                "image": "/static/img/sys-img/project/ZZYG.png",
                "introduction": "新建厂，采用高自动化率产线进行生产，对新厂技术工人、项目经理、部门骨干人员、科室经理等进行工业机器人操作运维技术技能、领导力等相关培训。",
            }
        ]
        data["teachers"] = [
            {
                "name": "许妍妩 高级讲师",
                "image": "/static/img/sys-img/teachers/xuyanwu.png",
                "introduction": ["毕业于北京航空航天大学，工业硕士学位；",
                                 "拥有10年以上企业项目与培训经验；",
                                 "以产品研发专家和项目经理等角色,进行业务拓展和项目交付，主编教材10余部，3部入选'十三五'规划教材。"]},
            {
                "name": "吴东海 高级讲师",
                "image": "/static/img/sys-img/teachers/jiangzhenming.jpeg",
                "introduction": ["曾就职于福耀集团，参与产线建设、设备升级项目，同时任内训师。曾为多家企业和院校实施过相关培训。",
                                 "12年自动化行业从业经验，擅长自动化领域技术应用与培训。"]
            },
            {
                "name": "姜振明 高级讲师",
                "image": "/static/img/sys-img/teachers/jiangzhenming.jpeg",
                "introduction": ["曾任华晟智造工业机器人高级讲师，负责培训项目策划与实施，曾为国内多所双高校提供师资培训",
                                 "丰富的机器人技术教学经历，擅长四大家族多种品牌机器人的调试应用"]},
            {
                "name": "胡玥 高级讲师",
                "image": "/static/img/sys-img/teachers/huyue.jpeg",
                "introduction": ["国际焊机工程师，曾就职于海纳川负责工艺设备调试项目，较强的工艺背景",
                                 "10年以上设备调试项目经验，擅长电气控制及安川机器人焊接应用 "]
            },
            {
                "name": "鲁一非 中级讲师",
                "image": "/static/img/sys-img/teachers/luyifei.png",
                "introduction": ["负责公司自动化设备产品的研发与调试，实战经验丰富",
                                 "擅长电气控制与PLC领域的技术开发及调试"]},
        ]
        data["业务介绍图"] = {
            "bg_image": ["/static/img/sys-img/yewu-bg-01.jpg", "/static/img/sys-img/yewu-bg-02.jpg"],
            "text": [
                {"name": "工业机器人技能培训",
                 "intro": "德国先进职业教育课程体系，创新考评体系，以考促学"
                 },
                {"name": "产学合作",
                 "intro": "校企联合共建专业，毕业就上岗"
                 },
                {"name": "人力资源服务",
                 "intro": "依托FESCO客户资源，精准匹配，优先面试，快人一步"
                 }
            ]
        }
        data[
            "经营理念"] = "北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。北京智能智造科技有限公司由北京外企视业网技术有限公司（FESCO视业）发起成立，系FESCO集团教育板块之一。"
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


def split_q(q):
    length = len(list(q))
    splited_list = []
    for i in range(length):
        splited_list.append(q[0: i + 1])
        if q[i + 1:] != '':
            splited_list.append(q[i + 1:])
    return splited_list


def compressImage(request):
    # 用户的头像
    picture_list = PersonalInfo.objects.all()
    for cp in picture_list:
        try:
            image = Image.open(cp.image)  # 通过cp.picture 获得图像
        except:
            continue
        print(cp.image)
        width = image.width
        height = image.height
        rate = 1.0  # 压缩率

        # 根据图像大小设置压缩率
        if width >= 2000 or height >= 2000:
            rate = 0.3
        elif width >= 1000 or height >= 1000:
            rate = 0.5
        elif width >= 500 or height >= 500:
            rate = 0.9

        width = int(width * rate)  # 新的宽
        height = int(height * rate)  # 新的高

        image.thumbnail((width, height), Image.ANTIALIAS)  # 生成缩略图
        # image.save('media/' + str(cp.picture), 'JPEG')  # 保存到原路径
        image.save(str(cp.image), 'JPEG')
        print(cp.image)
        cp.save()
        print("已完成")

    picture_list = EnterpriseInfo.objects.all()
    for cp in picture_list:
        try:
            image = Image.open(cp.logo)  # 通过cp.picture 获得图像
        except:
            continue
        print(cp.logo)
        width = image.width
        height = image.height
        rate = 1.0  # 压缩率

        # 根据图像大小设置压缩率
        if width >= 2000 or height >= 2000:
            rate = 0.3
        elif width >= 1000 or height >= 1000:
            rate = 0.5
        elif width >= 500 or height >= 500:
            rate = 0.9

        width = int(width * rate)  # 新的宽
        height = int(height * rate)  # 新的高

        image.thumbnail((width, height), Image.ANTIALIAS)  # 生成缩略图
        # image.save('media/' + str(cp.picture), 'JPEG')  # 保存到原路径
        image.save(str(cp.logo), 'JPEG')
        print(cp.logo)
        cp.save()
        print("已完成")

    return HttpResponse('compress ok')


def getAllPicturesInStatic(request):
    import os
    all = []
    for root_name, b, children in os.walk("static/img/"):
        try:
            partner_logo = dict(root_name=root_name, children=children)
        except:
            continue
        all.append(partner_logo)
    all = dict(all=all)
    return JsonResponse(all)


def compressImageByFile(request):
    import os
    for root_name, b, children in os.walk("static/img/"):
        for child in children:
            img_path = root_name + child
            open_and_compress(img_path)
    return HttpResponse("done")


def open_and_compress(img_path):
    try:
        image = Image.open(img_path)

        width = image.width
        height = image.height
        rate = 1.0  # 压缩率

        # 根据图像大小设置压缩率
        if width >= 2000 or height >= 2000:
            rate = 0.3
        elif width >= 1000 or height >= 1000:
            rate = 0.5
        elif width >= 500 or height >= 500:
            rate = 0.9

        width = int(width * rate)  # 新的宽
        height = int(height * rate)  # 新的高

        image.thumbnail((width, height), Image.ANTIALIAS)  # 生成缩略图
        # image.save('media/' + str(cp.picture), 'JPEG')  # 保存到原路径
        image.save(str(img_path), 'JPEG')
    except:
        return False


from django.db.models import Q


class SearchPositionsView(View):
    def get(self, request, *args, **kwargs):
        # session_exist(request)
        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        post_list = Recruitment.objects.filter(is_closed=False, post_limit_time__gt=datetime.datetime.now()).order_by(
            'post_limit_time')
        try:
            if len(list(post_list)) >= 7:
                post_list = post_list[:7]

            position_list = []
            for post in post_list:
                position_list.append(RecruitmentMapper(post).as_dict())
            data["post_list"] = position_list

        except:
            data["post_list"] = None

        data["has_q"] = False

        education_options = []
        for idx, label in EDUCATION_LEVELS:
            education_options.append(dict(idx=idx, label=label))
        data["education_choices"] = education_options
        cities_options = []
        for idx, label in PROVINCES_CHOICES:
            cities_options.append(dict(idx=idx, label=label))
        data["cities_options"] = cities_options
        salary_unit_options = []
        for idx, label in TIME_UNIT_CHOICES:
            salary_unit_options.append(dict(idx=idx, label=label))
        data["salary_unit_options"] = salary_unit_options
        exp_options = []
        for idx, label in YEAR_CHOICES:
            exp_options.append(dict(idx=idx, label=label))
        data["exp_options"] = exp_options
        job_nature_options = []
        for idx, label in JOB_NATURE_CHOICES:
            job_nature_options.append(dict(idx=idx, label=label))
        data["job_nature_options"] = job_nature_options
        pst_class_options = PositionClass.objects.filter(is_root=False).all()
        position_class = []
        for pst in pst_class_options:
            position_class.append(PositionClassMapper(pst).as_dict())
        data["position_class"] = position_class

        staff_size_options = []
        for opt in NumberOfStaff.objects.all():
            staff_size_options.append(NumberOfStaffMapper(opt).as_dict())
        data["staff_size_options"] = staff_size_options

        financial_options = []
        for idx, label in FINANCING_STATUS_CHOICES:
            financial_options.append(dict(idx=idx, label=label))
        data["financial_options"] = financial_options

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        # session_exist(request)
        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        q = request.GET.get('q')

        lst = split_q(q)
        data["query"] = q
        if q is None:
            post_list = Recruitment.objects.order_by('post_limit_time')
            try:
                if len(list(post_list)) >= 7:
                    post_list = post_list[:7]

                position_list = []
                for post in post_list:
                    position_list.append(RecruitmentMapper(post).as_dict())
                data["post_list"] = position_list

            except:
                data["post_list"] = None
            data["has_q"] = False
        else:
            post_list = Recruitment.objects.filter(
                Q(position__pst_class__name__in=lst) |
                Q(position__fullname__in=lst) |
                Q(enterprise__name__in=lst) |
                Q(enterprise__name__icontains=q) |
                Q(post_limit_time__gt=datetime.datetime.now())
            )

            position_list = []
            for post in post_list:
                position_list.append(RecruitmentMapper(post).as_dict())
            data["post_list"] = position_list

            data["has_q"] = True

        education_options = []
        for idx, label in EDUCATION_LEVELS:
            education_options.append(dict(idx=idx, label=label))
        data["education_choices"] = education_options
        cities_options = []
        for idx, label in PROVINCES_CHOICES:
            cities_options.append(dict(idx=idx, label=label))
        data["cities_options"] = cities_options
        salary_unit_options = []
        for idx, label in TIME_UNIT_CHOICES:
            salary_unit_options.append(dict(idx=idx, label=label))
        data["salary_unit_options"] = salary_unit_options
        exp_options = []
        for idx, label in YEAR_CHOICES:
            exp_options.append(dict(idx=idx, label=label))
        data["exp_options"] = exp_options
        job_nature_options = []
        for idx, label in JOB_NATURE_CHOICES:
            job_nature_options.append(dict(idx=idx, label=label))
        data["job_nature_options"] = job_nature_options
        pst_class_options = PositionClass.objects.filter(is_root=False).all()
        position_class = []
        for pst in pst_class_options:
            position_class.append(PositionClassMapper(pst).as_dict())
        data["position_class"] = position_class

        staff_size_options = []
        for opt in NumberOfStaff.objects.all():
            staff_size_options.append(NumberOfStaffMapper(opt).as_dict())
        data["staff_size_options"] = staff_size_options

        financial_options = []
        for idx, label in FINANCING_STATUS_CHOICES:
            financial_options.append(dict(idx=idx, label=label))
        data["financial_options"] = financial_options

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})


class LoginView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = {
            "bg-img": "/static/img/login-bg-01.jpg",
            "logo": "/static/img/logo_prise.png",
            "logo-white": "/static/img/logo_white.png"
        }
        back_dic["data"] = data
        # return render(request, "login.html")
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')

        username = request.POST.get("username")
        password = request.POST.get("password")
        # data = json.loads(request.body)
        # username = data.get('username')
        # password = data.get('password')

        print(username, password)
        user_obj = auth.authenticate(username=username, password=password)
        if user_obj:
            auth.login(request, user_obj)
            back_dic['url'] = '../'
            session_k = request.session.session_key
            request.session.set_expiry(60 * 60)
            back_dic["skey"] = session_k
            back_dic["msg"] = "你用于登陆的用户是" + str(user_obj) + ", 当前session指向用户" \
                              + User.objects.get(id=request.session.get('_auth_user_id')).username
            print("ok")
        else:
            back_dic['code'] = 2000
            back_dic['msg'] = '用户名或密码错误'
        return JsonResponse(back_dic)


from rest_framework.views import APIView
from rest_framework.response import Response
from user import api_wx
from django.core.cache import cache
import hashlib, time
from .models import User_WxID


class LoginWxView(APIView):
    def post(self, request):
        # 从前端拿code
        # param = request.data
        param = json.loads(request.body.decode())
        if not param["code"]:
            # return Response({'status': 1, "msg": "缺少参数"})
            return JsonResponse(dict(code=1001, msg="缺少参数，没有code"))
        # elif not param["code_mobile"]:
        #     return JsonResponse(dict(code=1001, msg="缺少参数，没有code_mobile"))
        else:
            '''换取手机号'''
            if not is_null(param["code_mobile"]):
                phone_res = api_wx.get_user_phone(param["code_mobile"])
                if phone_res:
                    phone_number = phone_res["phone_info"]["purePhoneNumber"]
                    print(phone_number)
                    is_exist = PersonalInfo.objects.filter(phone_number=phone_number)
                    if is_exist.exists():
                        this_user = is_exist.first()
                        this_user_id = this_user.id_id
                        print(this_user_id)
                        this_user = User.objects.get(id=this_user_id)
                        auth.login(request, this_user)
                        session_k = request.session.session_key
                        request.session.set_expiry(60 * 60)
                        msg = "已存在绑定用户，登陆成功"
                        return JsonResponse(dict(code=1000, msg=msg,
                                                 s_key=session_k))
            '''换取session key'''
            code = param['code']
            user_data = api_wx.get_login_info(code)
            if user_data:
                val = user_data['session_key'] + "&" + user_data['openid']
                md5 = hashlib.md5()
                md5.update(str(time.clock()).encode('utf-8'))
                md5.update(user_data['session_key'].encode('utf-8'))
                key = md5.hexdigest()
                cache.set(key, val)
                # 是否该用户已存在
                has_user = User_WxID.objects.filter(wx_id=user_data["openid"]).first()
                # has_user = Wxuser.objects.filter(openid=user_data['openid']).first()
                if not has_user:
                    # Wxuser.objects.create(openid=user_data['openid'])
                    default_pw = "wx" + str(rd.randint(10000, 99999))
                    new_user = User.objects.create(username=user_data["nickname"], password=default_pw)
                    PersonalInfo.objects.create(pk=new_user.id, phone_number=param["code_mobile"])
                    auth.login(request, new_user)
                    session_k = request.session.session_key
                    print(request.session)
                    request.session.set_expiry(60 * 60)
                    # User_WxID.objects.create(wx_id=user_data['openid'], user_id=new_user)
                    User_WxID.objects.create(wx_id=user_data['openid'], user_id=new_user.id)
                    msg = "已经创建用户，初始密码为" + default_pw
                else:
                    this_user = User.objects.get(id=has_user.user_id.id)
                    auth.login(request, this_user)
                    session_k = request.session.session_key
                    print(request.session)
                    request.session.set_expiry(60 * 60)
                    msg = "已存在绑定用户，登陆成功"

                User_WxID.objects.update()

                return JsonResponse(dict(code=1000, msg=msg,
                                         key=key, s_key=session_k))
            else:
                return JsonResponse(dict(code=1002, msg="无效的code"))



class LoginMsgView(View):
    def get(self, request, *args, **kwargs):
        """没有get方法"""
        return 1

    def post(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='', url='')

        data = json.loads(request.body.decode())
        """1:发送验证码；2:检查验证码"""
        if data["type"] == "1":
            mobile = data["mobile"]
            port_head = "https://inolink.com/ws/BatchSend2.aspx?"
            username = "tclkj03236"
            password = "123456@"
            msg_head = "您的验证码为"
            code = rd.randint(1000, 9999)
            sign = "，该验证码有效期为10分钟。【智能智造科技】"
            message = msg_head + str(code) + sign
            message_gb = urllib.parse.quote(message.encode("gb2312"))

            url = port_head + "CorpId=" + username + "&Pwd=" + password + "&Mobile=" + mobile \
                  + "&Content=" + message_gb + "&SendTime=&cell="
            r = requests.get(url).json()
            r.encoding = "utf-8"

            reply_code = int(r)
            if reply_code > 0:
                back_dic["code"] = 1000
                back_dic["msg"] = "短信发送成功"
                WxUserPhoneValidation.objects.create(unvalid_phone_number=mobile, valid_code=str(code))
            else:
                back_dic["code"] = 1001
                back_dic["msg"] = "错误码" + str(reply_code) + "，请联系管理员"
        elif data["type"] == "2":
            unchecked_code = data["code"]
            phone_number = data["mobile"]
            code_obj = WxUserPhoneValidation.objects.filter(unvalid_phone_number=phone_number).order_by("-valid_datetime").first()

            expired_time = code_obj.valid_datetime + datetime.timedelta(minutes=10)
            if datetime.datetime.now() > expired_time:
                is_expired = True
            else:
                is_expired = False

            if code_obj and not is_expired:
                if unchecked_code == code_obj.valid_code:
                    """此处需要创建一个用户"""
                    username = "MB" + get_random_string(length=16)
                    password = make_password(phone_number)
                    email = ""
                    """查找这个手机号是否存在"""
                    existed_user = PersonalInfo.objects.filter(phone_number=phone_number)
                    if existed_user.exists():
                        """存在: 登陆相应账号"""
                        this_user = User.objects.get(id=existed_user.first().id_id)
                        auth.login(request, this_user)
                        session_k = request.session.session_key
                        print(request.session)
                        request.session.set_expiry(60 * 60)
                        back_dic["skey"] = session_k
                        back_dic["code"] = 1000
                        back_dic["msg"] = "验证成功, 该手机号相关用户已存在, 已登陆"
                    else:
                        """不存在 创建新账号"""
                        user_obj = User.objects.create(username=username, password=password, email=email)
                        User_info = PersonalInfo.objects.create(id_id=user_obj.id, phone_number=phone_number)
                        # user_obj = auth.authenticate(username=username, password=password)
                        if user_obj:
                            auth.login(request, user_obj)
                            session_k = request.session.session_key
                            print(request.session)
                            request.session.set_expiry(60 * 60)
                            back_dic["skey"] = session_k
                            back_dic["code"] = 1000
                            back_dic["msg"] = "验证成功, 已为您创建用户, 初始密码为手机号"
                else:
                    back_dic["code"] = 1002
                    back_dic["msg"] = "验证码不正确"
            else:
                back_dic["code"] = 1003
                back_dic["msg"] = "验证码已过期，请重新验证"

        return JsonResponse(back_dic)


class LoginEnterPriseView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='', data=dict())
        data = {
            "bg-img": "/static/img/login-bg-01.jpg",
            "logo": "/static/img/logo_prise.png",
            "logo-white": "/static/img/logo_white.png"
        }
        back_dic["data"] = data
        # return render(request, "login.html")
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        username = request.POST.get("username")
        password = request.POST.get("password")
        user_obj = auth.authenticate(request, username=username, password=password)
        if user_obj:
            auth.login(request, user_obj)
            print("ook")
            back_dic['url'] = '../enterprise/index/'
            session_k = request.session.session_key
            request.session.set_expiry(60 * 60)
            back_dic["skey"] = session_k
            print("ok")
        else:
            back_dic['code'] = 2000
            back_dic['msg'] = '用户名或密码错误'
        return JsonResponse(back_dic)
        # return render(request, 'login.html')


class RegisterView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='', data=dict())
        data = {
            "bg-img": "/static/img/register-bg-01.jpg",
            "logo": "/static/img/logo_prise.png",
            "logo-white": "/static/img/logo_white.png"
        }
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})
        # return render(request, "register.html")

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        back_dir = dict(code=1000, msg='', url='/register/')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        data = [username, password, confirm_password, email]
        if ('' or None) in [username, password, confirm_password, email]:
            back_dir['code'] = 3000
            back_dir['msg'] = '请填写所有字段'
        elif User.objects.filter(username=username):
            back_dir['code'] = 4000
            back_dir['msg'] = '用户名已存在'
        elif len('password') <= 6:
            back_dir['code'] = 5000
            back_dir['msg'] = '密码过短'
        elif password != confirm_password:
            back_dir['code'] = 6000
            back_dir['msg'] = '两次输入密码不一致'
        elif not ValidateEmail(email):
            back_dir['code'] = 7000
            back_dir['msg'] = '请输入正确格式的邮箱'
        else:
            password = make_password(password)
            User.objects.create(username=username, password=password, email=email)
            print(username, password, email)
            back_dir['url'] = '/login/'
            back_dir['msg'] = '注册成功，跳转登陆页面'
        data = [username, password, confirm_password, email]
        back_dir["data"] = data
        return JsonResponse(back_dir)


"""在企业端还没做logout，20210525"""


def logout(request):
    try:
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        username = user.username
        session.delete()
    except:
        username = "匿名用户"
    auth.logout(request)
    return JsonResponse(dict(code=1000, msg="用户名为【" + str(username) + '】的用户已退出', url='../'))


def home(request):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dir = dict(code=1000, msg="", data=dict())
    data = dict()

    try:
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        print("当前登陆用户：", user.username)
        data["user"] = UserMapper(user).as_dict()
    except:
        data["user"] = {}
        back_dir["data"] = data
        back_dir["msg"] = "匿名用户"
        back_dir["code"] = 10
        return JsonResponse(back_dir)

    d1 = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    d2 = datetime.datetime.strptime(user.date_joined.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    days = (d1 - d2).days + 1
    data["days"] = str(days)

    try:
        personal = PersonalInfo.objects.filter(id=user.id).first()
        data["personal"] = PersonalInfoMapper(personal).as_dict()
    except:
        personal = None
        data["personal"] = {}

    if personal:
        has_personal = 1
        items = {'last_name': personal.id.last_name, 'first_name': personal.id.first_name,
                 'phone': personal.phone_number, 'qq': personal.qq_number, 'sex': personal.sex,
                 'nation': personal.nation, 'date_of_birth': personal.date_of_birth, 'height': personal.height,
                 'weight': personal.weight, 'postcode': personal.postcode, 'home_address': personal.home_address,
                 'birth_address': personal.birth_address, 'martial': personal.martial_status,
                 'education': personal.education, 'image': personal.image}
        ratio = 0
        for item in items:
            if not (items[item] == '' or items[item] is None):
                ratio += 1
        ratio = round(ratio / len(items), 4) * 100

        update_date_pi = personal.update_date
    else:
        has_personal = 0
        ratio = 0
        update_date_pi = ""
    data["has_personal"] = has_personal
    data["ratio"] = ratio
    data["update_date_pi"] = str(update_date_pi)

    try:
        job = user.personalinfo.jobexperience_set.order_by('-start_date')
        num_job = len(job)
    except:
        job = None
        num_job = 0
    try:
        edu = user.personalinfo.educationexperience_set.order_by('-start_date')
        num_edu = len(edu)
    except:
        edu = None
        num_edu = 0
    try:
        tra = user.personalinfo.trainingexperience_set.order_by('-start_date')
        num_tra = len(tra)
    except:
        tra = None
        num_tra = 0
    data["num_job"] = num_job
    data["num_edu"] = num_edu
    data["num_tra"] = num_tra

    try:
        cvs = user.cv_set.order_by('create_time')
        num_cv = len(cvs)
    except:
        cvs = None
        num_cv = 0
    data["num_cv"] = num_cv

    if cvs:
        cv_temp = user.cv_set.order_by('create_time')
        for cv in cv_temp:
            first_create_time = cv.create_time
            break
        cv_temp = user.cv_set.order_by('-update_time')
        for cv in cv_temp:
            last_modify_date = cv.update_time
            intention_id = cv.cv_positionclass_set.get().position_class_id_id
            intention_name = PositionClass.objects.get(id=intention_id).name
            break
    else:
        first_create_time = None
        last_modify_date = None
        intention_name = None

    data["first_create_time"] = first_create_time
    data["last_modify_date"] = last_modify_date
    data["last_modify_job_intention"] = intention_name

    back_dir["data"] = data
    return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})
    # return render(request, 'user/home.html', locals())

def my_page_dic(request):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dir = dict(code=1000, msg="", data=dict())
    data = dict()

    try:
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        print("当前登陆用户：", user.username)
        # data["user"] = UserMapper(user).as_dict()
    except:
        data["user"] = {}
        back_dir["data"] = data
        back_dir["msg"] = "匿名用户"
        back_dir["code"] = 10
        return JsonResponse(back_dir)

    cv_list = []
    my_cvs = CV.objects.filter(user_id=user.id)
    for cv in my_cvs:
        cv_list.append(CvMapper(cv).as_dict())
    # data["my_cvs"] = cv_list
    data["num_cv"] = len(cv_list)

    my_cvs_id = [c.id for c in my_cvs]
    my_applications = Applications.objects.filter(cv_id__in=my_cvs_id)
    app_list = []
    for app in my_applications:
        app_list.append(ApplicationsMapper(app).as_dict())
    # data["my_applications"] = app_list
    data["num_application"] = len(app_list)

    try:
        personal = PersonalInfo.objects.filter(id=user.id).first()
        # data["personal"] = PersonalInfoMapper(personal).as_dict()
    except:
        personal = None
        # data["personal"] = {}

    if personal:
        has_personal = 1
        items = {'last_name': personal.id.last_name, 'first_name': personal.id.first_name,
                 'phone': personal.phone_number, 'qq': personal.qq_number, 'sex': personal.sex,
                 'nation': personal.nation, 'date_of_birth': personal.date_of_birth, 'height': personal.height,
                 'weight': personal.weight, 'postcode': personal.postcode, 'home_address': personal.home_address,
                 'birth_address': personal.birth_address, 'martial': personal.martial_status,
                 'education': personal.education, 'image': personal.image}
        ratio = 0
        for item in items:
            if not (items[item] == '' or items[item] is None):
                ratio += 1
        ratio = round(ratio / len(items), 4) * 100

        update_date_pi = personal.update_date
    else:
        has_personal = 0
        ratio = 0
        update_date_pi = ""
    data["has_personal"] = has_personal
    data["complete_ratio"] = ratio

    back_dir["data"] = data

    return JsonResponse(back_dir)

def edit_password(request):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
    back_dir = {'code': 1000, 'msg': ''}
    data = dict()

    try:
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
    except:
        data["user"] = {}
        back_dir["data"] = data
        back_dir["msg"] = "匿名用户"
        back_dir["code"] = 10
        return JsonResponse(back_dir)

    if request.method == "POST":
        para = json.loads(request.body.decode())
        old_psw = para["old_psw"]
        new_psw = para["new_psw"]
        confirm_new_psw = para["confirm_new_psw"]
        print(para)

        is_right = user.check_password(old_psw)
        if is_right:
            if new_psw == confirm_new_psw:
                user.set_password(new_psw)
                user.save()
                print('ook')
                back_dir['msg'] = '修改成功, 请重新登陆'
                back_dir['url'] = '/login/'

            else:
                back_dir['code'] = 1001
                back_dir['msg'] = '两次密码不一致'
        else:
            back_dir['code'] = 1002
            back_dir['msg'] = '旧密码错误'

    back_dic = back_dir
    return JsonResponse(back_dic)


# return render(request, 'user/home.html', locals())


class EditSelfInfoView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        sex_choices = []
        for idx, label in SEX_CHOICE:
            sex_choices.append(dict(idx=idx, label=label))
        nations_choices = []
        for idx, label in NATIONS:
            nations_choices.append(dict(idx=idx, label=label))
        province_choices = []
        for idx, label in PROVINCES_CHOICES:
            province_choices.append(dict(idx=idx, label=label))
        martial_choices = []
        for idx, label in MARTIAL_CHOICES:
            martial_choices.append(dict(idx=idx, label=label))
        education_choices = []
        for idx, label in EDUCATION_LEVELS:
            education_choices.append(dict(idx=idx, label=label))
        data["sex_choices"] = sex_choices
        data["nations_choices"] = nations_choices
        data["province_choices"] = province_choices
        data["martial_choices"] = martial_choices
        data["education_choices"] = education_choices
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        data["user"] = UserMapper(user).as_dict()

        PER_valid = PersonalInfo.objects.filter(id_id=user.id)
        if not PER_valid:
            PersonalInfo.objects.create(id_id=user.id)
        data["personal"] = PersonalInfoMapper(user.personalinfo).as_dict()
        data["personal"]["age"] = calculate_age(user.personalinfo.date_of_birth)

        try:
            eva = user.personalinfo.evaluation
        except:
            eva = Evaluation.objects.create(id=user.personalinfo, self_evaluation="暂无自我评价")
        data["eva"] = EvaMapper(eva).as_dict()

        job_info_set = []
        job = user.personalinfo.jobexperience_set.order_by('-start_date')
        for j in job:
            job_info_set.append(JobExMapper(j).as_dict())

        tra_info_set = []
        tra = user.personalinfo.trainingexperience_set.order_by('-start_date')
        for t in tra:
            tra_info_set.append(TraExMapper(t).as_dict())

        edu_info_set = []
        edu = user.personalinfo.educationexperience_set.order_by('-start_date')
        for e in edu:
            edu_info_set.append(EduExMapper(e).as_dict())
        data["job_info_set"] = job_info_set
        data["edu_info_set"] = edu_info_set
        data["tra_info_set"] = tra_info_set

        position_class_choices = []
        position_class = PositionClass.objects.all()
        for pst in position_class:
            position_class_choices.append(PositionClassMapper(pst).as_dict())
        data["position_class_choices"] = position_class_choices

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dic = dict(code=1000, msg="成功了", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        PER_valid = PersonalInfo.objects.filter(id_id=user.id)
        if not PER_valid:
            PersonalInfo.objects.create(id_id=user.id)

        try:
            edit_type = json.loads(request.body.decode())["type"]
        except:
            edit_type = request.POST.get('type')

        print(edit_type)
        edit_type = str(edit_type)

        if edit_type == "101":
            para = json.loads(request.body.decode())
            print("参数", para)
            """contact information edit"""
            last_name = para["last_name"]
            first_name = para["first_name"]
            phone = para["phone"]
            qq = para["qq"]
            try:
                email = para["email"]
                has_email = True
            except:
                has_email = False

            if has_email:
                if ValidateEmail(email):
                    user.email = email
                else:
                    back_dic["code"] = 10011
                    back_dic["msg"] = "非法邮箱格式"

            # 存储姓，名
            if re.compile('[0-9]+').findall(last_name) or re.compile('[0-9]+').findall(first_name):
                back_dic["code"] = 10010
                back_dic["msg"] = "姓名中含有非法字符（数字）"
            else:
                user.last_name = last_name
                user.first_name = first_name

            # 手机号判断
            if phone in [None, ""] or (phone.isdigit() and len(phone) == 11):
                user.personalinfo.phone_number = phone
            else:
                back_dic['code'] = 1001
                back_dic['msg'] = '请输入正确的手机号码'

            # qq号判断
            if qq in [None, ""] or qq.isdigit():
                user.personalinfo.qq_number = qq
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '请输入正确的QQ号码'

            user.save()
            user.personalinfo.save()
        elif edit_type == "102":
            """avatar edit"""
            try:
                file_obj = request.FILES.get('name_avatar')
                user.personalinfo.image = file_obj
                user.personalinfo.save()
                back_dic["msg"] = "头像修改成功了"
            except:
                back_dic["code"] = 10201
                back_dic["msg"] = "unknown error, refresh and try again"
        elif edit_type == "103":
            para = json.loads(request.body.decode())
            print("参数", para)
            """self-info edit"""
            sex = para["sex"]
            nation = para["nation"]
            date_of_birth = para["date_of_birth"]
            height = para["height"]
            weight = para["weight"]
            postcode = para["postcode"]
            home_address = para["home_address"]
            birth = para["birth_address"]
            martial = para["martial"]

            if not sex or sex in ["", "null"]:
                user.personalinfo.sex = None
            elif sex in ["0", "1"]:
                user.personalinfo.sex = int(sex)
            else:
                back_dic['code'] = 1003
                back_dic['msg'] = '请从备选选项中选择性别'
            # 民族
            try:
                if nation is None or nation in ["", "null"]:
                    user.personalinfo.nation = 0
                else:
                    for idx, opt in NATIONS:
                        if idx == int(nation):
                            user.personalinfo.nation = int(nation)
            except:
                back_dic['code'] = 10032
                back_dic['msg'] = '请从备选选项中选择您的民族'

            # 生日
            if date_of_birth in ['', None]:
                user.personalinfo.date_of_birth = None
            else:
                try:
                    user.personalinfo.date_of_birth = date_of_birth
                except:
                    back_dic['code'] = 10031
                    back_dic['msg'] = '出生日期格式不正确，请刷新重试'

            # 身高判断
            if height.isdigit():
                user.personalinfo.height = height
            elif height in [None, "", "null"]:
                user.personalinfo.height = None
            else:
                back_dic['code'] = 1004
                back_dic['msg'] = '请输入正确的身高（只输入数字即可），单位：厘米（cm）'
            # 体重判断
            if is_number(weight):
                user.personalinfo.weight = weight
            elif weight in [None, "", "null"]:
                user.personalinfo.weight = None
            else:
                back_dic['code'] = 1005
                back_dic['msg'] = '请输入正确的体重（只输入数字即可），单位：千克（kg），可保留一位小数'
            # 邮编判断
            if postcode in [None, ""] or postcode.isdigit():
                user.personalinfo.postcode = postcode
            else:
                back_dic['code'] = 1006
                back_dic['msg'] = '请输入正确的邮编'
            # 家庭住址
            if home_address in [None, ""] or len(home_address) <= 50:
                user.personalinfo.home_address = home_address
            else:
                back_dic['code'] = 10061
                back_dic['msg'] = '地址太长了！'
            # 出生地/籍贯
            if birth in [None, "", "null"]:
                user.personalinfo.birth_address = None
            else:
                try:
                    for idx, opt in PROVINCES_CHOICES:
                        if idx == int(birth):
                            user.personalinfo.birth_address = int(birth)
                except:
                    back_dic['code'] = 10062
                    back_dic['msg'] = '请从备选选项中选择你的出生地（籍贯）'
            # 婚姻状况判断
            if martial in [None, "", "null"]:
                user.personalinfo.martial_status = None
            else:
                try:
                    if int(martial) == 0:
                        user.personalinfo.martial_status = 0
                    else:
                        user.personalinfo.martial_status = 1
                except:
                    back_dic['code'] = 1007
                    back_dic['msg'] = '请从备选选项中选择您的婚姻状况'

            user.save()
            user.personalinfo.save()
            if back_dic["code"] == 1000:
                back_dic["msg"] = "基本信息修改成功"
        elif edit_type == "104":
            """education level edit"""
            edu = json.loads(request.body.decode())["edu"]
            # 学历判断
            try:
                user.personalinfo.education = int(edu)
            except:
                back_dic['code'] = 1009
                back_dic['msg'] = '请从备选选项中选择您的最高学历'

            user.save()
            user.personalinfo.save()
            if back_dic["code"] == 1000:
                back_dic["msg"] = "学历修改成功了"
        elif edit_type in ["1051", "1052", "1053"]:
            """job experience edit"""
            if edit_type == "1051":
                """edit"""
                para = json.loads(request.body.decode())
                job_object = JobExperience.objects.get(id=int(para['id']))
                back_dic = job_is_valid(para)
                if back_dic["code"] == 1000:
                    job_object.start_date = para['start']
                    job_object.end_date = para['end']
                    job_object.enterprise = para['enterprise']
                    job_object.position = PositionClass.objects.get(id=int(para['position']))
                    job_object.job_content = para['content']
                    job_object.save()
                    back_dic["msg"] = "工作经历编辑成功"
                else:
                    return JsonResponse(back_dic)
            elif edit_type == "1052":
                """delete"""
                para = json.loads(request.body.decode())
                JobExperience.objects.filter(id=int(para['id'])).delete()
                back_dic['msg'] = '工作经历删除成功'
            elif edit_type == "1053":
                """create"""
                para = json.loads(request.body.decode())
                para["type"] = "102"
                # para = {'type': '102', 'start': request.POST.get('start'), 'end': request.POST.get('end'),
                #         'enterprise': request.POST.get('enterprise'), 'position': request.POST.get('position'),
                #         'content': request.POST.get('content')}
                back_dic = job_is_valid(para)
                if back_dic['code'] == 1000:
                    start_date = para["start"]
                    end_date = para["end"]
                    enterprise = para["enterprise"]
                    # location = request.POST.get('location')
                    position = para["position"]
                    content = para["content"]
                    JobExperience.objects.create(user_id_id=user.personalinfo.id_id, start_date=start_date,
                                                 end_date=end_date,
                                                 enterprise=enterprise,
                                                 position=PositionClass.objects.get(id=int(position)),
                                                 job_content=content)
                    back_dic['msg'] = '工作经历新增成功'
            else:
                return JsonResponse(back_dic)
        elif edit_type in ["1061", "1062", "1063"]:
            """training experience edit"""
            if edit_type == "1061":
                """edit"""
                para = json.loads(request.body.decode())
                tra_object = TrainingExperience.objects.get(id=int(para['id']))
                back_dic = tra_is_valid(para)
                if back_dic['code'] == 1000:
                    tra_object.start_date = para['start']
                    tra_object.end_date = para['end']
                    tra_object.training_team = para['team']
                    tra_object.training_name = para['content']
                    tra_object.save()
                    back_dic["msg"] = "培训经历修改成功"
            elif edit_type == "1062":
                """delete"""
                para = json.loads(request.body.decode())
                TrainingExperience.objects.filter(id=int(para['id'])).delete()
                back_dic['msg'] = '培训经历删除成功'
            elif edit_type == "1063":
                """create"""
                para = json.loads(request.body.decode())
                para["type"] = "301"
                # para = {'type': '301',
                #         'start': request.POST.get('start'), 'end': request.POST.get('end'),
                #         'team': request.POST.get('team'), 'content': request.POST.get('content')}
                back_dic = tra_is_valid(para)
                if back_dic['code'] == 1000:
                    start_date = para["start"]
                    end_date = para["end"]
                    enterprise = para["team"]
                    content = para["content"]
                    TrainingExperience.objects.create(user_id_id=user.personalinfo.id_id, start_date=start_date,
                                                      end_date=end_date, training_name=content,
                                                      training_team=enterprise)
                    back_dic['msg'] = '培训新增成功'
            else:
                return JsonResponse(back_dic)
        elif edit_type in ["1071", "1072", "1073"]:
            """education experience edit"""
            if edit_type == "1071":
                """edit"""
                para = json.loads(request.body.decode())
                edu_object = EducationExperience.objects.get(id=int(para['id']))
                back_dic = edu_is_valid(para)
                if back_dic["code"] == 1000:
                    edu_object.start_date = para['start']
                    edu_object.end_date = para['end']
                    edu_object.school = para['school']
                    edu_object.department = para['department']
                    edu_object.major = para['major']
                    edu_object.education = int(para["edu"])
                    edu_object.save()
                    back_dic['msg'] = '教育经历修改成功'
            elif edit_type == "1072":
                """delete"""
                para = json.loads(request.body.decode())
                EducationExperience.objects.filter(id=int(para['id'])).delete()
                back_dic['msg'] = '教育经历删除成功'
            elif edit_type == "1073":
                """create"""
                para = json.loads(request.body.decode())
                para["type"] = "201"
                # para = {'type': '201', 'start': request.POST.get('start'), 'end': request.POST.get('end'),
                #         'school': request.POST.get('school'), 'department': request.POST.get('department'),
                #         'major': request.POST.get('major'),
                #         'edu': request.POST.get('edu')}
                print(para)
                back_dic = edu_is_valid(para)
                if back_dic['code'] == 1000:
                    start_date = para["start"]
                    end_date = para["end"]
                    school = para["school"]
                    department = para["department"]
                    major = para["major"]
                    EducationExperience.objects.create(user_id_id=user.personalinfo.id_id,
                                                       start_date=start_date,
                                                       end_date=end_date, school=school, department=department,
                                                       major=major, education=int(para["edu"]))

                    back_dic['msg'] = '教育经历新增成功'
            else:
                return JsonResponse(back_dic)
        elif edit_type == "108":
            """evaluation edit"""
            try:
                Evaluation.objects.create(id_id=user.personalinfo.id_id)
            except:
                pass

            eva_content = json.loads(request.body.decode())["content"]
            if len(eva_content) >= 50:
                back_dic["code"] = 10080
                back_dic["msg"] = "自我评价过长！请限制在50字以内"
            else:
                user.personalinfo.evaluation.self_evaluation = eva_content
                user.personalinfo.evaluation.save()
                if back_dic["code"] == 1000:
                    back_dic["msg"] = "修改评价成功"
        else:
            back_dic["msg"] = "错误传值！！！速速联系管理员"

        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


class EditCvView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        cv_list = user.cv_set.order_by('-update_time')
        industry_list = Field.objects.filter(is_root=True)
        position_class = PositionClass.objects.filter()

        skill_levels = []
        for idx, label in SKILL_CHOICES:
            skill_levels.append(dict(idx=idx, label=label))
        data["skill_levels"] = skill_levels

        cv_contains = []
        for cv in cv_list:
            cv_contains.append(CvMapper(cv).as_dict())
        data["cv_list"] = cv_contains

        industry_contains = []
        for ind in industry_list:
            industry_contains.append(FieldMapper(ind).as_dict())
        data["industry_list"] = industry_contains

        pst_contains = []
        for pst in position_class:
            pst_contains.append(PositionClassMapper(pst).as_dict())
        data["position_class"] = pst_contains

        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dic = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        para = json.loads(request.body.decode())
        if para['type'] == '401':
            # 修改CV
            cv_object = CV.objects.get(id=int(para['id']))
            back_dic = cv_is_valid(para)
            if back_dic['code'] == 1000:
                if para['industry'] == '':
                    cv_object.industry_id = None
                else:
                    industry_this = Field.objects.get(id=int(para['industry']))
                    cv_object.industry_id = industry_this.id
                    print("here")
                cv_object.major = para['major']
                cv_object.courses = para['course']
                # intention_obj = CV_PositionClass.objects.get(cv_id=int(para['id']))
                # intention_obj.position_class_id = int(para['intention'])
                # intention_obj.save()
                cv_object.english_skill = int(para["english"])
                cv_object.computer_skill = int(para["computer"])
                cv_object.expected_salary = int(para['salary'])
                cv_object.professional_skill = para['pro']
                cv_object.award = para['award']
                cv_object.talent = para['talent']
                cv_object.save()
                back_dic["msg"] = "修改成功"
            # return JsonResponse(back_dic)
        elif para["type"] == "4011":
            # 要星标的简历
            cv_obj = CV.objects.get(id=int(para['id']))
            # 已经被星标的简历
            cv_alrs = user.cv_set.filter(is_staring=True)
            if cv_alrs.exists():
                for cv in cv_alrs:
                    cv.is_staring = False
                    cv.save()
            cv_obj.is_staring = True
            cv_obj.save()
            back_dic["msg"] = "已设为唯一星标简历"

        elif para['type'] == "403":
            CV.objects.filter(id=int(para['id'])).delete()
            back_dic['msg'] = '已删除'
            # return JsonResponse(back_dic)
        elif para["type"] == "402":
            back_dic = cv_is_valid(para)

            if back_dic["code"] == 1000:
                major = para["major"]
                courses = para["course"]
                intention = PositionClass.objects.get(id=int(para["intention"]))
                salary = para["salary"]
                pro = para["pro"]
                award = para["award"]
                talent = para["talent"]
                industry = Field.objects.get(id=int(para["industry"]))
                new_cv = CV.objects.create(user_id_id=user.id, industry_id=industry.id, major=major,
                                           courses=courses,
                                           english_skill=int(para["english"]),
                                           computer_skill=int(para["computer"]),
                                           expected_salary=int(salary),
                                           professional_skill=pro, award=award, talent=talent)
                CV_PositionClass.objects.create(cv_id=new_cv, position_class_id=intention)
                back_dic['msg'] = '新增成功'
        else:
            back_dic["msg"] = "这是一条假的成功消息"

        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


def find_rcm_by_pst_class(request, pst_class):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    rcm_list = []
    all_rcms = Recruitment.objects.filter(position__pst_class_id=pst_class, is_closed=False).all()
    for rcm in all_rcms:
        rcm_list.append(RecruitmentMapper(rcm).as_dict())
    data["all_rcms"] = rcm_list

    unit_choices = []
    for idx, label in TIME_UNIT_CHOICES:
        unit_choices.append(dict(idx=idx, label=label))
    data["unit_choices"] = unit_choices

    city_choices = []
    for idx, label in PROVINCES_CHOICES:
        city_choices.append(dict(idx=idx, label=label))
    data["city_choices"] = city_choices

    exp_choices = []
    for idx, label in YEAR_CHOICES:
        exp_choices.append(dict(idx=idx, label=label))
    data["exp_choices"] = exp_choices

    financial_choices = []
    for idx, label in FINANCING_STATUS_CHOICES:
        financial_choices.append(dict(idx=idx, label=label))
    data["financial_choices"] = financial_choices

    back_dic["data"] = data
    return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


def position_details_page(request, rcm_id):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    this_rcm = Recruitment.objects.get(id=rcm_id)
    data["this_rcm"] = RecruitmentMapper(this_rcm).as_dict()

    this_position = this_rcm.position
    data["this_position"] = PositionMapper(this_position).as_dict()

    this_enterprise = this_position.enterprise
    data["this_enterprise"] = EnterpriseInfoMapper(this_enterprise).as_dict()

    this_poster = User.objects.get(id=this_enterprise.id_id)
    data["this_poster"] = UserMapper(this_poster).as_dict()

    unit_choices = []
    for idx, label in TIME_UNIT_CHOICES:
        unit_choices.append(dict(idx=idx, label=label))
    data["unit_choices"] = unit_choices

    city_choices = []
    for idx, label in PROVINCES_CHOICES:
        city_choices.append(dict(idx=idx, label=label))
    data["city_choices"] = city_choices

    exp_choices = []
    for idx, label in YEAR_CHOICES:
        exp_choices.append(dict(idx=idx, label=label))
    data["exp_choices"] = exp_choices

    financial_choices = []
    for idx, label in FINANCING_STATUS_CHOICES:
        financial_choices.append(dict(idx=idx, label=label))
    data["financial_choices"] = financial_choices

    nature_choices = []
    for idx, label in JOB_NATURE_CHOICES:
        nature_choices.append(dict(idx=idx, label=label))
    data["nature_choices"] = nature_choices

    position_all = []
    position_class_set = PositionClass.objects.all()
    for pst in position_class_set:
        position_all.append(PositionClassMapper(pst).as_dict())
    data["position_class"] = position_all

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    this_user = user
    data["this_user"] = UserMapper(this_user).as_dict()

    cv_list = []
    cvs = CV.objects.filter(user_id_id=this_user.id).order_by("-update_time")
    for cv in cvs:
        cv_list.append(CvMapper(cv).as_dict())
    data["cvs"] = cv_list

    is_user_posted = False

    applications_of_this_rcm = Applications.objects.filter(recruitment=this_rcm)

    for item in applications_of_this_rcm:
        if item.cv in cvs:
            is_user_posted = True

    data["is_user_posted"] = is_user_posted

    back_dic["data"] = data

    if request.method == "POST":
        para = json.loads(request.body.decode())
        back_dic = {"code": 1000, "msg": "", "url": ""}
        try:
            cv = CV.objects.get(id=int(para["result"]))
            if str(para["type"]) == "101":
                Applications.objects.create(cv_id=cv.id, recruitment_id=this_rcm.id, progress=0)
                back_dic["msg"] = "已投递简历"
        except:
            back_dic["code"] = 1001
            back_dic["msg"] = "oops,出错了,请刷新重试！"
        return JsonResponse(back_dic)

    return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})
    #
    # return render(request, "user/position_details.html", locals())


def my_application(request):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dic = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    this_user = user
    data["this_user"] = UserMapper(this_user).as_dict()

    cv_list = []
    my_cvs = CV.objects.filter(user_id=this_user.id)
    for cv in my_cvs:
        cv_list.append(CvMapper(cv).as_dict())
    data["my_cvs"] = cv_list

    my_cvs_id = [c.id for c in my_cvs]
    my_applications = Applications.objects.filter(cv_id__in=my_cvs_id)
    app_list = []
    for app in my_applications:
        app_list.append(ApplicationsMapper(app).as_dict())
    data["my_applications"] = app_list

    progress_choices = []
    for idx, label in PROGRESS_CHOICES:
        progress_choices.append(dict(idx=idx, label=label))
    data["progress_choices"] = progress_choices

    city_choices = []
    for idx, label in PROVINCES_CHOICES:
        city_choices.append(dict(idx=idx, label=label))
    data["city_choices"] = city_choices

    job_exp_choices = []
    for idx, label in YEAR_CHOICES:
        job_exp_choices.append(dict(idx=idx, label=label))
    data["job_exp_choices"] = job_exp_choices

    edu_level_choices = []
    for idx, label in EDUCATION_LEVELS:
        edu_level_choices.append(dict(idx=idx, label=label))
    data["edu_level_choices"] = edu_level_choices

    back_dic["data"] = data

    if request.method == "POST":
        para = json.loads(request.body.decode())
        if para["type"] == "103":
            # 撤销用户自己投递的简历
            this_app = Applications.objects.filter(id=int(para["id"]))
            this_app.delete()
            back_dic = {"code": 1000, "msg": "已删除", "url": ""}
            return JsonResponse(back_dic)

    return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})
