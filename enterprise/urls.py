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
    # 职位列表
    path("positions-list/", views.PositionsListView.as_view(), name="positions"),
    # 职位详情
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

    # 职位检索
    path("position-retrieval/", views.PositionRetrieval.as_view(), name="position_retrieval"),

    # 协作HR管理
    path("cooperation-hr/", include([
        path("", views.HRCooperation.as_view()),
        path("<int:hr_id>/", views.HRCooperation.as_view()),
    ])),
    # 人才收藏。增加/删除/查询
    path("collections/", include([
        path("", views.CollectionsView.as_view()),
        path("<int:user_id>/", views.CollectionsView.as_view()),
    ])),
    # 企业岗位推荐
    path("recommend-positions/", include([
        path("", views.RecommendPositionWithinEnterprise.as_view()),
        path("<int:rcm_id>/", views.RecommendPositionWithinEnterprise.as_view()),
    ])),
    # 针对用户条件推荐
    path("recommend-positions-for-user/<int:user_id>/", views.RecommendPositionForUser.as_view()),

    # path("init_cooperation/", views.InitialCoopHRView.as_view()),
    # 职位编辑。增删改查
    path("position-make/v1.0.0/", include([
        # 添加和更新
        path("", views.PositionData.as_view(), name="position-add-update"),
        # 查询和删除
        path("<int:position_id>/", views.PositionData.as_view(), name="position-data-delete"),
    ])),
    # 测试
    path("re/", views.RE.as_view()),
    # 工具接口，初始化Applications表中hr数据（不添加接口文档）
    path("application_hr/v1.0.0/", views.ApplicationsHr.as_view(), name="Application-Hr"),
    # 候选人部分（删除部分不添加接口文档）
    path("application_user/v1.0.0/", views.Candidates.as_view(), name="Application-User"),
    # 获取企业信息
    path("enterprise_hr/v1.0.0/", views.EnterpriseInformation.as_view(), name="EnterpriseInformation"),

    path("import-enterpriseinfo/", views.ImportCompany.as_view()),
    path("import-position/", views.ImportPosition.as_view()),
    # 人才推荐
    path("candidatesrecommendation/v1.0.0/<int:rcm_id>/",views.CandidatesRecommendation.as_view()),

]
