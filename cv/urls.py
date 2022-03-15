from django.urls import path

from . import views

urlpatterns = [
    # path('search/', views.search, name='search'),
    path('<int:user_id>/<int:cv_id>/show-cv/', views.show_cv, name='show_cv'),
    path('<int:user_id>/<int:cv_id>/download-cv/', views.save_as_pdf, name='download-cv'),
    path('search_cv_page/', views.SearchCv.as_view(), name='search_cv_page'),
]
