"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from django.urls import path, include

from . import views

urlpatterns = [
    path("init_groups/", views.InitialSystemGroup.as_view()),
    path("init_user_class/", views.InitialUserClassData.as_view()),
    path("init_user_group/", views.InitialUsersGroups.as_view()),

    path("roles/", include([
        path("", views.Roles.as_view()),
        path("<int:role_id>/", views.Roles.as_view()),
    ])),
]
