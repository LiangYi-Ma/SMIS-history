# -*- coding:utf-8 -*-

# author: Mr. Ma
# datetime :2022/7/21


from utils.utils_def import number, email, wechart, qq


def industrial_commercial_review(text: str):
    """
    功能：检测文本中是否含有允许信息
    步骤：
        1：手机号检测
        2：邮件检测
        3：微信号检测
        4：QQ号检测（提示存在QQ或微信新）
    Return : Boolean, list
    """
    # 手机号检测
    bool_num, result_num = number(text)
    if not bool_num:
        # print(f'bool_num:{result_num}')
        return False,result_num
    # 邮件检测
    bool_email, result_email = email(text)
    if not bool_email:
        # print(f'bool_email:{result_email}')
        return False, result_email
    # 微信号检测
    bool_wechart, result_wechart = wechart(text)
    if not bool_wechart:
        # print(f'bool_wechart:{result_wechart}')
        return False, result_wechart
    # QQ号检测
    bool_qq, result_qq = qq(text)
    if not bool_qq:
        # print(f'bool_qq:{result_qq}')
        return False, result_qq
    return True, []


# industrial_commercial_review('sdgsg@1.comsbdrbsdtbs1232236451'
#                              '4khugi224153468395wang.li.zhe@shiyenet.com.cn6643sbdrbsdtbs12322364514khugi22443后f之h+'
#                              'jjas解决99h1254789652145789651哈哈18195100967哈vdufwang.li.zhe@shiyenet.com.cnvudsgvgvd'
#                              'gvcs哈哈2h:"[[;;+jjhh]]sdgsg@1.msbdrbsdtbs1232236451'
#                              '4khugi2241534683956643sbdrbsdtbs12322364514khugi22443后f之h+jjas解决99h1254'
#                              '789652145789651哈哈18195100967哈vdufvudsgvgvdgvcs哈哈2h:"[[;;+jjhh]]')
