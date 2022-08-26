import calendar
import time

from django.db import models
import datetime
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.contrib import auth
from django.contrib.auth.models import User
from enterprise.models import PositionClass, PROVINCES_CHOICES
from SMIS.constants import EDUCATION_LEVELS, NATIONS, MARTIAL_CHOICES, USER_CLASSES, SEX_CHOICE, SKILL_CHOICES, \
    NATURE_CHOICES, FINANCING_STATUS_CHOICES, PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, JOB_NATURE_CHOICES, \
    ONLINE_STATUS, IDENTITY, ENTITY_LIST
import datetime
from taggit.managers import TaggableManager
from enterprise.models import TaggedWhatever, Field, JobKeywords
from taggit.models import TagBase, GenericTaggedItemBase
from django.utils.text import slugify
from django.utils.translation import gettext, gettext_lazy as _


# Create your models here.


class WxUserPhoneValidation(models.Model):
    id = models.AutoField(primary_key=True)
    unvalid_phone_number = models.CharField(max_length=20, null=True, verbose_name='手机号码')
    valid_datetime = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    valid_code = models.CharField(max_length=10, null=False, default="0", verbose_name="验证码")

    # is_expired = models.BooleanField(default=False, verbose_name="是否已过期")

    class Meta:
        verbose_name_plural = '(WX)手机验证码暂存表'

    # def refresh_status(self):
    #     expiry_time = self.valid_datetime + datetime.timedelta(minutes=10)
    #     self.is_expired = (datetime.datetime.now() > expiry_time)

    def is_expired(self):
        expiry_time = self.valid_datetime + datetime.timedelta(minutes=10)
        if datetime.datetime.now() > expiry_time:
            return True
        else:
            return False
        # return datetime.datetime.now() > expiry_time

    is_expired.boolean = True
    is_expired.short_description = "是否已过期？"


class User_WxID(models.Model):
    # id = models.AutoField(primary_key=True)
    wx_id = models.CharField(max_length=100, verbose_name="用户微信号", null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")

    class Meta:
        verbose_name_plural = '用户&绑定微信号映射表'


class EmailCode(models.Model):
    email = models.EmailField(verbose_name="用户邮箱", null=True)
    code = models.IntegerField(verbose_name="验证码", null=True)
    code_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='验证码生成时间')

    class Meta:
        verbose_name_plural = '用户邮箱验证码表'


class Adcode(models.Model):
    id = models.AutoField(primary_key=True)
    first = models.CharField(max_length=15, null=True, blank=True, verbose_name="省级")
    second = models.CharField(max_length=15, null=True, blank=True, verbose_name="市级")
    third = models.CharField(max_length=20, null=True, blank=True, verbose_name="县/区级")
    adcode = models.CharField(max_length=6, null=True, blank=True, verbose_name="行政区码")

    class Meta:
        verbose_name_plural = "行政区码表-2022"


