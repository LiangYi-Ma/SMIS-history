from django.urls import path

from . import views

urlpatterns = [
    # path('search/', views.search, name='search'),
    path('<int:user_id>/<int:cv_id>/show-cv/', views.show_cv, name='show_cv'),
    path('<int:user_id>/<int:cv_id>/download-cv/', views.save_as_pdf, name='download-cv'),
    path('search_cv_page/', views.SearchCv.as_view(), name='search_cv_page'),
    path('cv_detail/', views.CvDetail.as_view(), name='cv_detail'),
    path('cv_deliver/', views.CvDeliver.as_view(), name='cv_deliver'),
    path('cv_download_pdf/', views.MakePdf.as_view(), name='cv_download_pdf'),
    # 个人简历文件上传/删除
    path('upload_cv/', views.UploadCvPdf.as_view(), name='upload_cv'),
]
