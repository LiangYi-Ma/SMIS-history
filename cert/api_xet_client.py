"""
@file_intro: 小鹅通服务器
@creation_date: 20220314
@update_date: 20220314
@author:Yaqi Meng
"""
from cert.api_xet_token_manager import TokenManager
import json
import requests

CLIENT_ID = "xopKrhhGeZD2176"
SECRET_KEY = "64rXKJ8ZFWRP42agzL8vqCP3Q0dowu35"
APP_ID = "appHTPxaGTp7928"
GRANT_TYPE = "client_credential"


MANAGER = TokenManager(APP_ID, CLIENT_ID, SECRET_KEY, GRANT_TYPE)


"""
调用小鹅client实现接口操作
会自动封装请求头和token进去
"""


class XiaoeClient:
    # user_params 需要传dict
    def request(self, method, url, user_params={}):
        access_token = MANAGER.token()
        user_params["access_token"] = access_token
        payload = json.dumps(user_params)
        # print(payload)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request(method, url, headers=headers, data=payload)
        #
        # print(response.text)
        # print(type(json.loads(response.text)))
        return json.loads(response.text)
