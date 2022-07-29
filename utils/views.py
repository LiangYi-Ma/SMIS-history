# author: Mr. Ma
# datetime :2022/7/28
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from user.models import User
from rest_framework.response import Response
from rest_framework.views import APIView

from SMIS.validation import session_exist
from utils.serializers import SensitiveWordReplaceSerializer, SensitiveWordSerializer
from utils.utils_def import sensitive_word

# 全局创建对象，同一文本调用不同操作，节省io,提高接口速度
sw = sensitive_word()


class SensitiveWordReplace(APIView):

    def post(self, request):
        """ 敏感词审查公用接口（敏感词替换） """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = SensitiveWordReplaceSerializer(data=data)
        bool = src.is_valid()
        if bool:
            try:
                if 'replace_type' in data.keys():
                    text = sw.check_text_replace(text=data['text'], replace_type=data['replace_type'])
                else:
                    text = sw.check_text_replace(text=data['text'])
                back_dir['data'] = text
            except Exception as e:
                # 重点用于捕获公共类中的所有异常，不至于出现程序报错
                back_dir['msg'] = str(e)
        else:
            err = str(src.errors)
            back_dir['msg'] = err
        return Response(back_dir)


class SensitiveWordKeyword(APIView):

    def post(self, request):
        """ 敏感词审查公用接口（返回敏感词） """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = SensitiveWordSerializer(data=data)
        bool = src.is_valid()
        if bool:
            try:
                text = sw.check_text_keyword(text=data['text'])
                back_dir['data'] = text
            except Exception as e:
                # 重点用于捕获公共类中的所有异常，不至于出现程序报错
                back_dir['msg'] = str(e)
        else:
            err = str(src.errors)
            back_dir['msg'] = err
        return Response(back_dir)


class SensitiveWordMsgKeyword(APIView):

    def post(self, request):
        """ 敏感词审查公用接口（返回敏感词+敏感词类型）"""
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = SensitiveWordSerializer(data=data)
        bool = src.is_valid()
        if bool:
            try:
                text = sw.check_text_msg_keyword(text=data['text'])
                back_dir['data'] = text
            except Exception as e:
                # 重点用于捕获公共类中的所有异常，不至于出现程序报错
                back_dir['msg'] = str(e)
        else:
            err = str(src.errors)
            back_dir['msg'] = err
        return Response(back_dir)


class SensitiveWordMsg(APIView):

    def post(self, request):
        """
        敏感词审查公用接口（返回不合规类型）
        (1:规范，2：不规范，3：疑似)
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = SensitiveWordSerializer(data=data)
        bool = src.is_valid()
        if bool:
            try:
                text, state = sw.check_text_msg(text=data['text'])
                back_dir['data'] = {'state': state, 'msg': text}
            except Exception as e:
                # 重点用于捕获公共类中的所有异常，不至于出现程序报错
                back_dir['msg'] = str(e)
        else:
            err = str(src.errors)
            back_dir['msg'] = err
        return Response(back_dir)