# 个人信息表
class PersonalInfo(models.Model):
    id = models.OneToOneField(User, primary_key=True, verbose_name='选择用户', on_delete=models.CASCADE)
    user_class = models.IntegerField(choices=USER_CLASSES, null=True, blank=True, verbose_name='用户类别')
    phone_number = models.CharField(max_length=20, null=True, verbose_name='手机号码')
    qq_number = models.CharField(max_length=15, null=True, blank=True, verbose_name='QQ号')

    sex = models.IntegerField(choices=SEX_CHOICE, null=True, blank=True, verbose_name='性别')
    nation = models.IntegerField(choices=NATIONS, null=True, blank=True, verbose_name='民族')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='出生日期')
    height = models.IntegerField(null=True, blank=True, verbose_name='身高')
    weight = models.FloatField(null=True, blank=True, verbose_name='体重')
    postcode = models.CharField(max_length=6, null=True, blank=True, verbose_name='邮编')
    home_address = models.CharField(max_length=120, null=True, blank=True, verbose_name='家庭住址')
    birth_address = models.IntegerField(choices=PROVINCES_CHOICES, null=True,
                                        blank=True, verbose_name='家乡省份')
    martial_status = models.IntegerField(choices=MARTIAL_CHOICES, verbose_name='婚姻状况',
                                         null=True, blank=True, )
    education = models.IntegerField(choices=EDUCATION_LEVELS, verbose_name='最高学历',
                                    null=True, blank=True)

    identity = models.IntegerField(choices=IDENTITY, verbose_name="当前身份", null=True, blank=True, default=0)
    wechat = models.CharField(max_length=28, verbose_name="微信号", null=True, blank=True)
    living_city = models.ForeignKey(Adcode, verbose_name="居住地", null=True, blank=True, on_delete=models.SET_NULL)
    job_start = models.DateField(null=True, blank=True, default=None, verbose_name="参加工作时间")
    image = models.ImageField(upload_to='static/img/',
                              null=True, blank=True, verbose_name='证件照/头像',
                              default="static/img/default_img.jpg")

    update_date = models.DateField(auto_now=True)
    online_status = models.IntegerField(null=True, blank=True, verbose_name='在线状态', choices=ONLINE_STATUS)
    online_time = models.DateTimeField(null=True, blank=True, verbose_name='在线状态更新时间')

    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def name(self):
        user_obj = User.objects.get(id=self.id_id)
        return user_obj.last_name + user_obj.first_name

    def __str__(self):
        return str(self.id)

    def active_time(self):
        # 计算活跃时间
        try:
            at = self.id.last_login
            ds = datetime.datetime.now() - at
            year = int(time.strftime('%Y', time.localtime()))
            month = int(time.strftime('%m', time.localtime()))
            days = calendar.monthrange(year, month)[1]
            days_1 = calendar.monthrange(year - 1 if month == 1 else year, 12 if month == 1 else month - 1)[1]
            days_2 = calendar.monthrange(year - 1 if month <= 2 else year, 12 if month <= 2 else month - 1)[1]
            days_3 = calendar.monthrange(year - 1 if month <= 3 else year, 12 if month <= 3 else month - 1)[1]
            days_4 = calendar.monthrange(year - 1 if month <= 4 else year, 12 if month <= 4 else month - 1)[1]
            days_5 = calendar.monthrange(year - 1 if month <= 5 else year, 12 if month <= 5 else month - 1)[1]
            if ds.days <= 0:
                return 1  # 当天
            elif ds.days <= 7:
                return 2  # 一周
            elif ds.days <= 14:
                return 3  # 两周
            elif ds.days <= days:
                return 4  # 近一个月
            elif ds.days <= (days + days_1):
                return 5  # 近两个月
            elif ds.days <= (days + days_1 + days_2):
                return 6  # 近三个月
            elif ds.days <= (days + days_1 + days_2 + days_3 + days_4 + days_5):
                return 7  # 近六个月
            else:
                return 8  # 六个月以上
        except Exception as e:
            raise e

    def degree_level(self):
        if self.education == 5:
            return "学士"
        elif self.education == 6:
            return "硕士"
        elif self.education == 8:
            return "博士"
        else:
            return "无"

    def age(self):
        today_d = datetime.datetime.now().date()
        try:
            birth_t = self.date_of_birth.replace(year=today_d.year)
            if today_d > birth_t:
                age = today_d.year - self.date_of_birth.year
            else:
                age = today_d.year - self.date_of_birth.year - 1
            return age
        except:
            return None

    def get_degree(self):
        all_edu = EducationExperience.objects.filter(user_id_id=self.id_id)
        res = 0
        for e in all_edu:
            res = max(res, e.education)
        return res

    def get_work_years(self):
        all_works = JobExperience.objects.filter(user_id_id=self.id_id)
        res = 0
        for w in all_works:
            res += w.working_years()
        return round(res, 3)

    def get_work_code(self):
        years = self.get_work_years()
        if years >= 10:
            res = 6
        elif years >= 5:
            res = 5
        elif years >= 3:
            res = 4
        elif years >= 1:
            res = 3
        else:
            res = 2
        return res

    class Meta:
        verbose_name_plural = '用户个人信息表'


