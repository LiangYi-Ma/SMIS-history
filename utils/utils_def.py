# author: Mr. Ma
# datetime :2022/7/22

import re


# 联系电话检测
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

# # 敏感词检测
# def sensitive_word(text: str):
#     src = jieba.cut(text, cut_all=True)
#     # print(",".join(src))
#     print(list(set(list(src))))
