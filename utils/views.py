# author: Mr. Ma
# datetime :2022/7/28
import datetime
import time

from django.db import transaction
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from user.models import User, PersonalInfo
from rest_framework.response import Response
from rest_framework.views import APIView

from SMIS.validation import session_exist
from utils import serializers
from utils.models import CommonWords
from utils.serializers import SensitiveWordReplaceSerializer, OnlineStatusSerializer
from utils.utils_data import ONLINE_STATUS_CHECK_TIME
from utils.utils_def import sensitive_word

# 全局创建对象，同一文本调用不同操作，节省io,提高接口速度
sw = sensitive_word()


class SensitiveWordMsg(APIView):

    def post(self, request):
        """
        敏感词审查公用接口
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
        src = SensitiveWordReplaceSerializer(data=data)
        bool = src.is_valid()
        if bool:
            try:
                msg, state = sw.check_text_msg(text=data['text'])
                if 'replace_type' in data.keys():
                    replace_text = sw.check_text_replace(text=data['text'], replace_type=data['replace_type'])
                else:
                    replace_text = sw.check_text_replace(text=data['text'])
                text = sw.check_text_msg_keyword(text=data['text'])
                back_dir['data'] = {'state': state, 'keyword': text, 'replace': replace_text}
            except Exception as e:
                # 重点用于捕获公共类中的所有异常，不至于出现程序报错
                back_dir['msg'] = str(e)
        else:
            err = str(src.errors)
            back_dir['msg'] = err
        return Response(back_dir)


class OnlineStatus(APIView):

    def get(self, request):
        # 当前用户的心跳检测(定时由前端做)
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        try:
            user = User.objects.get(id=uid)
            p1 = PersonalInfo.objects.filter(id=user.id).exists()
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            if p1:
                pi = PersonalInfo.objects.get(id=user.id)
                pi.online_status = 0
                pi.online_time = now
                pi.save()
            else:
                PersonalInfo.objects.create(id=user, online_status=0, online_time=now)
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)

    def post(self, request):
        """
        检测其它用户的活跃状态
        ONLINE_STATUS = (
            (0, "当前在线"),
            (1, "今日在线"),
            (2, "近一周"),
            (3, "近两周"),
            (4, "近一个月"),
            (5, "近两个月"),
            (6, "近三个月"),
            (7, "近六个月"),
            (8, "六个月以前"),
        )
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        back_dir = dict(code=200, msg="", data=dict())
        src = OnlineStatusSerializer(data=data)
        bool = src.is_valid()
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if bool:
            try:
                p1 = PersonalInfo.objects.filter(id=data['user_id']).first()
                if p1:
                    # 检测一下用户现在应该是是状态
                    sta = p1.active_time()
                    # 如果是当天在线，则再判断是否是当前在线
                    if sta <= 1:
                        ds = datetime.datetime.now() - p1.id.last_login
                        # 如果心跳检测时间超过规定检测时间则说明用户已经下线
                        if ds.seconds >= ONLINE_STATUS_CHECK_TIME * 60:
                            p1.online_status = 1
                            p1.online_time = now
                            p1.save()
                        else:
                            p1.online_status = 0
                            # 这里不改变时间，应该这里应该就是0 ，之所以修改完全是为了加一层保证
                            p1.save()
                    # 如果超过一天在线则不管是否是当前在线
                    else:
                        # 可能心跳检测完后没有再此按照时间判断是说明状态，因此要改变
                        p1.online_status = sta
                        p1.online_time = now
                        p1.save()
                else:
                    u1 = User.objects.filter(id=data['user_id']).first()
                    p1 = PersonalInfo.objects.create(id=u1)
                    p1.online_status = p1.active_time()
                    p1.save()
                back_dir['data'] = p1.online_status
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = bool.errors
        return Response(back_dir)


