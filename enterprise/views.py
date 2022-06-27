"""django packages"""
import cond as cond
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import make_password

from .serializers import PersonnelRetrievalDataSerializer, PositionDataSerializer

"""app's models"""
from cv.models import CV

from .models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, EnterpriseCooperation, \
    JobHuntersCollection, PositionClass, PositionCollection

from user.models import User, PersonalInfo
from user import models as user_models
from enterprise.models import SettingChineseTag, TaggedWhatever
import time

"""system pri-setting files"""
from SMIS.constants import EDUCATION_LEVELS, JOB_NATURE_CHOICES, NATURE_CHOICES, FINANCING_STATUS_CHOICES, \
    PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, PROGRESS_CHOICES
from SMIS.validation import enterprise_info_is_valid, position_info_is_valid, position_post_is_valid
from SMIS.mapper import PositionClassMapper, UserMapper, PersonalInfoMapper, EvaMapper, CvMapper, JobExMapper, \
    EduExMapper, TraExMapper, FieldMapper, RecruitmentMapper, EnterpriseInfoMapper, ApplicationsMapper, PositionMapper, \
    TaggedWhateverMapper, SettingChineseTagMapper, NumberOfStaffMapper
from SMIS.validation import session_exist
from enterprise.distance import Distance
from enterprise.test_data_create import CreateRCM

"""other"""
import random
import json
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from enterprise import serializers
from .models import StandardResultSetPagination
from user import serializers as serializers_user
from .utils.check_hr_utils import check_hr_enterprise, check_hr, hr_is_superuser, hr_appliaction
from .utils.key_convert import enterpriseinfo_key_convert
from .utils.initialization_applications_hr import InitializationApplicationsHr
import numpy as np

# 用于编写事务
from django.db import transaction

# Create your views here.

logo_image_white = "img/logo_white.jpg"
logo_image_color = "img/logo_prise.png"
logo_only_color = "img/logo_favicon.png"


class EnterpriseIndexView(TemplateView):
    logo_image = logo_image_white
    template_name = "enterprise/enterprise-index.html"

    def get(self, request, *args, **kwargs):
        back_dir = dict(code=1000, msg="", data=dict())
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        data["user"] = UserMapper(user).as_dict()

        data["lago_image"] = self.logo_image

        try:
            info = EnterpriseInfo.objects.get(id=user.id)
            data["has_info"] = True
        except:
            data["has_info"] = False

        if data["has_info"]:
            num_of_positions = Position.objects.filter(enterprise__id=info.id)
            data["num_of_positions"] = len(num_of_positions)

            num_of_rcms = Recruitment.objects.filter(enterprise__id=info.id)
            data["num_of_rcms"] = len(num_of_rcms)
        else:
            data["num_of_positions"] = 0
            data["num_of_rcms"] = 0

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

        # return render(request, self.template_name, {"logo_image": self.logo_image, "user": user})


def enterprise_info(request):
    session_dict = session_exist(request)
    if session_dict["code"] is 0:
        return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

    back_dir = dict(code=1000, msg="", data=dict())
    data = dict()

    session_key = request.META.get("HTTP_AUTHORIZATION")
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    user = User.objects.get(pk=uid)

    if request.method == "GET":
        enterprise_info_this = EnterpriseInfo.objects.filter(id_id=user.id)
        if not enterprise_info_this:
            EnterpriseInfo.objects.create(id_id=user.id)

        logo_image = logo_image_white
        data["logo_image"] = logo_image

        this_enterprise = user
        data["this_enterprise"] = UserMapper(this_enterprise).as_dict()

        # 所有企业默认标签
        enterprise_tags = SettingChineseTag.objects.filter(for_which_entity=0, is_self_setting=False)
        all_tags = []
        for tag in enterprise_tags:
            all_tags.append(SettingChineseTagMapper(tag).as_dict())
        data["enterprise_tags"] = all_tags

        # 该企业已选择的标签分类为【默认】和【自定义】
        tags_chosen = TaggedWhatever.objects.filter(object_id=int(user.id))
        tags_existed_ids = [tg.tag_id for tg in tags_chosen]

        tags_self_setting_chosen = []
        tags_default_chosen = []
        for tag in tags_chosen:
            if tag.tag.is_self_setting:
                tags_self_setting_chosen.append(TaggedWhateverMapper(tag).as_dict())
            else:
                tags_default_chosen.append(TaggedWhateverMapper(tag).as_dict())
        data["tags_default_chosen"] = tags_default_chosen
        data["tags_self_setting_chosen"] = tags_self_setting_chosen

        if EnterpriseInfo.objects.get(id=this_enterprise.id):
            has_info = True
            info = this_enterprise.enterpriseinfo
        else:
            has_info = False
        data["has_info"] = has_info
        data["info"] = EnterpriseInfoMapper(info).as_dict()

        nature_options = []
        for idx, label in NATURE_CHOICES:
            nature_options.append(dict(idx=idx, label=label))
        data["nature_options"] = nature_options

        staff_size_options = []
        for opt in NumberOfStaff.objects.all():
            staff_size_options.append(NumberOfStaffMapper(opt).as_dict())
        data["staff_size_options"] = staff_size_options

        financial_options = []
        for idx, label in FINANCING_STATUS_CHOICES:
            financial_options.append(dict(idx=idx, label=label))
        data["financial_options"] = financial_options
        #
        # first_level_field_options = Field.objects.filter(Q(is_root=True) & Q(is_enable=True))
        # if this_enterprise.enterpriseinfo.field.is_root is False:
        #     is_second = True
        #     first_field_now = this_enterprise.enterpriseinfo.field.parent.id
        # else:
        #     first_field_now = this_enterprise.enterpriseinfo.field.id
        #     is_second = False

        all_field = Field.objects.filter(Q(is_enable=True))
        field_options = []
        for field in all_field:
            field_options.append(FieldMapper(field).as_dict())
        data["field_options"] = field_options

    elif request.method == "POST":
        try:
            edit_type = json.loads(request.body.decode())["type"]
        except:
            edit_type = request.GET.get('type')
            if edit_type is None:
                edit_type = request.POST.get("type")

        enterprise_logo = request.FILES.get("enterprise_logo")
        if enterprise_logo and not edit_type:
            user.enterpriseinfo.logo = enterprise_logo
            user.enterpriseinfo.save()
            back_dir = dict(code=1000, msg="企业logo已修改", data=dict())
            return JsonResponse(back_dir)

        back_dic, para = edit_enterprise_info(request, edit_type)
        """
        1: 保存企业基本信息；
        2: 保存企业联系信息；
        3: 增加自定义企业标签；
        301: 移除默认企业标签；
        302: 移除自定义企业标签；
        303: 增加默认标签；
        """
        if edit_type == "1" and back_dic['code'] == 1000:
            # 保存信息
            user.enterpriseinfo.name = para["name"]
            user.enterpriseinfo.field = Field.objects.get(id=int(para["field"]))
            user.enterpriseinfo.nature = para["nature"]
            user.enterpriseinfo.staff_size = NumberOfStaff.objects.get(id=int(para["size"]))
            user.enterpriseinfo.financing_status = int(para["financial"])
            user.enterpriseinfo.establish_year = int(para["establish_year"])
            # this_field = Field.objects.filter(is_root=False, name=para["field"])
            user.enterpriseinfo.save()
            back_dic["msg"] = "企业基本信息修改成功！"
        elif edit_type == "2" and back_dic['code'] == 1000:
            user.email = para["email"]
            user.save()
            user.enterpriseinfo.address = para["address"]
            user.enterpriseinfo.site_url = para['site']
            user.enterpriseinfo.introduction = para["introduction"]
            user.enterpriseinfo.save()
            back_dic["msg"] = "企业联系信息修改成功！"
        elif edit_type == "3" and back_dic["code"] == 1000:
            tags = para["bonus"]
            """还没有限制自定义标签的个数"""
            user.enterpriseinfo.tags.add(tags)
            new_tag = TaggedWhatever.objects.filter(object_id=user.id).order_by("-create_time").first()
            print("new-tag：", new_tag.tag.name)
            new_tag.tag.is_self_setting = True
            new_tag.tag.for_which_entity = 0
            new_tag.tag.save()
            back_dic["msg"] = "企业标签" + str(para["bonus"]) + "添加成功！"
        elif edit_type == "303" and back_dic["code"] == 1000:
            # para = json.loads(request.body.decode())
            the_tag = SettingChineseTag.objects.get(id=int(para["id"]))
            user.enterpriseinfo.tags.add(the_tag)
        elif edit_type == "302" and back_dic["code"] == 1000:
            the_tag = SettingChineseTag.objects.get(id=int(para["id"]))
            the_tag_name = the_tag.name
            user.enterpriseinfo.tags.remove(the_tag)
            the_tag.delete()
            back_dic["msg"] = "已经移除自定义标签" + str(the_tag_name)
        elif edit_type == "301" and back_dic["code"] == 1000:
            the_tag = SettingChineseTag.objects.get(id=int(para["id"]))
            user.enterpriseinfo.tags.remove(the_tag)

        back_dir = back_dic

        # return JsonResponse(back_dic)
    back_dir["data"] = data
    return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})


