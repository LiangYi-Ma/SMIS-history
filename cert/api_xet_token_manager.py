"""
@file_intro: token管理
@creation_date: 20220314
@update_date: 20220314
@author:Yaqi Meng
"""

import requests
import json
import os.path
from datetime import datetime, timedelta
from SMIS.data_utils import Utils
from cert.models import accessToken

BASE_URL = Utils.BASE_URL
TOKEN_PATH = Utils.TOKEN_PATH
TOKEN_CACHE_PATH = Utils.TOKEN_CACHE_PATH
Content_Type = Utils.CONTENT_TYPE


class TokenManager:
    """TokenManager类维护token功能"""

    def __init__(self, app_id, client_id, secret_key, grant_type):
        self.token_record = None
        self.app_id = app_id
        self.client_id = client_id
        self.secret_key = secret_key
        self.grant_type = grant_type
        self.access_token = None
        self.token_expire_at = None

    # 外部调用token方法拿access token
    def token(self):
        self._read_token()
        print("now", datetime.now(), "expire time", self.token_expire_at)
        if not self.access_token or not self.token_expire_at or self.token_expire_at < datetime.now():
            ok, msg = self._get_access_token()
            if not ok:
                raise Exception("get access token fail:" + msg)
            self._write_token()
        return self.access_token

    # 请求小鹅通获取access token
    def _get_access_token(self):
        payload = json.dumps({
            "app_id": self.app_id,
            "client_id": self.client_id,
            "secret_key": self.secret_key,
            "grant_type": self.grant_type,
        })
        headers = {
            'Content-Type': Content_Type
        }
        response = requests.get(BASE_URL + TOKEN_PATH,
                                headers=headers, data=payload)
        print(response.status_code)
        if not response.ok:
            return False, "request fail"
        resp = json.loads(response.text)
        if resp['code'] != 0 or not resp['data']['access_token']:
            return False, resp['msg']
        self.access_token = resp['data']['access_token']
        self.token_expire_at = datetime.now(
        ) + timedelta(seconds=resp['data']['expires_in'])
        return True, resp['msg']

    # 从磁盘读取token
    def _read_token(self):
        record = accessToken.objects.using("db_cert").get(id=1)
        self.access_token = record.access_token
        if record.token_expire_at:
            expire = record.token_expire_at
        else:
            expire = 0
        self.token_expire_at = datetime.fromtimestamp(expire)
        # if not self.access_token and os.path.isfile(self.app_id + '_' + TOKEN_CACHE_PATH):
        #     token_dict = {}
        #     with open(self.app_id + '_' + TOKEN_CACHE_PATH, 'r') as f:
        #         token_dict = json.load(f)
        #     if token_dict['access_token']:
        #         self.access_token = token_dict['access_token']
        #         self.token_expire_at = datetime.fromtimestamp(
        #             token_dict['token_expire_at'])

    # token持久化到磁盘
    def _write_token(self):
        record = accessToken.objects.using("db_cert").get(id=1)
        record.access_token = self.access_token
        record.token_expire_at = datetime.timestamp(self.token_expire_at)
        print("》》》》：", self.access_token, self.token_expire_at)
        record.save()
        # with open(self.app_id + '_' + TOKEN_CACHE_PATH, 'w') as f:
        #     json.dump({
        #         "access_token": self.access_token,
        #         "token_expire_at": datetime.timestamp(self.token_expire_at),
        #     }, f)
