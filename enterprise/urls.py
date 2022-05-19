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
]
