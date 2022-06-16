from django.urls import path

from . import views

urlpatterns = [
    # path('search/', views.search, name='search'),
    path('<int:user_id>/<int:cv_id>/show-cv/', views.show_cv, name='show_cv'),
    path('<int:user_id>/<int:cv_id>/download-cv/', views.save_as_pdf, name='download-cv'),
    path('search_cv_page/', views.SearchCv.as_view(), name='search_cv_page'),
    path('cv_detail/v1.0.0/', views.CvDetail.as_view(), name='cv_detail'),
    path('cv_deliver/v1.0.0/', views.CvDeliver.as_view(), name='cv_deliver'),
    path('cv_download_pdf/v1.0.0/', views.MakePdf.as_view(), name='cv_download_pdf'),
    # 个人简历文件上传/删除
    path('upload_cv/v1.0.0/', views.UploadCvPdf.as_view(), name='upload_cv'),
]
