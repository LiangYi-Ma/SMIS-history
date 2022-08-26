# author: Mr. Ma
# datetime :2022/7/28
from django.urls import path

from . import views

urlpatterns = [

    # 敏感词审查公用接口（返回不合规类型/敏感词+敏感词具体类型/文本替换）
    path('sensitive_word_msg/v1.0.0/', views.SensitiveWordMsg.as_view(), name="sensitiveWordMsg"),

    # 用户在线状态更新+获取用户在线状态
    path('online_status/v1.0.0/', views.OnlineStatus.as_view(), name="OnlineStatus"),

    # 常用语部分接口
    path('common_words/v1.0.0/', views.CommonWordsMake.as_view(), name="CommonWords"),

]
