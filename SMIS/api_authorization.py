"""
认证接口
"""
from django.views.generic.base import View
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password

from user.models import User, PersonalInfo, JobExperience, TrainingExperience, \
    EducationExperience, Evaluation, WxUserPhoneValidation

import json
import re
import random as rd
import requests
import urllib
import datetime


class LoginByMsgView(View):
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
            # r.encoding = "utf-8"

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
            code_obj = WxUserPhoneValidation.objects.filter(unvalid_phone_number=phone_number).order_by(
                "-valid_datetime").first()

            expired_time = code_obj.valid_datetime + datetime.timedelta(minutes=10)
            if datetime.datetime.now() > expired_time:
                is_expired = True
            else:
                is_expired = False

            if code_obj and not is_expired:
                if unchecked_code == code_obj.valid_code:
                    """此处需要创建一个用户"""
                    username = str(phone_number)
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
                            back_dic["msg"] = "验证成功, 已为您创建用户, 初始用户名和密码为手机号"
                else:
                    back_dic["code"] = 1002
                    back_dic["msg"] = "验证码不正确"
            else:
                back_dic["code"] = 1003
                back_dic["msg"] = "验证码已过期，请重新验证"

        return JsonResponse(back_dic)


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

    def post(self, request, *args, **kwargs):
        back_dic = dict(code=1000, msg='')

        username = request.POST.get("username")
        password = request.POST.get("password")
        # data = json.loads(request.body)
        # username = data.get('username')
        # password = data.get('password')
        if not username and not password:
            data = json.loads(request.body.decode())
            username = data["username"]
            password = data["password"]

        print(username, password)
        user_obj = auth.authenticate(username=username, password=password)
        if not user_obj:
            is_exist = PersonalInfo.objects.filter(phone_number=username).first()
            if is_exist:
                username = is_exist.id.username
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

