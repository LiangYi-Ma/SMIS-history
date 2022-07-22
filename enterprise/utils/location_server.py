"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
import requests
from ast import literal_eval
import json

KEY = "QW3BZ-ECP6K-MDWJA-AMWCI-PXD55-KABYJ"
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Mobile Safari/537.36'
}


# 带城市的地址转坐标
def address2location(address):
    BASE_URL = "https://apis.map.qq.com/ws/geocoder/v1/?address="
    res = requests.get(url=BASE_URL+address, headers=HEADER)
    res = json.loads(res.text)
    if res["status"] == 0:
        return res["result"]["location"]
    else:
        return -1


def string2list(station):
    return literal_eval(station)


def location2adcode(location):
    BASE_URL = "https://apis.map.qq.com/ws/geocoder/v1/"
    params = {
        "key": KEY,
        "location": location
    }
    res = requests.get(url=BASE_URL, headers=HEADER, params=params)
    res = json.loads(res.text)
    print(location)
    print(res)
    if res["status"] == 0:
        return res["result"]["ad_info"]
    else:
        return -1


def distanceCalculate(from_str, to_str):
    params = {
        "key": KEY,
        "from": from_str,
        "to": to_str,
        "mode": "driving"
    }
    BASE_URL = "https://apis.map.qq.com/ws/distance/v1/matrix/"
    res = requests.get(url=BASE_URL, headers=HEADER, params=params)
    res = json.loads(res.text)
    if res["status"] == 0:
        elements = res["result"]["rows"][0]
        return elements["elements"][0]
    else:
        return -1




