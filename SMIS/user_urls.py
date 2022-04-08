from django.urls import path
from SMIS import user_view as UserViews
from django.conf.urls.static import static, serve
from django.conf import settings

urlpatterns = [

    path('index/', UserViews.index, name="index"),  # 返回问题加报错
    path('contact-us/', UserViews.ContactUsView.as_view(), name="contact-us"),  # 完成
    path('about-us/', UserViews.AboutUsView.as_view(), name="about-us"),  # 完成
    path("Training/", UserViews.TrainingPage.as_view(), name="training-page"),  # 完成
    path("compressImage/", UserViews.compressImage, name="compress-Image"),  # 完成
    path("compressImageByFile/", UserViews.compressImageByFile, name="compress-Image-by-file"),  # 完成
    path('login_qiye/', UserViews.LoginEnterPriseView.as_view(), name="login_qiye"),  # 完成
    path('logout/', UserViews.logout, name="logout"),  # 完成
    path('register/', UserViews.RegisterView.as_view(), name="register"),  # 完成
    path('wechat/', UserViews.LoginWxView.as_view())  # 报错

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