# 企业信息编辑
def edit_enterprise_info(request, edit_type):
    dic = {
        'code': 1000,
        'msg': '',
        'url': ''
    }
    para = {}
    if edit_type == "1":
        received_data = json.loads(request.body.decode())
        para = {
            "edit_type": 1,
            "name": received_data["name"],
            # "class": request.POST.get("class"),
            "nature": received_data["nature"],
            "field": received_data["field"],
            "size": received_data["size"],
            "financial": received_data["financial"],
            "establish_year": received_data["establish_year"],
        }
        # para = {
        #     "edit_type": 1,
        #     "name": request.POST.get("name"),
        #     # "class": request.POST.get("class"),
        #     "nature": request.POST.get('nature'),
        #     "field": request.POST.get('field'),
        #     "size": request.POST.get('size'),
        #     "financial": request.POST.get('financial'),
        #     "establish_year": request.POST.get("establish_year"),
        # }
        # para格式：{'nature': '5', 'field': '培训/课外教育/教育辅助', 'size': '<20', 'financial': '', 'establish_year': '2000'}
        print("参数：", para)

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        enterprise_info_exist = EnterpriseInfo.objects.filter(id_id=user.id)
        if not enterprise_info_exist:
            EnterpriseInfo.objects.create(id_id=user.id)
            print("创造了一个新信息")

        dic = enterprise_info_is_valid(para)
    elif edit_type == "2":
        received_data = json.loads(request.body.decode())
        para = {
            "edit_type": 2,
            "email": received_data["email"],
            "address": received_data["address"],
            "site": received_data["site"],
            "introduction": received_data["introduction"],
        }
        # para = {
        #     "edit_type": 2,
        #     "email": request.POST.get("email"),
        #     "address": request.POST.get("address"),
        #     "site": request.POST.get("site"),
        #     "introduction": request.POST.get("introduction"),
        # }
        print("参数：", para)
        dic = enterprise_info_is_valid(para)
    elif edit_type == "3":
        para = {
            "edit_type": 3,
            "bonus": request.POST.get("bonus"),
        }
        if not para["bonus"]:
            try:
                para["bonus"] = json.loads(request.body.decode())["bonus"]
            except:
                para["bonus"] = request.GET.get('bonus')
        print("参数：", para)
        dic = enterprise_info_is_valid(para)
    elif edit_type in ["301", "302", "303"]:
        para = json.loads(request.body.decode())
        print(para)
        para["edit_type"] = int(edit_type)
        dic = enterprise_info_is_valid(para)

    return dic, para


def recommend_candidates_by_rcm(rcm_obj):
    """还要去掉被邀请的人"""
    candidate_list = []
    the_cv = CV.objects.filter().order_by('?').first()
    # Applications.objects.create(cv=the_cv, recruitment=rcm_obj, progress=5)
    candidate_list.append(dict(cv=CvMapper(the_cv).as_dict(), simu_rate=round(random.random(), 2) * 100))
    return candidate_list


class FindingView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        education_levels = []
        for idx, label in EDUCATION_LEVELS:
            education_levels.append(dict(idx=idx, label=label))
        data["education_levels"] = education_levels

        this_enterprise_info = user.enterpriseinfo
        data["this_enterprise_info"] = EnterpriseInfoMapper(this_enterprise_info).as_dict()

        # 当前正在发布的岗位
        rcms = Recruitment.objects.filter(enterprise=this_enterprise_info, is_closed=False).order_by("post_limit_time")
        rcm_list = []
        for rcm in rcms:
            rcm_list.append(RecruitmentMapper(rcm).as_dict())
        data["rcms"] = rcm_list

        list_rcm_recommend = []
        # 该公司正在邀请的人才
        inviting_list = Applications.objects.filter(progress=5,
                                                    recruitment__enterprise__id=this_enterprise_info.id).order_by(
            "create_time")

        print("here")
        for i in inviting_list:
            print(i.recruitment_id)
        for rcm in rcms:
            # dic = {"rcm": RecruitmentMapper(rcm).as_dict(), "rec": recommend_candidates_by_rcm(rcm),
            #        "inv": inviting_list.filter(recruitment_id=rcm.id)}
            inviting_list_by_rcm = []
            for inv in inviting_list.filter(recruitment_id=rcm.id):
                inviting_list_by_rcm.append(ApplicationsMapper(inv).as_dict())
            dic = {"rcm": RecruitmentMapper(rcm).as_dict(), "rec": recommend_candidates_by_rcm(rcm),
                   "inv": inviting_list_by_rcm}
            list_rcm_recommend.append(dic)
        data["list_rcm_recommend"] = list_rcm_recommend

        # 匹配程度，这里占位，函数还没写
        simu_rate = round(random.random(), 2) * 100

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()
        para = json.loads(request.body.decode())
        if para["type"] == "101":
            # 企业端邀请人才，后台建立Applications对象，状态为5:邀请中
            # [cv_id, rcm_id] = para["id"].split('.')
            cv_id = para["cv_id"]
            rcm_id = para["rcm_id"]
            Applications.objects.create(recruitment_id=int(rcm_id), cv_id=int(cv_id), progress=5)
            back_dic = {"code": 1000, "msg": "已通过", "url": ""}

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})


def finding_page_by_search(request):
    return render(request, "enterprise/find.html", locals())


def data_analyse_page(request):
    return render(request, "enterprise/data.html", locals())


class HRPageView(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        education_levels = []
        for idx, label in EDUCATION_LEVELS:
            education_levels.append(dict(idx=idx, label=label))
        data["education_levels"] = education_levels

        this_enterprise_info = user.enterpriseinfo
        data["this_enterprise_info"] = EnterpriseInfoMapper(this_enterprise_info).as_dict()

        # 该企业的所有启用中的招聘
        rcms = Recruitment.objects.filter(enterprise=this_enterprise_info, is_closed=False).order_by("post_limit_time")
        rcm_list = []
        for rcm in rcms:
            rcm_list.append(RecruitmentMapper(rcm).as_dict())
        data["rcms"] = rcm_list

        rcms_id = [r.id for r in rcms]
        print(rcms_id)
        applications = Applications.objects.filter(recruitment_id__in=rcms_id)
        applications_list = []
        for app in applications:
            applications_list.append(ApplicationsMapper(app).as_dict())
        data["applications"] = applications_list

        progress_choices = []
        for idx, label in PROGRESS_CHOICES:
            progress_choices.append(dict(idx=idx, label=label))
        data["progress_choices"] = progress_choices

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        para = json.loads(request.body.decode())
        if para["type"] == "101":
            # HR通过候选人的简历
            this_app = Applications.objects.get(id=int(para["id"]))
            this_app.progress = 2
            this_app.save()
            back_dir = {"code": 1000, "msg": "已通过", "url": ""}
        elif para["type"] == "102":
            # HR退回/拒绝候选人的简历
            this_app = Applications.objects.get(id=int(para["id"]))
            this_app.progress = 1
            this_app.save()
            back_dir = {"code": 1000, "msg": "已退回", "url": ""}

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})


