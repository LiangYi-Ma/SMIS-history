from django.urls import path

from . import views
from .forms import UploadImageForm

urlpatterns = [
    path('home/', views.home, name='home'),
    path('edit_password/', views.edit_password, name="edit_password"),
    path('edit_selfinfo/', views.EditSelfInfoView.as_view(), name='edit_selfinfo'),
    # path('edit_experiences/', views.edit_experiences, name='edit_experiences'),
    # path('edit_selfinfo_contact/', views.edit_selfinfo_contact, name='edit_selfinfo_contact'),
    # path('edit_selfinfo_basic/', views.edit_selfinfo_basic, name='edit_selfinfo_basic'),
    # path('edit_selfinfo_edu/', views.edit_selfinfo_edu, name='edit_selfinfo_edu'),
    # path('edit_selfinfo_eva/', views.edit_eva, name='edit_selfinfo_eva'),

    # path('edit_avatar/', views.edit_avatar, name='edit_avatar'),
    path('edit_my_cv/', views.EditCvView.as_view(), name='edit_my_cv'),

    path('find_rcm/<int:pst_class>/', views.find_rcm_by_pst_class, name='find_rcm_by_pst_class'),
    path('search_positions/', views.SearchPositionsView.as_view(), name="search-rcm"),
    path('position_details/<int:rcm_id>/', views.position_details_page, name="position_details"),
    path('my-applications/', views.my_application, name="my-applications"),
    path('my_page/', views.my_page_dic, name="my_page"),
    # 获取用户的隐私设置
    path('privacySetting/',views.PrivacySettingList.as_view(),name="privacySetting"),

]
