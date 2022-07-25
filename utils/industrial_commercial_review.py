# author: Mr. Ma
# datetime :2022/7/21

"""
    接口地址： http://api.qichacha.com/ECIThreeElVerify/GetInfo
    支持格式： JSON
    请求方式： GET
"""

import requests

from utils.utils_data import QCC_URL, QCC_KEY, QCC_TOKEN, QCC_TIMESPAN


def qcc_industrial_commercial_review(credit_code: str, company_name: str, oper_name: str):
    """
    功能：工商信息审查
    params：credit_code:  String  统一社会信用代码
    params：company_name: String  企业名称
    params：oper_name:    String  法定代表人名称
    return：Dict,
    {
        "Status": "200",
         "Message": "【有效请求】查询成功",
         "OrderNumber": "ECITHREEELVERIFY2022072210442227098738",
         "Result": {"VerifyResult": 1}
     }
     Result核验结果：
        0：统一社会信用代码有误，
        1：一致，
        2：企业名称不一致，
        3：法定代表人名称不一致
    """
    try:
        url = QCC_URL
        params = {
            'key': QCC_KEY,
            'creditCode': credit_code,
            'companyName': company_name,
            'operName': oper_name
        }
        headers = {
            'Content-Type': 'JSON',
            'Token': QCC_TOKEN,
            'Timespan': QCC_TIMESPAN
        }

        response = requests.get(url, params=params, headers=headers)
        # 响应内容，返回的是Unicode格式的数据
        return response.text
    except Exception as e:
        raise e

# qcc_industrial_commercial_review('91110108MA01GFQG24', '北京智能智造科技有限公司', '孙寿海')