class PositionsPageView(View):
    def edit_positions(self, para):
        dic = {
            'code': 1000,
            'msg': '',
            'url': ''
        }
        if para["type"] == "201":
            dic = position_info_is_valid(para)
        elif para["type"] in ["202", "101"]:
            dic = position_post_is_valid(para)
        elif para["type"] in ["203", "103"]:
            pass
        elif para["type"] == "000":
            dic = position_info_is_valid(para)
        else:
            dic["msg"] = "如果你看到这句话，说明type可能传错了，速速联系小孟"
        return dic

    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        logo_image = logo_image_white
        data["logo_image"] = logo_image

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        this_enterprise_info = user.enterpriseinfo
        data["this_enterprise_info"] = EnterpriseInfoMapper(this_enterprise_info).as_dict()

        positions = Position.objects.filter(enterprise=this_enterprise_info).order_by("-update_time")
        position_list = []
        for pos in positions:
            position_list.append(PositionMapper(pos).as_dict())
        data["positions"] = position_list

        idx_pst = [i + 1 for i in range(len(positions))]
        zip_them = zip(idx_pst, positions)

        recruitment = Recruitment.objects.filter(enterprise=this_enterprise_info, is_closed=False).order_by(
            "post_limit_time")

        now = timezone.now().date()
        data["now"] = str(now)

        for rcm_each in recruitment:
            if rcm_each.post_limit_time < now:
                rcm_each.is_closed = True
                rcm_each.save()
        idx_rcm = [i + 1 for i in range(len(recruitment))]
        zip_recruitment = zip(idx_rcm, recruitment)
        rcms_list = []
        for rcm in recruitment:
            rcms_list.append(RecruitmentMapper(rcm).as_dict())
        data["recruitment"] = rcms_list

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
        pst_class_options = PositionClass.objects.all()
        position_class = []
        for pst in pst_class_options:
            position_class.append(PositionClassMapper(pst).as_dict())
        data["position_class"] = position_class

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)

        para = json.loads(request.body.decode())
        back_dic = self.edit_positions(para)
        print("参数", para)

        this_enterprise_info = user.enterpriseinfo
        if para["type"] == "201" and back_dic["code"] == 1000:
            # 编辑岗位的信息
            this_position = Position.objects.get(id=int(para["id"]))
            this_pst_class = PositionClass.objects.get(id=int(para["class"]))
            this_position.pst_class = this_pst_class
            this_position.fullname = para["name"]
            this_position.requirement = para["requirement"]
            this_position.job_content = para["content"]
            this_position.extra_info = para["extra"]
            this_position.save()
            back_dir["msg"] = "编辑岗位成功"
        elif para["type"] == "202" and back_dic["code"] == 1000:
            # 发布招聘
            this_position = Position.objects.get(id=int(para["id"]))
            print(1)
            """
            {'type': '202', 'id': 10, 'number': '213', 'education': 2, 
            'salary_1': '213', 'salary_2': '2312', 'salary_unit': 2, 
            'city': 7, 'exp': 0, 'nature': 2, 'deadline': '2021-07-31'}
            """
            Recruitment.objects.create(enterprise=this_enterprise_info, position=this_position,
                                       number_of_employers=int(para["number"]),
                                       education=int(para["education"]), city=int(para["city"]),
                                       salary_min=int(para["salary_1"]),
                                       salary_max=int(para["salary_2"]), salary_unit=int(para["salary_unit"]),
                                       job_experience=int(para["exp"]), job_nature=int(para["nature"]),
                                       post_limit_time=para["deadline"])
            back_dir['msg'] = '发布招聘成功'
        elif para["type"] == "103" and back_dic["code"] == 1000:
            # 删除岗位
            have_posted = Recruitment.objects.filter(enterprise=this_enterprise_info,
                                                     position__id=int(para["id"]),
                                                     is_closed=False)
            if have_posted:
                back_dir["code"] = 10031
                back_dir["msg"] = "当前岗位正在发布中，请先撤销或完成你的招聘动作"
            else:
                try:
                    this_position = Position.objects.get(id=int(para["id"]))
                    this_position.delete()
                    back_dir["msg"] = "已经删除该岗位"
                except:
                    back_dir["code"] = 10030
                    back_dir["msg"] = "哎呀，删除过程中出错了，请刷新重试"
        elif para["type"] == "203" and back_dic["code"] == 1000:
            # 撤销招聘
            try:
                this_recruitment = Recruitment.objects.get(id=int(para["id"]))
                this_recruitment.is_closed = True
                this_recruitment.save()
                back_dir["msg"] = "已撤销"
            except:
                back_dir["code"] = 20030
                back_dir["msg"] = "撤销失败，请刷新重试"
        elif para["type"] == "101" and back_dic["code"] == 1000:
            # 修改招聘
            """
            {'type': '101', 'id': '13', 'number': '3', 'education': '中专', 
            'salary_1': '2', 'salary_2': '32', 'salary_unit': '1', 'city': '3', 
            'exp': 'idx', 'nature': '3', 'deadline': '2021-04-21'}
            """
            this_recruitment = Recruitment.objects.get(id=int(para["id"]), is_closed=False)
            this_recruitment.education = int(para["education"])
            this_recruitment.number_of_employers = int(para["number"])
            this_recruitment.salary_min = int(para["salary_1"])
            this_recruitment.salary_max = int(para["salary_2"])
            this_recruitment.salary_unit = para["salary_unit"]
            this_recruitment.city = int(para["city"])
            this_recruitment.job_experience = int(para["exp"])
            this_recruitment.job_nature = int(para["nature"])
            this_recruitment.post_limit_time = para["deadline"]
            this_recruitment.save()
            back_dir['msg'] = '修改这个招聘成功'
        elif para["type"] == "000" and back_dic["code"] == 1000:
            # 创建岗位
            Position.objects.create(pst_class=PositionClass.objects.get(id=int(para["class"])), fullname=para["name"],
                                    requirement=para["requirement"], job_content=para["content"],
                                    extra_info=para["extra"], enterprise=this_enterprise_info)
            back_dir["msg"] = "增加一个岗位成功"
        else:
            back_dir = back_dic
        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})


class PositionsListView(APIView):
    """接口实例"""

    def get(self, request):
        # 最终要返回的query set
        query_set = Position.objects.all()

        # 实例化分页器
        obj = StandardResultSetPagination()
        # query_set:传入数据；request:获取URL请求
        page_list = obj.paginate_queryset(query_set, request)

        # 序列化分页列表
        serializer = serializers.PositionListSerializer(instance=page_list, many=True)
        # 获取分页后的返回结果
        res = obj.get_paginated_response(serializer.data)
        # restframe的返回
        return Response(res.data)


class PositionDetailsView(APIView):
    def get(self, request, position_id):
        position_obj = Position.objects.get(id=position_id)
        serializer = serializers.PositionDetailSerializer(position_obj, many=False)
        return Response(serializer.data)

    def put(self, request, position_id):
        data = json.loads(request.body.decode())
        serializer = serializers.PositionDetailSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        print(data)

        return Response({})


