from SMIS import settings
import requests


def get_access_token():
    """拿到接口调用凭证"""
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + settings.AppID + \
          "&secret=" + settings.AppSecret
    response = requests.get(url)
    # 把它变成json的字典
    json_response = response.json()
    print("token:", json_response)
    # 判断调用返回值
    if json_response.get("access_token"):
        return json_response
    else:
        return False


def get_login_info(code):
    """拿到用户登录信息"""
    code_url = settings.code2Session.format(settings.AppID, settings.AppSecret, code)
    response = requests.get(code_url)
    json_response = response.json()
    if json_response.get("session_key"):
        return json_response
    else:
        return False


def get_user_phone(code, ):
    """拿到用户微信绑定的手机号"""
    access_token = get_access_token()
    if access_token["access_token"]:
        code_url = "https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token=" + access_token[
            "access_token"]
        response = requests.post(url=code_url, json={"code": code})
        json_response = response.json()
        print("phone:", json_response)
        if json_response.get("phone_info"):
            return json_response
        else:
            return False
    return False
