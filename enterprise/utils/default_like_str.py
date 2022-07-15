# author: Mr. Ma
# datetime :2022/7/13
from enterprise.models import Position


def default_like_str():
    """
    功能：初始化Position表中的like_str字段
    return：Boolean(是为了后续接口的调用，以判断是否成功),String(为了显示提示信息)
    """
    try:
        pos = Position.objects.all()
        # 此处不判断是否以及初始化，是为了将更新该字段值功能一起做了
        for i in pos:
            i.like_str_default()
            i.save()
        return True, '数据初始化完成'
    except Exception as e:
        # 不抛异常是因为这个方法不是接口的功能，而是公共字段
        return False, str(e)