class PersonnelRetrieval(APIView):
    # 人才检索（简历检索）
    def get(self, request):
        try:
            # 需要组装成字符串模糊查询的字段
            """
                因为传过来的参数比较多，所以决定要通过body传参
                request.data:获取在body中传过来的所有json参数
                Search_term：为固定检索词，必须条件，其它条件为非必须
            """
            # 前端参数校验
            data = request.data
            ser = PersonnelRetrievalDataSerializer(data=data)
            print(ser.is_valid(raise_exception=True))
            # 对条件进行抽取出来,不包含必须的检索词字段
            conditions = list(request.data.keys())
            conditions.remove('Search_term')
            if len(conditions) != 0:
                # 空值检测，序列化中没办法检测空值，所以在这手动检测
                for i in conditions:
                    if data[i] == '':
                        conditions.remove(i)
            # 数据查询
            if len(conditions) == 0:
                query_set = CV.objects.all()
            else:
                sql = {}
                # 动态拼接字符串
                for i in range(len(conditions)):
                    # 课程因为有多个所以需要模糊查询该字段
                    if conditions[i] == 'courses' or conditions[i] == 'professional_skill':
                        sql[conditions[i] + '__icontains'] = data[conditions[i]]
                    else:
                        sql[conditions[i]] = data[conditions[i]]

                query_set = CV.objects.filter(**sql).all()
            # 检索词查询处理
            query_set = list(query_set)
            query_set_new = []
            for i in range(len(query_set)):
                src = f'{query_set[i].industry}{query_set[i].major}{query_set[i].courses}{query_set[i].english_skill}' \
                      f'{query_set[i].computer_skill}{query_set[i].professional_skill}{query_set[i].award}{query_set[i].talent}'
                if data['Search_term'] in src:
                    query_set_new.append(query_set[i])
            query_set = query_set_new
            # 序列化，分页处理
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(query_set, request)
            serializer = serializers.PersonnelRetrievalSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)
            return Response(res.data)

        except Exception as e:
            print(e)


class PositionRetrieval(APIView):
    # 职位检索（岗位检索）
    def get(self, request):
        try:
            data = request.data
            ser = PositionDataSerializer(data=data)
            print(ser.is_valid(raise_exception=True))
            # 对条件进行抽取
            conditions = list(request.data.keys())
            conditions.remove('Search_term')
            if len(conditions) != 0:
                # 空值检测，序列化中没办法检测空值，所以在这手动检测
                for i in conditions:
                    if data[i] == '':
                        conditions.remove(i)
            # 数据查询
            if len(conditions) == 0:
                query_set = Position.objects.all()
            else:
                # 动态拼接条件
                sql = {}
                for i in range(len(conditions)):
                    if conditions[i] == 'job_content' or conditions[i] == 'requirement':
                        sql[conditions[i] + '__icontains']: data[conditions[i]]
                    else:
                        sql[conditions[i]]: data[conditions[i]]
                print(sql)
                query_set = Position.objects.filter(**sql).all()
            # 检索词查询处理
            query_set = list(query_set)
            query_set_new = []
            for i in range(len(query_set)):
                src = f'{query_set[i].enterprise}{query_set[i].pst_class}{query_set[i].fullname}{query_set[i].job_content}' \
                      f'{query_set[i].requirement}{query_set[i].extra_info}'
                if data['Search_term'] in src:
                    query_set_new.append(query_set[i])
            query_set = query_set_new
            # 分页，序列化
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(query_set, request)
            serializer = serializers.PositionDetailSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)
            return Response(res.data)
        except Exception as e:
            print(e)


