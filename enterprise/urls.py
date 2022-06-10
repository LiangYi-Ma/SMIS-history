from django.urls import path, include
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
    path("personnel-retrieval/v1.0.0/", views.PersonnelRetrieval.as_view(), name="personnel_retrieval"),
    # 职位检索

    path("position-retrieval/v1.0.0/", views.PositionRetrieval.as_view(), name="position_retrieval"),

    # 根据session获取收藏的职位列表
    path("position-collection-list/v1.0.0/", views.PositionCollectionList.as_view(), name="PositionCollectionList"),
    # 根据session添加职位收藏
    path("position-collection-add/v1.0.0/", views.PositionCollectionAdd.as_view(), name="PositionCollectionAdd"),
    # 根据session和职位id取消收藏
    path("position-collection-cancel/v1.0.0/", views.PositionCollectionCancel.as_view(),
         name="PositionCollectionCancel"),

    path("position-retrieval/", views.PositionRetrieval.as_view(), name="position_retrieval"),

    path("cooperation-hr/", include([
        path("", views.HRCooperation.as_view()),
        path("<int:hr_id>/", views.HRCooperation.as_view()),
    ])),

    path("collections/", include([
        path("", views.CollectionsView.as_view()),
        path("<int:user_id>/", views.CollectionsView.as_view()),
    ])),

    # path("init_cooperation/", views.InitialCoopHRView.as_view()),
    # 职位操作
    path("position-make/v1.0.0/", include([
        # 添加和更新
        path("", views.PositionData.as_view(), name="position-add-update"),
        # 查询和删除
        path("<int:position_id>/", views.PositionData.as_view(), name="position-data-delete"),
    ])),

]
