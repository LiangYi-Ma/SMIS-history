# author: Mr. Ma
# datetime :2022/7/28
from django.urls import path

from . import views

urlpatterns = [

    # 敏感词审查公用接口（敏感词替换）
    path('sensitive_word_replace/v1.0.0/', views.SensitiveWordReplace.as_view(), name="sensitiveWordReplace"),

    # 敏感词审查公用接口（返回敏感词）
    path('sensitive_word_keyword/v1.0.0/', views.SensitiveWordKeyword.as_view(), name="sensitiveWordKeyword"),

    # 敏感词审查公用接口（返回敏感词+敏感词类型）
    path('sensitive_word_msg_keyword/v1.0.0/', views.SensitiveWordMsgKeyword.as_view(), name="sensitiveWordMsgKeyword"),

    # 敏感词审查公用接口（返回不合规类型）
    path('sensitive_word_msg/v1.0.0/', views.SensitiveWordMsg.as_view(), name="sensitiveWordMsg"),
]
