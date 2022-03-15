from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register_to_student/', views.registerStudentView.as_view(), name='register_to_student'),
    path('certificte_to_student/', views.studentCertificationView.as_view()),
    path('upload_student_info_file/', views.updateStudentValidationViaFile.as_view()),
    path('<int:class_id>/upload_exam_file/', views.updateStudentExamStatusViaFile.as_view()),
    path('certification_editing/', views.certEditionView.as_view()),
    path('<int:cert_id>/certification_sample_uploading/', views.editCertificationSample),
    path('teacher_editing/', views.teacherEditionView.as_view()),
    path('<int:teacher_id>/teacher_photo_uploading/', views.editTeacherPhoto),
    path('course_editing/', views.courseEditionView.as_view()),
    path('<int:course_id>/course_ads_picture_uploading/', views.editCourseAdsPicture),
    path('class_editing/', views.classEditionView.as_view()),
    path('<int:class_id>/class_details/', views.classDetailsView.as_view()),
    path('<int:student_id>/student_details/', views.studentDetailsView.as_view()),
    path('<int:class_id>/students_management/', views.classStudentsManagementView.as_view()),
    path('binding_xet_account/', views.bindingXetUser.as_view()),
    path('binding_exam/', views.examListSearch.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)