class CommonWordsMake(APIView):

    def get(self, request):
        """ 查找（查找所有 + 查找单条详情）"""
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        try:
            if "id" in data.keys():
                """ 查看详情 """
                cw = CommonWords.objects.filter(id=data['id'])
                if cw.exists():
                    cws = serializers.CommonWordsSerializer(instance=cw.first())
                    back_dir['data'] = cws.data
                else:
                    back_dir['code'] = 1001
                    back_dir['data'] = '数据不存在！'
            else:
                """ 查找所有 """
                cw_datas = CommonWords.objects.filter(user=uid).order_by('index').all()
                cws = serializers.CommonWordsSerializer(instance=cw_datas, many=True)
                back_dir['data'] = cws.data
        except Exception as e:
            back_dir['code'] = 1002
            back_dir['msg'] = str(e)
        return Response(back_dir)

    @transaction.atomic()
    def post(self, request):
        """ 添加常用语 + 审核 """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = serializers.CommonWordsPostSerializer(data=data)
        if src.is_valid:
            try:
                num = CommonWords.objects.filter(user=uid).count()
                if num >= 5:
                    back_dir['code'] = 1004
                    back_dir['msg'] = '常用语数已达到上线'
                else:
                    # 数据校验
                    msg, state = sw.check_text_msg(text=data['word'])
                    if state == 1:
                        # 查找最后一条数据的index
                        cw_end = CommonWords.objects.filter(user=uid, is_end=1)
                        if cw_end.exists():
                            indexs = cw_end.first().index
                            cw_end.update(is_end=0)
                            CommonWords.objects.create(
                                word=data['word'],
                                index=indexs + 1,
                                is_end=1,
                                user=User.objects.get(id=1)
                            )
                        else:
                            CommonWords.objects.create(
                                word=data['word'],
                                index=1,
                                is_end=1,
                                user=User.objects.get(id=1)
                            )
                        back_dir['msg'] = '添加成功'
                    else:
                        back_dir['code'] = 1003
                        text = sw.check_text_msg_keyword(text=data['word'])
                        back_dir['msg'] = '常用语内容不规范'
                        back_dir['data'] = text
            except Exception as e:
                back_dir['code'] = 1002
                back_dir['msg'] = str(e)
        else:
            back_dir['code'] = 1001
            back_dir['msg'] = src.errors
        return Response(back_dir)

    @transaction.atomic()
    def put(self, request):
        """ 编辑常用语 + 修改顺序 """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = serializers.CommonWordsPutSerializer(data=data)
        if src.is_valid:
            try:
                cw = CommonWords.objects.get(id=data['id'])
                if 'word' in data.keys():
                    """ 修改常用语 """
                    cw.word = data['data']
                    cw.save()
                    back_dir['msg'] = '更新成功'
                elif 'local' in data.keys():
                    """ 移动位置 """
                    indexs = cw.index
                    is_end = cw.is_end
                    if data['local'] == 1:
                        ''' 前移 '''
                        if is_end:
                            if indexs != 1:
                                CommonWords.objects.filter(id=data['id']).update(index=indexs - 1, is_end=0)
                                CommonWords.objects.filter(user=uid, index=indexs - 1).exclude(id=data['id']).update(
                                    index=indexs, is_end=1)
                                back_dir['msg'] = '移动成功'
                            else:
                                back_dir['code'] = 1001
                                back_dir['msg'] = '常用语只有一条不可移动'
                        else:
                            if indexs == 1:
                                back_dir['code'] = 1006
                                back_dir['msg'] = '优先级已经处于第一位，不可前移'
                            else:
                                CommonWords.objects.filter(id=data['id']).update(index=indexs - 1)
                                CommonWords.objects.filter(user=uid, index=indexs - 1).exclude(id=data['id']).update(
                                    index=indexs)
                                back_dir['msg'] = '移动成功'
                    else:
                        ''' 后移 '''
                        if is_end:
                            back_dir['code'] = 1005
                            back_dir['msg'] = '优先级已经处于最后，不可后移'
                        else:
                            cws_new = CommonWords.objects.filter(user=uid, index=indexs + 1).exclude(id=data['id'])
                            if cws_new.first().is_end:
                                CommonWords.objects.filter(id=data['id']).update(index=indexs + 1, is_end=1)
                                CommonWords.objects.filter(user=uid, index=indexs + 1).exclude(id=data['id']).update(
                                    index=indexs, is_end=0)
                                back_dir['msg'] = '移动成功'
                            else:
                                CommonWords.objects.filter(id=data['id']).update(index=indexs + 1)
                                CommonWords.objects.filter(user=uid, index=indexs + 1).exclude(id=data['id']).update(
                                    index=indexs)
                            back_dir['msg'] = '移动成功'
                else:
                    back_dir['code'] = 1002
                    back_dir['msg'] = 'word和local参数不能同时为空'
            except Exception as e:
                back_dir['code'] = 1003
                back_dir['msg'] = str(e)
        else:
            back_dir['code'] = 1004
            back_dir['msg'] = src.errors
        return Response(back_dir)

    @transaction.atomic()
    def delete(self, request):
        """ 删除常用语 """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')
        back_dir = dict(code=200, msg="", data=dict())
        data = request.data
        src = serializers.CommonWordsDeleteSerializer(data=data)
        if src.is_valid:
            try:
                cw = CommonWords.objects.get(id=data['id'])
                index = cw.index
                is_end = cw.is_end
                cw.delete()
                if is_end:
                    if index != 1:
                        CommonWords.objects.filter(index=index - 1, user=uid).update(is_end=True)
                else:
                    cws_data = CommonWords.objects.filter(index__gt=index, user=uid).all()
                    for i in cws_data:
                        i.index = i.index - 1
                        i.save()
                back_dir["msg"] = "删除成功"
            except Exception as e:
                back_dir["code"] = 1001
                back_dir["msg"] = str(e)
        else:
            back_dir["code"] = 1002
            back_dir["msg"] = src.errors
        return Response(back_dir)
