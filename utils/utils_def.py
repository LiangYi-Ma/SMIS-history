# -*- coding:utf-8 -*-
# author: Mr. Ma
# datetime :2022/7/22

import hashlib
import json
import re

from better_profanity import profanity
# 联系电话检测
import requests
import collections

from utils import utils_data
from utils.utils_data import BDY_ACCESS_TOKEN_URL, BDY_GRANT_TYPE, BDY_APP_KEY, BDY_SECRET_KEY, BDY_CHECK, BDY_HEADERS, \
    BDY_ACCESS_TOKEN, RES_POSITION_DATA_LIST_COUNT


def number(text: str):
    """
    text：检索文本
    return：Boolean，list
    """
    # 可以截取11个字符以上符合要求的联系电话
    res = re.findall('(13\d{9}|14[5|7]\d{8}|15\d{9}|166{\d{8}|17[3|6|7]{\d{8}|18\d{9})', text)
    if len(res):
        return False, res
    else:
        return True, []


# 微信号检测
def wechart(text: str):
    """
    text：检索文本
    return：Boolean，list
    """
    res = re.findall('[^\u4e00-\u9fa5]{6,}', text)
    for i in range(len(res)):
        src = re.sub('^\d+', '', res[i])
        res[i] = src
    result = []
    for i in res:
        if len(i) >= 6 and len(i) <= 20:
            result.append(i)
        elif len(i) > 20:
            if 'wx' in i.lower()[:5] or 'v' in i.lower()[:4] or 'w' in i.lower()[:4]:
                result.append(i)
    if len(list(set(result))):
        return False, result
    else:
        return True, []


# QQ号检测()
def qq(text: str):
    """
    text：检索文本
    return：Boolean，list
    """
    res = re.findall("[1-9]\d{4,10}", text)
    if len(res):
        return False, res
    else:
        return True, []


# 邮件检测
def email(text: str):
    """
    text：检索文本
    return：Boolean，list
    """
    # 剔除非汉字的字符串
    res = re.findall('[^\u4e00-\u9fa5]{6,}', text)
    regex = re.compile(r'([^\u4e00-\u9fa5]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{2,3})')
    result = []
    if len(res):
        for i in res:
            emails = re.findall(regex, i)
            if len(emails):
                result.extend(emails)
    if len(list(set(result))):
        return False, result
    else:
        return True, result


def md5(text):
    """ md5 加密（主要用于将字符串生成唯一标识）"""
    text_hl = hashlib.md5()
    text_hl.update(text.encode(encoding='utf-8'))
    return text_hl.hexdigest()


