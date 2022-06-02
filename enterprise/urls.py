from django.urls import path
from enterprise.views import *

from . import views

urlpatterns = [
    # path('home/', views.home, name='home'),
    path("index/", EnterpriseIndexView.as_view(), name="enterprise_index"),
    path("enterprise-info/", views.enterprise_info, name="enterprise_info"),
    path("positions/", views.PositionsPageView.as_view(), name="positions"),
    path("hr/", views.HRPageView.as_view(), name="hr"),
    path("data/", views.data_analyse_page, name="data"),
    path("finding/", views.FindingView.as_view(), name="finding_people"),
    path("finding_by_search/", views.finding_page_by_search, name="finding_people_by_search"),
    # path("service/", views.service_page, name="services"),

    # 接口实例
    path("positions-list/", views.PositionsListView.as_view(), name="positions"),
    path("position-details/<int:position_id>/", views.PositionDetailsView.as_view()),

    # 人才检索
    path("personnel-retrieval/", views.PersonnelRetrieval.as_view(), name="personnel_retrieval"),
    # 职位检索
    path("position-retrieval/", views.PositionRetrieval.as_view(), name="position_retrieval"),

    # 根据session获取收藏的职位列表
    path("position-collection-list/", views.PositionCollectionList.as_view(), name="PositionCollectionList"),
    # 根据session添加职位收藏
    path("position-collection-add/", views.PositionCollectionAdd.as_view(), name="PositionCollectionAdd"),
    # 根据session和职位id取消收藏
    path("position-collection-cancel/", views.PositionCollectionCancel.as_view(), name="PositionCollectionCancel")
]
