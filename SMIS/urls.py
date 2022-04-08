"""SMIS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from SMIS import api_authorization as AuthViews
# from user.views import LoginView
from django.conf.urls.static import static, serve
from django.conf import settings
from SMIS import views as GlobalViews
from django.views.generic import TemplateView
from user import api_wx as WxViews

urlpatterns = [

    path("", TemplateView.as_view(template_name="index.html")),
    # path('static/', serve,
    #      {'document_root': settings.STATIC_ROOT}, name='static'),
    path('', include('SMIS.user_urls')),
    path('admin/', admin.site.urls, name='admin'),
    path('reset/', GlobalViews.setAdminInfo.as_view()),

    # path('login/', UserViews.login, name="login"),
    path('login/', AuthViews.LoginView.as_view(), name="login"),
    path('login_mobile/', AuthViews.LoginByMsgView.as_view(), name="login_mobile"),
    path('cv/', include('cv.urls')),
    path('user/', include('user.urls')),
    path('enterprise/', include("enterprise.urls")),
    path('cert/', include("cert.urls")),

    # path('Drawing-AI/', GlobalViews.drawing_by_image, name='Drawing-AI'),
    # path('Drawing-AI/<int:image_id>/', GlobalViews.drawing_file, name='Drawing-AI-Image-ID'),
    # 评论模块，待补充
    # path('comments/', include('django_comments.urls')),

    # path('wechat/', WxViews.serve),
    # path('user/info/', WxViews.get_wx_user_info),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
