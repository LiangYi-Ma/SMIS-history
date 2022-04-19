from django.contrib.auth.hashers import make_password
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from SMIS.validation import ValidateEmail
from user.models import User, PersonalInfo
from enterprise.models import Field, NumberOfStaff, Recruitment, EnterpriseInfo, Applications, Position, PositionClass
from django.contrib.sessions.models import Session
from enterprise.models import SettingChineseTag, TaggedWhatever

import datetime
import json
import random as rd
from PIL import Image

from SMIS.constants import JOB_NATURE_CHOICES, YEAR_CHOICES
from SMIS.mapper import PositionClassMapper, UserMapper
from SMIS.validation import is_null
from SMIS.data_utils import Utils


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
        return JsonResponse(dict(code=10, msg="匿名用户"))

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
        if len(tags_existed_ids) >= 3:
            tags_rd = rd.sample(tags_existed_ids, 3)
        elif len(tags_existed_ids) == 0:
            tags_rd = []
        else:
            tags_rd = tags_existed_ids
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
    partner_logo = ''
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
        data["beijing"] = dict(location=Utils.Contact_Us_Location,
                               phone=Utils.Contact_Us_Phone,
                               address=Utils.Contact_Us_Address,
                               image="/static/img/sys-img/build-beijing.jpg",
                               url=Utils.Contact_Us_Url,
                               coordinates=Utils.Contact_Us_Coordinates)
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


class AboutUsView(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = dict()
        # 以下参数相当于公共部分，如果再次单独提取出来可能没有必要
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


class TrainingPage(View):
    def get(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')
        data = dict()
        data["QRcode"] = "/static/img/sys-img/code-pub.jpeg"
        back_dic["data"] = data
        return JsonResponse(back_dic, safe=False, json_dumps_params={'ensure_ascii': False})


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


def compressImageByFile(request):
    import os
    for root_name, b, children in os.walk("static/img/"):
        for child in children:
            img_path = root_name + child
            open_and_compress(img_path)
    return HttpResponse("done")


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


from rest_framework.views import APIView
from user import api_wx
from django.core.cache import cache
import hashlib, time
from user.models import User_WxID


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