class EducationExperience(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(PersonalInfo, verbose_name='用户信息ID', on_delete=models.CASCADE)
    school = models.CharField(max_length=100, null=True, blank=True, verbose_name='学校名称')
    # 院系名称2.0后不再需要
    department = models.CharField(max_length=15, null=True, blank=True, verbose_name='院系名称')

    major = models.CharField(max_length=100, null=True, blank=True, verbose_name='专业')
    # EDUCATION_LEVELS选项改为了新版的
    education = models.IntegerField(choices=EDUCATION_LEVELS, null=True, blank=True, verbose_name='学历')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始时间')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束时间')

    is_unified_recruit = models.BooleanField(verbose_name="是否统招", default=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def get_owner(self):
        return self.user_id.id

    def get_creator(self):
        return self.user_id.id

    def add_validation(self):
        all_query = EducationExperience.objects.filter(user_id=self.user_id)
        if all_query.count() >= 5:
            return False
        else:
            return True

    def __str__(self):
        return str(self.user_id) + ':' + str(self.school)

    class Meta:
        verbose_name_plural = '教育经历表'


# class PositionSkillChineseTag(TagBase):
#     # allow_unicode=True，才能支持中文
#     slug = models.SlugField(verbose_name=_("slug"), unique=True, max_length=100, allow_unicode=True)
#     is_self_setting = models.BooleanField(verbose_name="是否是自定义标签", default=False, blank=True)
#     """暂未实装，还没找到修改这个表的方法"""
#     position_class = models.ManyToManyField("enterprise.PositionClass",)
#     for_which_entity = models.IntegerField(choices=ENTITY_LIST, verbose_name="所属实体",
#                                            blank=True, default=5)
#
#     # 覆盖，用来计算slug的，也要添加allow_unicode=True参数
#     def slugify(self, tag, i=None):
#         slug = slugify(tag, allow_unicode=True)
#         if i is not None:
#             slug += "_%d" % i
#         return slug
#
#     class Meta:
#         verbose_name = _("tag")
#         verbose_name_plural = _("tags")
#         app_label = "taggit"
#
#
# class TaggedPositionClass(GenericTaggedItemBase):
#     # 自定义的模型类传进来
#     tag = models.ForeignKey(
#         PositionSkillChineseTag,
#         on_delete=models.CASCADE,
#         related_name="%(app_label)s_%(class)s_items",
#     )
#
#     create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
#     update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')


# 工作经历（对于每个user_id,上限10）


class JobExperience(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(PersonalInfo, verbose_name='用户信息ID', on_delete=models.CASCADE)
    enterprise = models.CharField(max_length=18, null=True, blank=True, verbose_name='企业名称')
    position = models.ForeignKey("enterprise.PositionClass", null=True, blank=True, verbose_name='岗位类别',
                                 on_delete=models.SET_NULL)
    job_content = models.CharField(max_length=22, null=True, blank=True, verbose_name='工作内容简述')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始时间')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束时间')

    # 最多5个标签
    # tags = TaggableManager(through=TaggedPositionClass, blank=True, verbose_name="职业技能标签")
    jobkeywords = models.ManyToManyField(JobKeywords, null=True, blank=True, verbose_name="岗位关键词")
    field = models.ForeignKey(Field, null=True, blank=True, default=None, on_delete=models.SET_NULL,
                              verbose_name="行业领域", limit_choices_to={'is _root': False})
    position_name = models.CharField(max_length=100, verbose_name="", null=True, blank=True)
    job_nature = models.IntegerField(choices=JOB_NATURE_CHOICES, null=True, blank=True, verbose_name='工作性质')
    salary_min = models.IntegerField(null=True, blank=True, verbose_name="月薪下限")
    salary_max = models.IntegerField(null=True, blank=True, verbose_name="月薪上限")
    job_desc = models.TextField(max_length=3000, null=True, blank=True, verbose_name='工作描述')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def working_years(self):
        e = datetime.datetime(self.end_date.year, self.end_date.month, self.end_date.day)
        s = datetime.datetime(self.start_date.year, self.start_date.month, self.start_date.day)
        return round((e - s).days / 365, 3)

    def work_year_make(self):
        """ 处理工作年限数据格式 """
        year = self.working_years()
        up_1 = [9, 8]  # +1
        up_5 = [3, 4, 5, 6, 7]  # 变5
        down_0 = [0, 1, 2]  # 变0
        if '.' in str(year):
            yeal = str(year).split('.')
            flag = yeal[1][0]
            if int(flag) in up_5:
                year = f'{int(year)}.5'
            elif int(flag) in down_0:
                year = int(year)
            elif int(flag) in up_1:
                year = int(year) + 1
        return year

    def get_owner(self):
        return self.user_id.id

    def get_creator(self):
        return self.user_id.id

    def add_validation(self):
        all_query = JobExperience.objects.filter(user_id=self.user_id)
        if all_query.count() >= 10:
            return False
        else:
            return True

    def __str__(self):
        return str(self.user_id) + ':' + str(self.enterprise)

    class Meta:
        verbose_name_plural = '工作经历表'


class TrainingExperience(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(PersonalInfo, verbose_name='用户信息ID', on_delete=models.CASCADE)
    training_team = models.CharField(max_length=100, null=True, blank=True, verbose_name='培训单位')
    training_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='培训名称')
    complete_certification = models.ImageField(upload_to='static/img', verbose_name='结课证明', null=True, blank=True,
                                               default=None)
    start_date = models.DateField(null=True, blank=True, verbose_name='开始时间')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束时间')
    training_content = models.TextField(max_length=3000, null=True, blank=True, verbose_name="培训内容")
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def get_owner(self):
        return self.user_id.id

    def get_creator(self):
        return self.user_id.id

    def add_validation(self):
        all_query = TrainingExperience.objects.filter(user_id=self.user_id)
        if all_query.count() >= 5:
            return False
        else:
            return True

    def __str__(self):
        return str(self.user_id) + ':' + str(self.training_name)

    class Meta:
        verbose_name_plural = '培训经历表'


class ProjectExperience(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(PersonalInfo, verbose_name="用户信息ID", on_delete=models.CASCADE)
    project_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="项目名称")
    project_role = models.CharField(max_length=100, null=True, blank=True, verbose_name="项目角色")
    project_desc = models.TextField(max_length=3000, null=True, blank=True, verbose_name="项目描述")
    start_date = models.DateField(null=True, blank=True, verbose_name="开始时间")
    end_date = models.DateField(null=True, blank=True, verbose_name="结束时间")
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def get_owner(self):
        return self.user_id.id

    def get_creator(self):
        return self.user_id.id

    def add_validation(self):
        all_query = ProjectExperience.objects.filter(user_id=self.user_id)
        if all_query.count() >= 10:
            return False
        else:
            return True

    class Meta:
        verbose_name_plural = "项目经历表"


class Evaluation(models.Model):
    id = models.OneToOneField(PersonalInfo, verbose_name='用户信息ID', on_delete=models.CASCADE, primary_key=True)
    teacher_evaluation = models.CharField(max_length=200, null=True, blank=True, verbose_name='教师评价')
    # 新版500字
    self_evaluation = models.TextField(max_length=500, null=True, blank=True, verbose_name='个人优势')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    def __str__(self):
        return str(self.id)

    def name(self):
        user_obj = User.objects.get(id=self.id_id)
        return user_obj.last_name + user_obj.first_name

    class Meta:
        verbose_name_plural = '评价表'


class PrivacySetting(models.Model):
    id = models.IntegerField(primary_key=True)
    phone_hidden = models.BooleanField(blank=True, null=True, default=False)
    name_hidden = models.BooleanField(blank=True, null=True, default=False)
    email_hidden = models.BooleanField(blank=True, null=True, default=False)

    def get_user_obj(self):
        return User.objects.get(id=self.id)

    def get_owner(self):
        return User.objects.get(id=self.id)

    class Meta:
        verbose_name_plural = "隐私设置表"
