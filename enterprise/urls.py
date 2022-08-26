from django.urls import path, include
from enterprise import views_location as loc_views
from enterprise.view import views, views_positions, view_cv_position
from enterprise.view.views_positions import ShowField, ShowPositionClass

urlpatterns = [
    # path('home/', views.home, name='home'),
    path("index/", views.EnterpriseIndexView.as_view(), name="enterprise_index"),
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
    # path("personnel-retrieval/v1.0.0/", views.PersonnelRetrieval.as_view(), name="personnel_retrieval"),

    # 优化后：人才检索
    path("personnel-retrieval/v1.0.0/", views.PersonnelRetrievalLike.as_view(), name="personnel_retrieval_like"),

    # 工具接口：初始CV全表like_str字段数据
    path("default-like-str-cv/", views.DefaultLikeStrCv.as_view()),

    # 职位检索
    # 因为参数是可变的，参数不确定所以此处不能用drf中要求的url格式，使用/?Search_term='x'格式
    # path("position-retrieval/v1.0.0/", views.PositionRetrieval.as_view(), name="position_retrieval"),

    # 多线程重构后职位检索(先保留，之后可能会用到多线程解决方案)
    # path("position-retrieval-pool/v1.0.0/", views.PositionRetrievalTest.as_view(), name="personnel_retrieval_pool"),

    # 重构数据库后职位检索
    path("position-retrieval-like/v1.0.0/", views.PositionRetrievalLike.as_view(), name="personnel_retrieval_like"),

    # 工具接口：新增职位
    path("insert-position/", views.InsertPosition.as_view()),

    # 工具接口：初始全表like_str字段数据
    path("default-like-str-position/", views.DefaultLikeStrPosition.as_view()),

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

    # 位置服务
    path("initial_metro/", loc_views.InitialMetroInfo.as_view()),
    path("initial_enterprise_location/", loc_views.InitialEnterpriseLocation.as_view()),
    path("nearby_enterprise/", loc_views.NearbyEnterprise.as_view()),
    path("metro_list/", loc_views.MetroList.as_view()),

    # 人才推荐
    path("candidatesrecommendation/v1.0.0/<int:rcm_id>/", views.CandidatesRecommendation.as_view()),

    # 新岗位表数据初始化
    path("inserts_position_new/v1.0.0/", views.PositionNewInsert.as_view()),

    # 职位部分（新表重构）
    path("position-make/v1.0.1/", views_positions.PositionMake.as_view()),

    # 职位复制
    path("position-copy/v1.0.1/", views_positions.PositionMakeCopy.as_view()),

    # field表数据初始化
    path("field-insert/v1.0.1/", views_positions.FieldInsertData.as_view()),

    # 岗位上线/下线/职位刷新
    path("post-position/v1.0.1/", views_positions.PostPosition.as_view()),

    # 发布职位审核（机器审核，非人工审核）(1:规范，2：不规范，3：疑似)
    path("position-examine/v1.0.1/", views_positions.PositionExamine.as_view()),

    # 行业类型列表
    path("show-field/v1.0.1/", ShowField.as_view()),

    # 岗位类型列表
    path("show-pst-class/v1.0.1/", ShowPositionClass.as_view()),

    # PositionClass数据初始化
    path("read-csv/v1.0.1/", views_positions.read_csv.as_view()),

    # 职位福利列表tag
    path("show-tag/v1.0.1/", views_positions.ShowTag.as_view()),

    # 职位关键字列表jobkeywords
    path("show-jobkeywords/v1.0.1/", views_positions.ShowJobkeywords.as_view()),

    # 人才信息（收藏人才）
    path("position-collection/v1.0.1/", view_cv_position.PositionCollectionList.as_view()),

    # V2.0版本企业端：人才检索
    path("personnel-retrieval/v1.0.1/", view_cv_position.PositionNewCvRetrieval.as_view()),

    # V2.0版本企业端：人才检索中(快捷搜索中岗位信息查询)
    path("personnel-retrieval-quick-search/v1.0.1/", view_cv_position.PositionNewCvRetrievalQuickSearch.as_view()),

    # V2.0版本企业端：获取企业中发布的岗位列表（用于人才检索中快捷搜索的选项列表）
    path("enterprise-position/v1.0.1/", view_cv_position.EnterprisePosition.as_view())
]
