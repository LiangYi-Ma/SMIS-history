from django.db import models
from django.contrib.auth.models import User
from SMIS import constants
import datetime


# Create your models here.


class studentInfo(models.Model):
    student_id = models.IntegerField(primary_key=True, verbose_name='用户/学员id')
    student_name = models.CharField(max_length=16, blank=True, null=True, verbose_name="全名")
    phone_number = models.CharField(max_length=11, null=True, verbose_name='手机号码')
    wechat_openid = models.CharField(max_length=32, null=True, blank=True, verbose_name="微信号")
    id_number = models.CharField(max_length=18, null=True, blank=True, verbose_name="身份证号")
    sex = models.IntegerField(choices=constants.SEX_CHOICE, null=True, blank=True, verbose_name="性别")
    is_valid = models.IntegerField(choices=constants.XET_VALIDATION, default=0, null=True, blank=True,
                                   verbose_name="小鹅通账号认证")
    xet_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return str(self.student_name)

    def update_sex(self):
        if int(self.id_number[16]) % 2 == 0:
            self.sex = 0
            print('女的')
        else:
            self.sex = 1
            print('男的')
        self.save()

    class Meta:
        verbose_name_plural = '学员信息表'


class teacherInfo(models.Model):
    teacher_id = models.AutoField(primary_key=True)
    teacher_name = models.CharField(max_length=16, blank=True, null=True, verbose_name="教师姓名")
    phone_number = models.CharField(max_length=11, null=True, verbose_name='手机号码')
    wechat_openid = models.CharField(max_length=32, null=True, blank=True, verbose_name="微信号")
    teaching_field = models.IntegerField(choices=constants.TEACHING_FIELDS, default=0, verbose_name="教师授课领域")
    level = models.IntegerField(choices=constants.TEACHER_LEVEL, default=0, verbose_name="教师职级")
    self_introduction = models.CharField(max_length=120, null=True, blank=True, default="该教师简介暂未更新",
                                         verbose_name="教师简介")
    photo = models.ImageField(upload_to='static/img/teachers',
                              null=True, blank=True, verbose_name='教师证件照',
                              default="static/img/default_img.jpg")

    def __str__(self):
        return str(self.teacher_name)

    class Meta:
        verbose_name_plural = '教师信息表'


class certificationInfo(models.Model):
    cert_id = models.AutoField(primary_key=True)
    cert_name = models.CharField(max_length=32)
    cert_level = models.IntegerField(choices=constants.CERTIFICATION_LEVEL,
                                     blank=True, null=True, verbose_name="证书等级")
    issuing_unit = models.CharField(max_length=32, blank=True, null=True, verbose_name="发证单位")
    cert_introduction = models.CharField(max_length=256, blank=True, null=True, verbose_name="证书简介")
    testing_way = models.IntegerField(choices=constants.TESTING_WAYS, default=1, verbose_name="考核方式")
    aim_people = models.CharField(max_length=64, blank=True, null=True, verbose_name="针对人群")
    cor_positions = models.CharField(max_length=64, blank=True, null=True, verbose_name="相关岗位")
    cert_sample = models.ImageField(upload_to='static/img/certification_samples',
                                    null=True, blank=True, verbose_name='证书样图',
                                    default="static/img/default_img.jpg")
    # 有效期指该证书自签发之日起有效时限，如雅思证书的有效期是2年
    expiry_date = models.CharField(max_length=16, blank=True, null=True, verbose_name="证书有效期")

    def __str__(self):
        return ""

    class Meta:
        verbose_name_plural = '证书信息表'