# 敏感词检测
class sensitive_word():
    # 文本审核接口

    def __init__(self, text=None):
        self._text = text
        # 创建有序字典：为了清除数据方便
        self._res_position = collections.OrderedDict()
        self._res_keyword = collections.OrderedDict()

    def _clear_dict_cache(self):
        # 防止_res_position，_res_keyword数据积攒过多影响性能,调用则清理80%内容
        res_position_data = self._res_position
        res_keyword_data = self._res_keyword
        rp = list(res_position_data.keys())
        rk = list(res_keyword_data.keys())
        if len(rp) > RES_POSITION_DATA_LIST_COUNT:
            for i in rp[:int(len(rp) * 0.8)]:
                del res_position_data[i]
            self._res_position = res_position_data
            self._res_keyword = res_keyword_data
        if len(rk) > RES_POSITION_DATA_LIST_COUNT:
            for i in rk[:int(len(rk) * 0.8)]:
                del res_keyword_data[i]
            self._res_position = res_position_data
            self._res_keyword = res_keyword_data

    def _get_token(self):
        """
            获取token
        """
        try:
            url = BDY_ACCESS_TOKEN_URL
            params = {
                'grant_type': BDY_GRANT_TYPE,
                'client_id': BDY_APP_KEY,
                'client_secret': BDY_SECRET_KEY
            }
            headers = {
                'Content-Type': 'JSON'
            }
            response = requests.post(url, params=params, headers=headers)
            if response:
                access_token = json.loads(response.text)["access_token"]
                return access_token
            else:
                return ''
        except Exception as e:
            raise e

    def _replace(self, text, replace_type='*'):
        """ 内部公共类，替换文本 """
        pos_1 = self._res_position[md5(text)]
        for i in pos_1.keys():
            locals = pos_1[i]
            for j in locals:
                start = j[0]
                end = j[1]
                string = list(text)
                string[start:end + 1] = replace_type * (end - start + 1)
                text = ''.join(string)
        censored_text = profanity.censor(text)
        return censored_text

    def _msg_all(self, text):
        """ 获取所有的异常类型 """
        pos_1 = self._res_keyword[md5(text)]
        return pos_1.keys()

    def _keyword_all(self, text):
        """ 获取所有的异常词 """
        pos_1 = self._res_keyword[md5(text)]
        res = []
        for i in pos_1.keys():
            res.extend(pos_1[i])
        return res

    def _check_text(self, text=None):
        """
            返回数据格式(全格式)：查看bdy_data_api文件
            return: dict
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text
        try:
            request_url = BDY_CHECK
            params = {
                "text": text
            }
            flag = 0
            to = utils_data.BDY_ACCESS_TOKEN
            while flag < 2:
                # 这里如果每调用一下就获取一次token会影响性能因此这里做判断，如果过期则轮询获取token然后再次发起请求
                request_url = request_url + "?access_token=" + to
                headers = BDY_HEADERS
                response = requests.post(request_url, data=params, headers=headers)
                if response:
                    if 'error_code' in response.json().keys() and response.json()['error_code'] in [110, 111]:
                        token = self._get_token()
                        # 控制循环次数，避免出现死循环
                        flag = flag + 1
                        if token:
                            to = token
                            utils_data.BDY_ACCESS_TOKEN = to
                            continue
                        else:
                            raise SystemError('获取百度云 Token失败')
                    return response.json()
                else:
                    raise SystemError('调用百度云文本检测第三方接口失败')
            return {}
        except Exception as e:
            raise e

    def _tree_data(self, text=None):
        """
            工具类（私有）：
            功能：将识别出的结果树结果进行提取（{uid:{类型1：[位置1,位置2....],类型2：[位置1,位置2....]...}}）{
            "uid": {
                "类型1": [
                    ["位置1"],
                    ["位置2]"
                ],
                "类型2": [
                    ["位置1"],
                    ["位置2"]
                ]
            }
            uid：为text文本md5加密后的结果
            目的：统一处理数据，之后的违规词替换和错误类型提取不用重复处理
            return : int( 1 : 不规范，汇总成功,  2 : 规范， 3：疑似)
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text
        try:
            # 遍历结果树，提取类型和位置列表
            result = self._check_text(text)
            uid = md5(text)
            self._res_position[uid] = {}
            self._res_keyword[uid] = {}
            if 'error_code' not in result.keys() and len(result.keys()) > 0 and int(result['conclusionType']) == 2:
                data = result['data']
                for i in data:
                    self._res_position[uid][i['msg']] = []
                    self._res_keyword[uid][i['msg']] = []
                    if len(i['hits']):
                        for j in i['hits']:
                            if len(j['wordHitPositions']):
                                for h in j['wordHitPositions']:
                                    self._res_keyword[uid][i['msg']].append(h['keyword'])
                                    if len(h['positions']):
                                        for k in h['positions']:
                                            self._res_position[uid][i['msg']].append(k)
                return 1  # 不规范，汇总成功
            elif len(result.keys()) == 0:
                raise SystemError('系统异常，百度云第三方接口请求值为空！')
            elif int(result["conclusionType"]) == 1:
                return 2  # 规范
            elif int(result["conclusionType"]) == 3:
                return 3  # 疑似
            elif 'error_code' in result.keys():
                raise SystemError(result['error_msg'])  # 系统异常，直接抛出异常
            elif result['conclusionType'] == 4:
                raise SystemError('审核失败')
            raise SystemError('系统异常')
        except Exception as e:
            raise e

    def check_text_replace(self, text=None, replace_type='*'):
        """
            敏感词检测：对敏感词替换(只有在不合规时替换)
            return：text
            data：list 用敏感类型分配
            wordHitPositions：list 以关键词个数分配
            positions：list 以关键词的位置分配
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text
        self._clear_dict_cache()
        try:
            if md5(text) in self._res_position.keys():
                return self._replace(text, replace_type)
            else:
                bool = self._tree_data()
                if bool == 1:
                    return self._replace(text, replace_type)
                else:
                    return text
        except Exception as e:
            raise e

    def check_text_keyword(self, text=None):
        """
        功能：返回敏感词
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text
        self._clear_dict_cache()
        try:
            if md5(text) in self._res_position.keys():
                return self._keyword_all(text)
            else:
                bool = self._tree_data()
                if bool == 1:
                    return self._keyword_all(text)
                else:
                    return []
        except Exception as e:
            raise e

    def check_text_msg(self, text=None):
        """
        功能：返回不合规类型
        return :list,int(1:规范，2：不规范，3：疑似)
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text
        self._clear_dict_cache()
        try:
            if md5(text) in self._res_position.keys():
                if len(self._res_position[md5(text)].keys()):
                    return self._msg_all(text), 2
                else:
                    return [], 1
            else:
                bool = self._tree_data()
                if bool == 1:
                    return self._msg_all(text), 2
                elif bool == 2:
                    return [], 1
                else:
                    return [], 3
        except Exception as e:
            raise e

    def check_text_msg_keyword(self, text=None):
        """
        功能：返回不合规类型:词
        return :list
        """
        if text is None:
            if self._text is None:
                raise ValueError('text不能为空！')
            else:
                text = self._text
        else:
            self._text = text

        self._clear_dict_cache()
        try:
            if md5(text) in self._res_position.keys():
                return self._res_keyword[md5(text)]
            else:
                bool = self._tree_data()
                if bool == 1:
                    return self._res_keyword[md5(text)]
                elif bool == 2:
                    return []
                else:
                    return []
        except Exception as e:
            raise e
