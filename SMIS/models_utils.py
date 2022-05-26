"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from rest_framework.pagination import LimitOffsetPagination


# 分页器，不需要迁移
class StandardResultSetPagination(LimitOffsetPagination):
    # 默认页尺寸，一页返回20条记录
    default_limit = 20
    # 页尺寸在URL中的赋值名
    limit_query_param = "limit"
    # 偏移量，从偏移量的数字后开始拿数据
    offset_query_param = "offset"
    # 页尺寸上限
    max_limit = None