class courseInfo(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=32, null=True, blank=True, verbose_name="课程名")
    course_direction = models.IntegerField(choices=constants.COURSE_DIRECTION, blank=True, null=True,
                                           verbose_name="课程方向")
    course_type = models.IntegerField(choices=constants.COURSE_TYPE, blank=True, null=True, verbose_name="课程类别")
    course_price = models.FloatField(null=True, blank=True, verbose_name="课程售价")
    course_true_price = models.FloatField(null=True, blank=True, verbose_name="真实售价")
    ads_picture = models.ImageField(upload_to='static/img/course_ads_pictures',
                                    null=True, blank=True, verbose_name='课程宣传图',
                                    default="static/img/default_img.jpg")

    def __str__(self):
        return str(self.course_name)

    class Meta:
        verbose_name_plural = '课程信息表'


class classInfo(models.Model):
    class_id = models.AutoField(primary_key=True)
    class_type = models.IntegerField(choices=constants.CLASS_TYPE, null=True, blank=True, verbose_name="班级类型")
    class_period = models.IntegerField(choices=constants.CLASS_PERIOD, null=True, blank=True, verbose_name="周期类型")
    class_status = models.IntegerField(choices=constants.CLASS_STATUS, null=True, blank=True, verbose_name="班级状态")
    class_start_date = models.DateField(null=True, blank=True, verbose_name="预计开班时间")
    class_end_date = models.DateField(null=True, blank=True, verbose_name="预计结课日期")
    is_exam_exist = models.BooleanField(default=0, verbose_name="是否包含笔试")
    is_practice_exist = models.BooleanField(default=0, verbose_name="是否包含实训")
    min_practice_score = models.FloatField(default=60, verbose_name="实训达标成绩")
    is_cert_exist = models.BooleanField(default=0, verbose_name="是否关联证书")
    is_online_study_exist = models.BooleanField(default=0, verbose_name="是否包含线上课")
    min_study_time = models.IntegerField(default=100, verbose_name="线上课达标时长（h）")

    def __str__(self):
        return str(self.class_id)

    def update_class_status(self):
        now = datetime.datetime.now()
        start = datetime.datetime(self.class_start_date.year, self.class_start_date.month, self.class_start_date.day)
        end = datetime.datetime(self.class_end_date.year, self.class_end_date.month, self.class_end_date.day)
        if start > now:
            self.class_status = 0
        elif end < now:
            self.class_status = 2
        else:
            self.class_status = 1
        self.save()

    class Meta:
        verbose_name_plural = '班级信息表'


class classTeacherCon(models.Model):
    class_teacher_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    teacher_id = models.ForeignKey(teacherInfo, verbose_name='教师', on_delete=models.CASCADE)
    teacher_responsibility = models.CharField(max_length=64, verbose_name="教师职责", blank=True, null=True)

    def __str__(self):
        return str(self.class_id) + "-" + str(self.teacher_id.teacher_name) + "/" + str(self.teacher_responsibility)

    class Meta:
        verbose_name_plural = '班级-教师关联表'


class classExamCon(models.Model):
    class_exam_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    exam_id = models.CharField(max_length=128, verbose_name='考试id', blank=True, null=True)
    min_score = models.FloatField(default=60, verbose_name='考试达标成绩', blank=True, null=True)

    class Meta:
        verbose_name_plural = '班级-考试关联表'


class classCourseCertCon(models.Model):
    class_course_cert_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    course_id = models.ForeignKey(courseInfo, verbose_name='课程', blank=True, null=True, on_delete=models.SET_NULL)
    cert_id = models.ForeignKey(certificationInfo, verbose_name='证书', blank=True, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=64, verbose_name="备注", blank=True, null=True)

    def __str__(self):
        return str(self.class_id) + "-" + str(self.course_id.course_name) + "-" + str(self.cert_id.cert_name)

    class Meta:
        verbose_name_plural = '班级-课程-证书关联表'


