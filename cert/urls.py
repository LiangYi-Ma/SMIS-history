from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static
from . import api_practice as practice_views
from . import api_test_data_create as test_views


urlpatterns = [
    # 注册为学员
    path('register_to_student/', views.registerStudentView.as_view(), name='register_to_student'),
    path('certificte_to_student/', views.studentCertificationView.as_view()),
    path('upload_student_info_file/', views.updateStudentValidationViaFile.as_view()),
    # 绑定小鹅通账号
    path('binding_xet_account/', views.bindingXetUser.as_view()),
    path('<int:class_id>/upload_exam_file/', views.updateStudentExamStatusViaFile.as_view()),
    # 为班级绑定考试
    path('binding_exam/', views.examListSearch.as_view()),
    # 证书视图
    path('certification_editing/', views.certEditionView.as_view()),
    # 证书样图上传
    path('<int:cert_id>/certification_sample_uploading/', views.editCertificationSample),
    # 检查班级中学员证书发放资格
    path('<int:class_id>/check_issuing_qualification/', views.checkIssuingQualificationByClassID.as_view()),
    # 教师视图
    path('teacher_editing/', views.teacherEditionView.as_view()),
    path('<int:teacher_id>/teacher_details/', views.TeacherDetail.as_view()),
    # 教师照片上传
    path('<int:teacher_id>/teacher_photo_uploading/', views.editTeacherPhoto),
    # 课程视图
    path('course_editing/', views.courseEditionView.as_view()),
    # 课程宣传图上传
    path('<int:course_id>/course_ads_picture_uploading/', views.editCourseAdsPicture),
    # 班级视图
    path('class_editing/', views.classEditionView.as_view()),
    # 班级详情
    path('<int:class_id>/class_details/', views.classDetailsView.as_view()),
    # 班级学员管理
    path('<int:class_id>/students_management/', views.classStudentsManagementView.as_view()),
    # 学员详情
    path('<int:student_id>/student_details/', views.studentDetailsByIDView.as_view(),name="根据学员ID查询学员详细信息"),
    path('my_details/', views.studentDetailsBySessionView.as_view(), name="根据session查询学员详细信息"),
    # 补更新线上课学习时间
    path('<int:class_id>/update_online_study_record_by_hand/', views.updateOnlineStudyRecordsByHand.as_view()),

    # 参与实训
    path('<int:class_id>/join_practice/', practice_views.startPractice.as_view(), name="进入实训"),
    # 学员合法性验证
    path('student_validation/', practice_views.studentValidationCheck.as_view(), name="学员合法性验证"),
    # 实训结果上传
    path('upload_practice_result/', practice_views.updatePracticeRecord.as_view(), name="学员实训结果上传"),
    # 验证教师身份
    path('teacher_validation/', practice_views.teacherValidationCheck.as_view(), name="教师身份验证"),
    # 查询学员实验数据
    path('process_data/<int:student_id>/', practice_views.getPracticeProgressData.as_view(), name="查询学员实验数据"),

    # 客服咨询Post
    path('consultation/', views.CustomerServiceConsultation.as_view()),
    # 用户考试结果更新
    path('student_exam_update/', views.StudentExamUpdate.as_view()),
    # 主页GET
    path('index_frontend/', views.HomeCourseCertification.as_view()),
    # 证书详情
    path('<int:cert_id>/certification_detail/', views.CertificationDetail.as_view()),
    # 课程详情
    path('<int:course_id>/course_detail/', views.CourseDetail.as_view()),
    # 测试接口
    path('create_teat_data/', test_views.CreateTestData.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
