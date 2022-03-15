import os
import random
import string

import requests

from SMIS import settings

token = os.environ.get('TOKEN')
app_id = os.environ.get('APP_ID')
app_secret = os.environ.get('APP_SECRET')
redirect_url = os.environ.get('REDIRECT_URL')
state = os.environ.get('STATE')

# 网页授权部分
web_get_code = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&state=%s&scope=' % (
    app_id, redirect_url, state)
web_get_fan_info = 'https://api.weixin.qq.com/sns/userinfo?access_token='
web_check_access_token = 'https://api.weixin.qq.com/sns/auth?access_token='
web_get_access_token = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&grant_type=authorization_code&code=' % (
    app_id, app_secret)


def get_wx_authorize_url(appid: str, state: str = None):
    if state is None:
        state = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
    redirect_url = 'your callback url'  # 回调链接，在这里面进行用户信息入库的操作
    response_type = 'code'
    scope = 'snsapi_userinfo'
    wx_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={appid}&redirect_uri={redirect_url}&response_type={response_type}&scope={scope}&state={state}#wechat_redirect"
    return wx_url


def request_access_token(appid: str, secret: str, code: str):
    secret = settings.WX_SECRET
    api = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={appid}&secret={secret}&code=[code]&grant_type=authorization_code"
    r = requests.get(api)
    # 成功会返回3个参数：openid, session_key, unionid
    return r.json()


def convert_string_encoding(s: str, from_encoding: str, to_encoding: str) -> str:
    """先根据 from_encoding 转换成bytes，然后在 decode 为 to_encoding 的字符串
  """
    return bytes(s, encoding=from_encoding).decode(to_encoding)