class classStudentCon(models.Model):
    class_student_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    student_id = models.ForeignKey(studentInfo, verbose_name='学生', on_delete=models.CASCADE)
    study_progress = models.IntegerField(choices=constants.CERT_PROGRESS_OPTIONS,
                                         verbose_name="线上学习进度", default=2)
    exam_progress = models.IntegerField(choices=constants.CERT_PROGRESS_OPTIONS,
                                        verbose_name="线上考试进度", default=2)
    cert_progress = models.IntegerField(choices=constants.CERT_PROGRESS_OPTIONS,
                                        verbose_name="证书进度", default=2)
    practice_progress = models.IntegerField(choices=constants.CERT_PROGRESS_OPTIONS,
                                            verbose_name="实操进度", default=2)

    def updateClosed2Uncompleted(self):
        if self.class_id.is_exam_exist and self.exam_progress == 2:
            self.exam_progress = 0
        if self.class_id.is_cert_exist and self.cert_progress == 2:
            self.cert_progress = 0
        if self.class_id.is_online_study_exist and self.study_progress == 2:
            self.study_progress = 0
        if self.class_id.is_practice_exist and self.practice_progress == 2:
            self.practice_progress = 0

    def __str__(self):
        return str(self.class_id) + "-" + str(self.student_id.student_name)

    class Meta:
        verbose_name_plural = '班级-学生关联表'


class practiceRecords(models.Model):
    practice_id = models.AutoField(primary_key=True, verbose_name='实训id')
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    student_id = models.ForeignKey(studentInfo, verbose_name='学生', on_delete=models.CASCADE)
    available_times = models.IntegerField(default=3, verbose_name='剩余可实训次数')
    deadline = models.DateField(null=True, blank=True, verbose_name="实训截止日期")
    practice_score = models.FloatField(null=True, blank=True, verbose_name="最高实训成绩")
    latest_update_date = models.DateField(auto_now=True, verbose_name="上次更新日期")

    def is_passed(self):
        return self.practice_score >= self.class_id.min_practice_score

    class Meta:
        verbose_name_plural = '实训结果记录表'


class examRecords(models.Model):
    class_exam_id = models.ForeignKey(classExamCon, primary_key=True, verbose_name='', on_delete=models.CASCADE)
    student_id = models.ForeignKey(studentInfo, verbose_name='学生', on_delete=models.CASCADE)
    join_time = models.DateTimeField(null=True, blank=True, verbose_name="参加考试时间")
    exam_score = models.FloatField(null=True, blank=True, verbose_name="考试成绩")

    def is_passed(self):
        return self.exam_score >= self.class_exam_id.min_score

    class Meta:
        verbose_name_plural = '考试结果记录表'


class onlineStudyRecords(models.Model):
    online_study_id = models.AutoField(primary_key=True, verbose_name='实训id')
    class_id = models.ForeignKey(classInfo, verbose_name='班级', on_delete=models.CASCADE)
    student_id = models.ForeignKey(studentInfo, verbose_name='学生', on_delete=models.CASCADE)
    accumulated_time = models.FloatField(verbose_name='累计时长（h）', default=0)
    latest_time = models.FloatField(verbose_name='上次新增时长（h）', default=0)

    def is_passed(self):
        return self.accumulated_time >= self.class_id.min_study_time

    class Meta:
        verbose_name_plural = '线上课时长记录表'


class updateDateRecords(models.Model):
    """仅记录批量更新的日期（考试、线上课）"""
    class_id = models.ForeignKey(classInfo, primary_key=True, verbose_name="班级id", on_delete=models.CASCADE)
    exam_update_date = models.DateField(verbose_name="上次考试更新时间", null=True, blank=True)
    study_update_date = models.DateField(verbose_name="上次线上课更新时间", null=True, blank=True)

    class Meta:
        verbose_name_plural = '数据更新时间记录表'


class failedUpdateRecords(models.Model):
    """仅记录线上课更新失败日期"""
    class_id = models.ForeignKey(classInfo, primary_key=True, verbose_name="班级id", on_delete=models.CASCADE)
    failed_date = models.DateField(verbose_name="更新失败日期", null=True, blank=True)
    is_updated = models.BooleanField(verbose_name="是否已补更新", null=True, blank=True)

    class Meta:
        verbose_name_plural = '线上课数据更新失败记录表'

