"""django packages"""
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.contrib.sessions.models import Session

"""app's models"""
from cv.models import CV
from .models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position
from user.models import PositionClass, User
from enterprise.models import SettingChineseTag, TaggedWhatever

"""system pri-setting files"""
from SMIS.constants import EDUCATION_LEVELS, JOB_NATURE_CHOICES, NATURE_CHOICES, FINANCING_STATUS_CHOICES, \
    PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, PROGRESS_CHOICES
from SMIS.validation import enterprise_info_is_valid, position_info_is_valid, position_post_is_valid
from SMIS.mapper import PositionClassMapper, UserMapper, PersonalInfoMapper, EvaMapper, CvMapper, JobExMapper, \
    EduExMapper, TraExMapper, FieldMapper, RecruitmentMapper, EnterpriseInfoMapper, ApplicationsMapper, PositionMapper, \
    TaggedWhateverMapper, SettingChineseTagMapper, NumberOfStaffMapper

"""other"""
import random
import json
import datetime

# Create your views here.

logo_image_white = "img/logo_white.jpg"
logo_image_color = "img/logo_prise.png"
logo_only_color = "img/logo_favicon.png"


def session_exist(request):
    # session_key = request.session.session_key
    session_key = request.META.get("HTTP_AUTHORIZATION")
    print("*****", request.META.get("HTTP_AUTHORIZATION"))
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
        back_dic = edit_positions(para)
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


def edit_positions(para):
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


def service_page(request):
    return render(request, "enterprise/service.html", locals())