class PositionCollectionList(APIView):
    # 岗位收藏列表
    def get(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        user_id = session.get_decoded().get('_auth_user_id')

        query_set = PositionCollection.objects.filter(user_id=user_id).all()
        obj = StandardResultSetPagination()
        page_list = obj.paginate_queryset(query_set, request)
        serializer = serializers.PositionCollectionSerializer(instance=page_list, many=True)
        res = obj.get_paginated_response(serializer.data)
        return Response(res.data)


class PositionCollectionAdd(APIView):
    # 添加岗位收藏
    def get(self, request):
        position_id = request.query_params
        ser = serializers.PositionCollectionAddSerializer(data=position_id)
        bool = ser.is_valid(raise_exception=True)
        if bool:
            position_id = position_id['position_id']
            session_dict = session_exist(request)
            if session_dict["code"] != 1000:
                return JsonResponse(session_dict)
            session_key = request.META.get("HTTP_AUTHORIZATION")
            session = Session.objects.get(session_key=session_key)
            user_id = session.get_decoded().get('_auth_user_id')
            # 首先检查position_id是不是存在
            position = Position.objects.filter(id=position_id).first()
            back_dir = dict(code=200, msg="", data=dict())
            if position:
                # 判断收藏目标是否已经存在，如果存在将收藏时间改成当前时间
                collect = PositionCollection.objects.filter(user_id=user_id, position_id=position_id).first()
                if collect:
                    curr_time = datetime.datetime.now()
                    times = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
                    try:
                        PositionCollection.objects.filter(user_id=user_id,
                                                          position_id=position_id).update(
                            create_time=times)
                        back_dir['msg'] = '收藏成功'
                    except Exception as e:
                        print(e)
                        back_dir['code'] = 5002
                        back_dir['msg'] = "收藏失败！"
                else:
                    # 添加数据
                    try:
                        new_join = PositionCollection.objects.create(user_id=user_id, position_id=position_id)
                        new_join.save()
                        back_dir['msg'] = '收藏成功'
                    except Exception as e:
                        print(e)
                        back_dir['code'] = 5003
                        back_dir['msg'] = "收藏失败！"
            else:
                back_dir['code'] = 5001
                back_dir['msg'] = '您收藏的职位不存在！'
            back_dir['data'] = 'null'
            return Response(back_dir)
        else:
            return Response(bool)


class PositionCollectionCancel(APIView):
    # 取消岗位收藏
    def get(self, request):
        position_id = request.query_params
        ser = serializers.PositionCollectionAddSerializer(data=position_id)
        bool = ser.is_valid(raise_exception=True)
        if bool:
            position_id = position_id['position_id']
            session_dict = session_exist(request)
            if session_dict["code"] != 1000:
                return JsonResponse(session_dict)
            session_key = request.META.get("HTTP_AUTHORIZATION")
            session = Session.objects.get(session_key=session_key)
            user_id = session.get_decoded().get('_auth_user_id')
            # 检查position_id是不是存在
            position = Position.objects.filter(id=position_id).first()
            back_dir = dict(code=200, msg="", data=dict())
            if position:
                # 判断收藏目标是否已经存在，如果存在则删除
                collect = PositionCollection.objects.filter(user_id=user_id, position_id=position_id).first()
                if collect:
                    try:
                        PositionCollection.objects.filter(user_id=user_id,
                                                          position_id=position_id).delete()
                        back_dir['msg'] = '取消收藏成功'
                    except Exception as e:
                        print(e)
                        back_dir['code'] = 5003
                        back_dir['msg'] = "取消收藏失败！"
                else:
                    back_dir['code'] = 5002
                    back_dir['msg'] = '收藏不存在'
            else:
                back_dir['code'] = 5001
                back_dir['msg'] = '您取消收藏的职位不存在！'
            back_dir['data'] = 'null'
            return Response(back_dir)
        else:
            return Response(bool)


class HRCooperation(APIView):
    """
    get: hr_id-用户ID
    add: 添加协作者
    put: 更换主HR
    delete: 删除协作者
    """

    def get(self, request, hr_id=None):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        leader_hr = User.objects.get(pk=uid)
        Coop_query = EnterpriseCooperation.objects.get(user_id=leader_hr.id, is_superuser=True)
        this_enterprise_id = Coop_query.enterprise_id
        this_enterprise = EnterpriseInfo.objects.get(id=this_enterprise_id)
        query_set = EnterpriseCooperation.objects.filter(enterprise_id=this_enterprise_id)

        if not hr_id:
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(query_set, request)
            serializer = serializers.CooperationListSerializer(instance=query_set, many=True)
            res = obj.get_paginated_response(serializer.data)
            return Response(res.data)
        else:
            this_hr = query_set.get(user_id=hr_id)
            this_user = User.objects.get(id=hr_id)
            serializer_user = serializers_user.UserSerializer(instance=this_user, many=False)
            serializer_coop = serializers.CooperationListSerializer(instance=this_hr, many=False)
            data = dict(
                user_info=serializer_user.data,
                hr_data=serializer_coop.data
            )
            return Response(data)

    def post(self, request):
        """添加协作hr"""
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return Response(session_dict, status=404)

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        leader_hr = User.objects.get(pk=uid)
        Coop_query = EnterpriseCooperation.objects.get(user_id=leader_hr.id, is_superuser=True)
        this_enterprise_id = Coop_query.enterprise_id

        json_data = json.loads(request.body.decode())
        if "user_id" in json_data.keys():
            if not User.objects.filter(id=json_data["user_id"]).exists():
                return Response(status=404, data={"msg": "user not exist"})
        json_data["enterprise_id"] = this_enterprise_id
        serializer = serializers.CooperationSerializer(data=json_data)
        if serializer.is_valid():
            serializer.save()
        return Response({"msg": "HR(Not leader hr) added success."})

    def delete(self, request, hr_id):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return Response(session_dict, status=404)

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        leader_hr = User.objects.get(pk=uid)
        Coop_query = EnterpriseCooperation.objects.get(user_id=leader_hr.id, is_superuser=True)
        this_enterprise_id = Coop_query.enterprise_id

        all_hrs = EnterpriseCooperation.objects.filter(enterprise_id=this_enterprise_id)
        # try:
        #     all_hrs.get(user_id=leader_hr.id, is_superuser=True)
        # except PermissionError as e:
        #     return Response(dict(msg=e))

        try:
            this_hr = all_hrs.get(user_id=hr_id)
            if this_hr.is_superuser is True:
                return Response(status=201, data=dict(msg="At least one leader HR needed."))
            this_hr.delete()
            return Response({})
        except:
            return Response(status=404, data=dict(msg="HR not exist."))

    def put(self, request, hr_id):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return Response(session_dict, status=404)

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        leader_hr = User.objects.get(pk=uid)
        Coop_query = EnterpriseCooperation.objects.get(user_id=leader_hr.id, is_superuser=True)
        this_enterprise_id = Coop_query.enterprise_id
        all_hrs = EnterpriseCooperation.objects.filter(enterprise_id=this_enterprise_id)

        if all_hrs.first().get_owner() is leader_hr.id:
            try:
                this_hr = all_hrs.get(user_id=hr_id)
            except:
                return Response(status=404, data=dict(msg="HR not exist."))
            this_hr.is_superuser = True
            old_leader = all_hrs.get(user_id=leader_hr.id)
            old_leader.is_superuser = False
            old_leader.save()
            this_hr.save()
            return Response({})


class CollectionsView(APIView):
    """
    get: 收藏列表获取，分页
    post: 添加收藏
    delete: 取消收藏
    """

    def get(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        this_hr = User.objects.get(id=uid)
        this_coop = EnterpriseCooperation.objects.get(user_id=uid)
        this_enterprise = this_coop.get_enterprise_object()

        collections_queryset = JobHuntersCollection.objects.filter(enterprise_id=this_enterprise.id.id).order_by(
            "join_date")
        obj = StandardResultSetPagination()
        page_list = obj.paginate_queryset(collections_queryset, request)

        serializers_collection_list = serializers.CollectionListSerializers(instance=page_list, many=True)
        res = obj.get_paginated_response(serializers_collection_list.data)
        print(res.data)
        return Response(res.data)

    def post(self, request, user_id):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        this_hr = User.objects.get(id=uid)
        this_coop = EnterpriseCooperation.objects.get(user_id=uid)
        this_enterprise = this_coop.get_enterprise_object()

        # 存在性检查
        is_exist = JobHuntersCollection.objects.filter(user_id=user_id, enterprise_id=this_enterprise.id.id)
        if is_exist.exists():
            return Response(status=401, data={"msg": "collection exists already."})

        # 数据合法性检查
        new_data = dict(
            user_id=user_id,
            enterprise_id=this_enterprise.id.id,
            collector=this_hr.id,
        )
        new_collect = serializers.CollectionSerializers(data=new_data)
        if new_collect.is_valid():
            new_collect.save()
            return Response(data={"msg": "new collection added."})

        return Response(status=400, data={"msg": "invalid data."})

    def delete(self, request, user_id):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')

        this_hr = User.objects.get(id=uid)
        this_coop = EnterpriseCooperation.objects.get(user_id=uid)
        this_enterprise = this_coop.get_enterprise_object()

        this_collect = JobHuntersCollection.objects.filter(user_id=user_id, enterprise_id=this_enterprise.id.id)
        if not this_coop.is_superuser and this_collect.first().get_creator().id != this_hr.id:
            return Response(status=403, data={"msg": "You can only delete collection you collected."})
        if this_collect.exists():
            this_collect.first().delete()
            return Response(data={"msg": "collection deleted."})
        return Response(status=400, data={"msg": "invalid collection."})


class RecommendPositionWithinEnterprise(APIView):
    """
    get:
    - 输入职位id，查询所属公司，按照职位相似度拟推荐顺序;
    - 没有职位ID传递过来，则按照热门顺序返回（暂）。
    """

    def get(self, request, rcm_id=None):
        if not rcm_id:
            return Response(data=dict(msg="未实装"))
        else:
            this_recruitment = Recruitment.objects.get(id=rcm_id)
            this_enterprise = this_recruitment.enterprise
            other_recruitment = Recruitment.objects.filter(enterprise=this_enterprise, is_closed=False).exclude(
                position__id=rcm_id)

            # 制作参数矩阵
            rcm = this_recruitment
            key_words_list = [
                [rcm.position.pst_class.parent.id, rcm.position.pst_class.id, rcm.job_experience, rcm.education,
                 rcm.job_nature]]
            indexes = [rcm.id]
            for rcm in other_recruitment:
                sub_list = [rcm.position.pst_class.parent.id, rcm.position.pst_class.id, rcm.job_experience,
                            rcm.education, rcm.job_nature]
                key_words_list.append(sub_list)
                indexes.append(rcm.id)

            kw_matrix = np.array(key_words_list)
            indexes = np.array(indexes)

            obj = Distance()
            obj.mat = kw_matrix
            obj.indexes = indexes
            # 拿到企业内其他已发布职位的相似度顺序
            dis = obj.compute_standard_euclidean()

            # 拼接query
            qs = []
            for item in dis:
                if item[0] != rcm_id:
                    # 拼接无法指定顺序
                    # res_queryset = res_queryset | other_recruitment.filter(id=item[0])
                    qs.extend(other_recruitment.filter(id=item[0]))

            # 实例化分页器
            obj = StandardResultSetPagination()
            # query_set:传入数据；request:获取URL请求
            page_list = obj.paginate_queryset(qs, request)

            serializer = serializers.RecruitmentListSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)

            return Response(data=dict(res=res.data))


class RecommendPositionForUser(APIView):
    def get(self, request, user_id):
        """
        get：user_id 为必需。
        TODO：需要cv对象，此处需要决定，是按照CV来推荐还是个人。人的CV不一定存在，因此不一定有数据。
        0.筛选项：工作经验，学位，期望薪资(需关联简历，需要再做讨论)
        1.根据个人条件量化条件向量self_array=[工作经验，技能分数，工作意向一级分类，工作意向二级分类]
        2.按照筛选项筛选所有在招职位rcm；
        3.量化职位向量rcm_array = [工作经验，技能要求，工作意向一级，工作意向二级]
        """

        personal_info = PersonalInfo.objects.get(id_id=user_id)
        work_code = personal_info.get_work_code()
        edu_code = personal_info.get_degree()
        any_cv = CV.objects.filter(user_id_id=user_id).order_by("update_time").first()
        if any_cv:
            skill_score = any_cv.english_skill + any_cv.computer_skill
        else:
            skill_score = 4
        self_array = [work_code, skill_score, ]

        # 第一次绝对的筛选
        rcm_list = Recruitment.objects.filter(education__lte=edu_code, job_experience__lte=work_code)

        return Response(data=dict())


# 协作表初始化
# class InitialCoopHRView(APIView):
#     def get(self, request):
#         data = dict()
#         all_enterprise = EnterpriseInfo.objects.all()
#         for obj in all_enterprise:
#             leader_id = obj.id.id
#             EnterpriseCooperation.objects.create(user_id=leader_id, enterprise_id=leader_id, is_active=True, is_superuser=True)
#         return Response({})


class PositionData(APIView):
    def get(self, request):
        # 通过职位id获取职位信息，还涉及到了Recruitment招聘表返回数据为招聘表和岗位岗的所有信息)，不需要检验session
        position_id = request.query_params
        ser = serializers.PositionDataDelete(data=position_id)
        bool = ser.is_valid(raise_exception=True)
        back_dir = dict(code=200, msg="", data=dict())
        if bool:
            try:
                position_id = position_id['position_id'][0]
                data_1 = Position.objects.filter(id=position_id).first()
                data_2 = Recruitment.objects.filter(position_id=position_id).first()
                if data_1 and data_2:
                    # 序列化器之前已经定义了，此处直接调用
                    try:
                        # 对两个表中的数据进行简单处理，并且进行组合
                        serializer_data_1 = serializers.PositionDetailZySerializer(instance=data_1)
                        serializer_data_1 = dict(serializer_data_1.data)
                        serializer_data_1['position_id'] = serializer_data_1['id']
                        serializer_data_1.pop('id')
                        serializer_data_2 = serializers.RecruitmentDetailSerializer(instance=data_2)
                        serializer_data_2 = dict(serializer_data_2.data)
                        serializer_data_2['recruitment_id'] = serializer_data_2['id']
                        serializer_data_2.pop('id')
                        for i in serializer_data_2.keys():
                            serializer_data_1[i] = serializer_data_2[i]
                        back_dir['data'] = serializer_data_1
                    except Exception as e:
                        print(e)
                else:
                    back_dir['msg'] = "职位不存在！"
            except Exception as e:
                back_dir['msg'] = e
            return Response(back_dir)
        else:
            return Response(bool)

    def post(self, request):
        # 新增职位，需要校验hr身份
        # 校验sessiion
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user_id = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        if user_id:
            # 参数校验
            data = request.data
            ser = serializers.PositionAdd(data=data)
            bool = ser.is_valid(raise_exception=True)
            if bool:
                # 根据企业id校验hr身份，hr只能添加本公司的职位
                enterprise = int(data['enterprise'])
                bool_hr = check_hr_enterprise(enterprise, uid)
                if bool_hr:
                    # 添加岗位信息和招聘信息表
                    conditions = list(data.keys())
                    # 空值检测，序列化中没办法检测空值，所以在这手动检测
                    for i in conditions:
                        if data[i] == '':
                            conditions.remove(i)
                    position_data = [
                        'pst_class',
                        'fullname',
                        'job_content',
                        'requirement',
                        'extra_info']
                    recruitment_data = ['number_of_employers',
                                        'education',
                                        'city',
                                        'salary_min',
                                        'salary_max',
                                        'salary_unit',
                                        'job_experience',
                                        'job_nature',
                                        'post_limit_time',
                                        'salary_min',
                                        'salary_max']
                    # 动态拼接条件
                    sql_position = {}
                    sql_recruitment = {}
                    for i in range(len(conditions)):
                        if conditions[i] in position_data:
                            sql_position[conditions[i]] = data[conditions[i]]
                        elif conditions[i] in recruitment_data:
                            sql_recruitment[conditions[i]] = data[conditions[i]]
                    sql_position['enterprise_id'] = int(data['enterprise'])
                    sql_recruitment['enterprise_id'] = int(data['enterprise'])
                    try:
                        # 因为此处新增数据是两个表同时新增，所以在这使用事务
                        with transaction.atomic():
                            position_new = Position.objects.create(**sql_position)
                            sql_recruitment['position_id'] = position_new.id
                            recruitment_new = Recruitment.objects.create(**sql_recruitment)
                        back_dir['msg'] = "新增成功"
                    except Exception as e:
                        print(e)
                        back_dir['msg'] = "新增失败"
                else:
                    back_dir['msg'] = "该用户不是hr"
            else:
                back_dir['msg'] = bool
        else:
            back_dir['msg'] = "用户不存在"
        return Response(back_dir)

    def put(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user_id = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        if user_id:
            # 参数校验
            data = request.data
            ser = serializers.PositionUpdate(data=data)
            bool = ser.is_valid(raise_exception=True)
            if bool:
                # 根据职位id查找企业id
                position_id = data['position_id']
                check_position = Position.objects.filter(id=position_id).first()
                if check_position:
                    # 根据企业id校验hr身份，hr只能添加本公司的职位
                    bool_hr = check_hr_enterprise(check_position.enterprise.id_id, uid)
                    if bool_hr:
                        conditions = list(request.data.keys())
                        conditions.remove('position_id')
                        if len(conditions) != 0:
                            # 空值检测
                            for i in conditions:
                                if data[i] == '':
                                    conditions.remove(i)
                        position_data = ['pst_class',
                                         'fullname',
                                         'job_content',
                                         'requirement',
                                         'extra_info']
                        recruitment_data = ['number_of_employers',
                                            'education',
                                            'city',
                                            'salary_min',
                                            'salary_max',
                                            'salary_unit',
                                            'job_experience',
                                            'job_nature',
                                            'post_limit_time']
                        # 数据查询
                        if len(conditions) == 0:
                            back_dir['msg'] = "没有更新项"
                        else:
                            # 动态拼接条件
                            sql_position = {}
                            sql_recruitment = {}
                            for i in range(len(conditions)):
                                if conditions[i] in position_data:
                                    sql_position[conditions[i]]: data[conditions[i]]
                                elif conditions[i] in recruitment_data:
                                    sql_recruitment[conditions[i]]: data[conditions[i]]
                            try:
                                if sql_position:
                                    position_new = Position.objects.filter(position_id=position_id).update(
                                        **sql_position)
                                if sql_recruitment:
                                    recruitment_new = Recruitment.objects.filter(position_id=position_id).update(
                                        **sql_recruitment)
                                back_dir['msg'] = "更新成功"
                            except Exception as e:
                                print(e)
                                back_dir['msg'] = "更新失败"
                        pass
                    else:
                        back_dir['msg'] = "该用户不是hr"
                else:
                    back_dir['msg'] = "该岗位不存在"
            else:
                back_dir['msg'] = bool
        else:
            back_dir['msg'] = "用户不存在"
        return Response(back_dir)

    def delete(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user_id = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        if user_id:
            # 参数校验
            position_id = request.query_params
            ser = serializers.PositionDataDelete(data=position_id)
            bool = ser.is_valid(raise_exception=True)
            if bool:
                # 根据职位id查找企业id
                position_id = position_id['position_id']
                enterprise_id = Position.objects.filter(id=position_id).first()
                if enterprise_id:
                    # 根据企业id校验hr身份，hr只能添加本公司的职位
                    bool_hr = check_hr_enterprise(enterprise_id.enterprise.id_id, uid)
                    if bool_hr:
                        # 删除数据
                        try:
                            with transaction.atomic():
                                Position.objects.filter(id=position_id).delete()
                                Recruitment.objects.filter(position_id=position_id).delete()
                            back_dir['msg'] = "删除成功"
                        except Exception as e:
                            print(e)
                            back_dir['msg'] = "删除失败"
                    else:
                        back_dir['msg'] = "该用户不是hr"
                else:
                    back_dir['msg'] = "该职位不存在"
            else:
                back_dir['msg'] = bool
        else:
            back_dir['msg'] = "用户不存在"
        return Response(back_dir)


class RE(APIView):
    def get(self, request):
        obj = CreateRCM()
        obj.file = request.FILES.get("file")
        data = obj.get_matrix()

        return Response(dict(mat=data))


class ApplicationsHr(APIView):
    """
    初始化Applicatiion中hr，将初始化过程进行了封装，因为这部分需要多次调用，这里是为初始化hr写了一个接口
    """

    def get(self, request):
        rets = InitializationApplicationsHr()
        back_dir = dict(code=200, msg="", data=dict())
        back_dir['msg'] = rets
        return Response(back_dir)


class Candidates(APIView):
    """
    预先需要做的：在Applications表中新增数据列：负责人hr（hr：int，逻辑外键，可以为空，默认为管理者hrID）默认值可以为空，建立方法控制其hr，
                即当求职者投递进度为0时，hr设置为管理者hr
    get:获取流程中的候选人列表。
        无参数时：session用户为管理者hr时，显示：所有候选人。包括其流程进度、提交的简历id、负责他的hr
                session用户为协作hr时，显示当前hr负责的候选人。包括其流程进度、提交的简历id
    put:修改候选人投递进度。
        参数为要修改的进度code和候选人记录id
    delete:删除候选人（这个接口暂时不开放，不要写进接口文档中），只有进度不为0时可以删除，删除直接删除整条记录。
    1：管理者hr是负责人hr。
    2：新加字段hr
    3：在Application中的全是候选者
    """

    def get(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        try:
            # 检查用户是否是hr
            enterprisecooperation = check_hr(uid)
            if enterprisecooperation:
                # 检查hr的类别
                enterprisecooperations = EnterpriseCooperation.objects.filter(user_id=uid).first()
                is_superuser_data = enterprisecooperations.is_superuser
                if is_superuser_data:
                    # 管理者hr,显示：所有候选人
                    applications_datas = Applications.objects.all()
                    # 分页
                    obj = StandardResultSetPagination()
                    page_list = obj.paginate_queryset(applications_datas, request)
                    # 序列化
                    serializer = serializers.CandidatesGetGlSerializer(instance=page_list, many=True)
                    res = obj.get_paginated_response(serializer.data)
                    return Response(res.data)
                else:
                    # 协作者hr
                    applications_datas = Applications.objects.filter(hr=enterprisecooperation).all()
                    obj = StandardResultSetPagination()
                    page_list = obj.paginate_queryset(applications_datas, request)
                    serializer = serializers.CandidatesGetXzSerializer(instance=page_list, many=True)
                    res = obj.get_paginated_response(serializer.data)
                    return Response(res.data)
            else:
                back_dir['msg'] = "该用户不是hr"
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)

    def put(self, request):
        # 要判断修改的用户是不是对应候选人的hr
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        # 校验参数
        data = request.data
        sre = serializers.CandidatesPutSerializer(data=data)
        bool = sre.is_valid()
        try:
            if bool:
                # 通过候选人记录id查出协作表中的用户来校验是否是对应hr，不用用户id查出来协作表去校验候选人，这样会麻烦很多
                applications_datas = Applications.objects.filter(id=data['id']).first()
                if applications_datas:
                    hrs = EnterpriseCooperation.objects.filter(id=applications_datas.hr_id).first()
                    # 因为类型不用，所以强转一下
                    if int(hrs.user_id) == int(uid):
                        applications_datas.progress = data['progress']
                        applications_datas.save()
                        back_dir['msg'] = "更新成功"
                    else:
                        back_dir['msg'] = "该用户不是该候选人的hr"
                else:
                    back_dir['msg'] = "候选人不存在"
            else:
                back_dir['msg'] = str(bool.errors)
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)

    def delete(self, request):
        """
        参数：application_id
        条件：进度不为0，并且hr需要是对应删除的候选人hr
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        src = serializers.DeleteApplicationSerializer(data=request.data)
        bool = src.is_valid()
        try:
            if bool:
                application_id = src.validated_data['application_id']
                # 校验用户是否是hr,并且校验候选人是否存在，候选人对应的hr是否是该用户（已封装）
                bool_app_hr, res = hr_appliaction(uid, application_id)
                if bool_app_hr:
                    # 判断候选人的状态是否是非0
                    application_data = Applications.objects.filter(id=application_id).first()
                    if application_data.progress == 0:
                        back_dir['msg'] = "候选人状态为未开始，不可删除"
                    else:
                        application_data.delete()
                        back_dir['msg'] = "删除成功！"
                else:
                    back_dir['msg'] = res
            else:
                back_dir['msg'] = str(src.errors)
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)


class EnterpriseInformation(APIView):
    """
    get：获取企业信息。返回session用户对应的企业信息（用户是hr,即协作表中的对应关系）。
    put：更新企业信息，只有管理者hr可以修改企业信息, enterpriseInfo.get_owner()可以拿到当前企业的管理者hrID。
    """

    def get(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        # 首先确定用户是否是hr
        bool_hr = check_hr(uid)
        if bool_hr:
            enterprisecooperation = EnterpriseCooperation.objects.filter(user_id=uid).first()
            enterprise_data = EnterpriseInfo.objects.filter(id=enterprisecooperation.enterprise_id).first()
            # 序列化
            re_data = serializers.EnterpriseInfoSerializer(instance=enterprise_data)
            back_dir['msg'] = '查询成功'
            back_dir['data'] = re_data.data
        else:
            back_dir['msg'] = '该用户不是hr'
        return Response(back_dir)

    def put(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        try:
            # 数据校验
            data = request.data
            src = serializers.EnterpriseInfoCdSerializer(data=data)
            bool_data = src.is_valid()
            if bool_data:
                # 按照逻辑一个hr只在一个企业中
                # 首先确定hr是否是修改目标企业的hr
                bool_en_hr = check_hr_enterprise(data['id'], uid)
                if bool_en_hr:
                    # 检测hr身份（会同时检测是否是hr）
                    bool_hr = hr_is_superuser(uid)
                    if bool_hr == 0:
                        back_dir['msg'] = '用户不是管理者hr'
                    elif bool_hr == 1:
                        # 更新数据
                        sql = dict(src.validated_data)
                        sql.pop('User')  # 删除主键
                        if sql:
                            # 数据外键字段名转换，已封装
                            sql = enterpriseinfo_key_convert(sql)
                            # 此处序列化数据之后字段值全部转化成了外键的表名，需要处理
                            enterprise_data = EnterpriseInfo.objects.filter(id=data['id']).update(**sql)
                            back_dir['msg'] = '更新成功' if enterprise_data > 0 else '更新失败'
                        else:
                            back_dir['msg'] = '更新的字段为空'
                    else:
                        back_dir['msg'] = '用户不是hr'
                else:
                    back_dir['msg'] = '该用户不是修改企业hr'
            else:
                back_dir['msg'] = str(src.errors)
        except Exception as e:
            print(e)
            back_dir['msg'] = str(e)
        return Response(back_dir)


class ImportCompany(View):
    """
    post: 自动读取文件，导入公司信息，临时接口，不做交互
    """

    def post(self, request):
        # company = {
        #     "number": "CZL1212016210",
        #     "name": "河北普傲汽车科技有限公司",
        #     "size": "20-99人",
        #     "property": 2,
        #     "address": "栾城区裕翔街159号",
        #     "city": "石家庄",
        #     "companyDescWithHtml": "<p>河北普傲汽车科技有限公司，成立于2019年，隶属于河北国傲投资集团。有两个工作地址，总部在石家庄，在北京有研发中心。普傲汽车科技是一家致力于汽车主动安全及智能驾驶标准化评估系统研发、测试和生产的专业化公司。目前丰田汽车已与河北普傲汽车科技有限公司共同签署一项关于AEB标准化评估的专利授权协议，将用于开发和验证汽车AEB系统的标准化安全测试评估系统。该协议是Toyota IP Solutions自2019年末成立以来首个对外的商业授权。</p> \n<p>公司在中国和美\ufffd\ufffd\ufffd同时拥有专业的研发和生产团队，拥有多名博士作为主要的技术骨干，研发人员均来自海内外著名的大学以及研究机构，研究成果已经成为SAE国际标准J3116-201706和J3157-201902以及ISO TC 22/SC 33N的核心组成部分。</p> \n<p>作为ADAS及智能驾驶技术引领新一波的高新技术研发热潮，公司将在智能驾驶技术评估平台方面实现突破，弥补中国在此项技术领域的空白，为汽车主动安全以及智能驾驶在实际路测进行之前的严格封闭道路测试提供完整的解决方案，包括测试场景、测试设备以及评估方法等，建立规模化、专业化的评测平台和技术团队。</p> \n<p>同时，普傲科技重视企业文化建设，始终坚持“以人为本”的人才理念，重视、关爱人才，建立多元化的人才培养体系，为人才提供广阔的发展平台，为公司快速、健康发展提供坚实的人才保障，公司将不断在汽车主动安全及智能驾驶领域开拓及探索，助跑国内汽车智能驾驶技术长远发展。</p> \n<p> </p> \n<p>&nbsp;</p>",
        #     "companyWebsiteUrl": "www.prideautotech.com",
        #     "establishedTime": "1546358400000",
        #     "industry": "互联网/IT/电子/通信",
        #     "financingStageName": 8
        # }
        with open("enterprise/outer_data/processed_company_info_code.json", "r") as f:
            all_company_list = json.load(f)
            for company in all_company_list:
                check_exist = EnterpriseInfo.objects.filter(name=company["name"])
                if not check_exist.exists():
                    if len(company["address"]) > 50: company["address"] = company["address"][:50]
                    if len(company["companyDescWithHtml"]) > 500: company["address"] = company["address"][:500]
                    try:
                        new_user = User.objects.create(username=company["number"], password=make_password("123"))
                    except:
                        new_user = User.objects.get(username=company["number"])

                    EnterpriseInfo.objects.get_or_create(id=new_user)
                    new_user.enterpriseinfo.name = company["name"][0:18]
                    new_user.enterpriseinfo.size = NumberOfStaff.objects.get(id=random.randint(2, 8))
                    new_user.enterpriseinfo.nature = company["property"]
                    new_user.enterpriseinfo.address = company["address"]
                    new_user.enterpriseinfo.introduction = company["companyDescWithHtml"]
                    new_user.enterpriseinfo.site_url = company["companyWebsiteUrl"]
                    new_user.enterpriseinfo.establish_year = random.randint(2000, 2022)
                    try:
                        industry = Field.objects.get(name=company["industry"])
                    except:
                        industry = Field.objects.get(id=36)
                    new_user.enterpriseinfo.field = industry
                    new_user.enterpriseinfo.financing_status = company["financingStageName"]
                    new_user.enterpriseinfo.save()
                    new_user.save()
                else:
                    this_enterprise = EnterpriseInfo.objects.get(name=company["name"])
                    size = NumberOfStaff.objects.get(id=7)
                    this_enterprise.staff_size = size
                    this_enterprise.save()

        return JsonResponse({})


class ImportPosition(View):
    """
    post: 自动读取文件，导入职位信息和招聘信息，临时接口，不做交互
    """

    def post(self, request):
        # position = {
        #     "pstClass": 27,
        #     "pstClassName1": "电气工程师",
        #     "desc": "<p>岗位职责：</p><p>1、方案制作，根据产品需求，与机械部门工作制作，制定产品研发方案；</p><p>2、根据产品方案，绘制电气原理图、接线图以及生产部门图纸；</p><p>3、负责电气部件的选型及采购清单；</p><p>4、根据产品需求，编写产品程序，包括伺服、工控屏等；</p><p>5、负责新产品测试验证及优化调试；</p><p>6、有关电气、图文资料的收集、整理、归档，编制相关说明书。</p><p>任职要求：</p><p>1、***本科及以上学历，有较好实际工作经验的可降低要求；</p><p>2、电气、电子、机电、自动化等相关专业；</p><p>3、有相关研发设计经验，能独立完成设计、调试等工作者优先；</p><p>4、熟练掌握伺服电机的控制，了解CAN、zigbee协议优先；</p><p>        5、具备良好的组织协调能力、人际交往能力和解决问题的能力<br></p>",
        #     "enterpriseName": "河北普傲汽车科技有限公司",
        #     "extraInfo": "周五双休、自动驾驶、智能网联、大牛带队",
        #     "pstName": "电气工程师",
        #     "city": 5,
        #     "numberNeeded": 2,
        #     "salary": [
        #         8000,
        #         10000
        #     ],
        #     "education": 5,
        #     "jobExp": 1,
        #     "nature": 1,
        #     "publishTime": "2022-06-15 15:50:12"
        # }

        with open("enterprise/outer_data/processed_position_info_code.json", "r") as f:
            all_position_data = json.load(f)
            for position in all_position_data:
                this_enterprise = EnterpriseInfo.objects.get(name=position["enterpriseName"][0:18])
                try:
                    pst_class = PositionClass.objects.get(name=position["pstClassName1"])

                except:
                    pst_class = PositionClass.objects.get(id=position["pstClass"])

                find_exist = Position.objects.filter(job_content=position["desc"][0:150])
                if not find_exist.exists():
                    new_position = Position.objects.create(
                        enterprise=this_enterprise,
                        pst_class=pst_class,
                        fullname=position["pstName"][0:10],
                        job_content=position["desc"][0:150],
                        extra_info=position["extraInfo"]
                    )
                    new_rcm = Recruitment.objects.create(
                        enterprise=this_enterprise,
                        position=new_position,
                        number_of_employers=position["numberNeeded"],
                        education=position["education"],
                        city=position["city"],
                        salary_min=position["salary"][0],
                        salary_max=position["salary"][1],
                        salary_unit=1,
                        job_experience=position["jobExp"],
                        job_nature=position["nature"],
                        post_limit_time=datetime.datetime.now().date() + datetime.timedelta(days=200),
                    )
                    new_position.save()
                    new_rcm.save()
                else:
                    this_position = find_exist.first()
                    this_position.pst_class = pst_class
                    print(pst_class.name)
                    this_position.save()

                    # return Response({})

        return JsonResponse({})


class CandidatesRecommendation(APIView):
    """
    针对岗位的人才（简历）推荐列表。这个接口不涉及推荐算法，主要是查询和筛选
    get：url参数-<int:rcm_id>来自Recruitment表。根据所传入的rcm_id拿到recruitment对象。推荐人才的思路是：
        1.教育经历：硬性条件。user.models.PersonalInfo.get_degree可以知道用户的最高学历，用来做筛选
        2.工作经验：硬性条件。user.models.PersonalInfo.get_work_code提供了计算用户工作经验的方法
        3.工资区间：职位提供的最高工资（enterprise/models.py:260）高于用户预期工资（cv/models.py:96）就行。
        4.岗位类别一级类别：cv.models.CV_PositionClass这个表提供了每份简历对应的求职意向，求职意向来自岗位类别enterprise.PositionClass表，都是存的二级类别，一级类别相同就可以推荐。
        5.岗位类别二级类别：二级类别相同就放在推荐列表的前面一点。
        需要分页，返回值应该包括一个简历列表
    """
