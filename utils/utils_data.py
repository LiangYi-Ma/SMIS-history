# author: Mr. Ma
# datetime :2022/7/22
import time
import hashlib

QCC_URL = 'http://api.qichacha.com/ECIThreeElVerify/GetInfo'
QCC_KEY = '99d5da22474048028926803d3e7378fa'
QCC_SECRETKEY = '2A2A36D1E88CC76980F4E86948FB0A87'
QCC_TIMESPAN = str(int(time.time()))  # 需要秒级10位Unix时间戳，字符串

qcc_hl = hashlib.md5()
qcc_hl.update(f'{QCC_KEY}{QCC_TIMESPAN}{QCC_SECRETKEY}'.encode(encoding='utf-8'))
QCC_TOKEN = qcc_hl.hexdigest().upper()  # 大写32位字符串

BDY_APP_KEY = 'A5lla8k7tMdtCoF1D4TifIsh'
BDY_SECRET_KEY = 'OTWzVkLLOOsDuWVGEllKkKvZ7V3nrtR9'
BDY_ACCESS_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
BDY_GRANT_TYPE = 'client_credentials'
BDY_CHECK = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"
BDY_HEADERS = {'content-type': 'application/x-www-form-urlencoded'}
BDY_ACCESS_TOKEN = ''  # 初始化
