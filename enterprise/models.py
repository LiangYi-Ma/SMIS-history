from django.db import models
from datetime import datetime, timedelta
from django.urls import reverse

from django.utils import timezone
from taggit.managers import TaggableManager
from rest_framework.pagination import LimitOffsetPagination
# 让taggit支持中文标签
from taggit.models import TagBase, GenericTaggedItemBase
from django.utils.text import slugify
from django.utils.translation import gettext, gettext_lazy as _

from user.models import User
from SMIS.constants import EDUCATION_LEVELS, NATIONS, MARTIAL_CHOICES, USER_CLASSES, SEX_CHOICE, SKILL_CHOICES, \
    NATURE_CHOICES, FINANCING_STATUS_CHOICES, PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, JOB_NATURE_CHOICES, \
    ENTITY_LIST



# Create your models here.

def is_null(value):
    return value in ["", None, "null", "undefined"]


"""TAG SETTING"""


class SettingChineseTag(TagBase):
    # allow_unicode=True，才能支持中文
    slug = models.SlugField(verbose_name=_("slug"), unique=True, max_length=100, allow_unicode=True)
    is_self_setting = models.BooleanField(verbose_name="是否是自定义标签", default=False, blank=True)
    """暂未实装，还没找到修改这个表的方法"""
    for_which_entity = models.IntegerField(choices=ENTITY_LIST, verbose_name="所属实体",
                                           blank=True, default=0)

    # 覆盖，用来计算slug的，也要添加allow_unicode=True参数
    def slugify(self, tag, i=None):
        slug = slugify(tag, allow_unicode=True)
        if i is not None:
            slug += "_%d" % i
        return slug

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        app_label = "taggit"


class TaggedWhatever(GenericTaggedItemBase):
    # 自定义的模型类传进来
    tag = models.ForeignKey(
        SettingChineseTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )

    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')


"""所有自定义标签，已删除，不用这个表了"""


# class SelfSettingTags(models.Model):
#     id = models.AutoField(primary_key=True)
#     tag = models.ForeignKey(SettingChineseTag, on_delete=models.CASCADE, verbose_name="标签")
#     entity = models.IntegerField(choices=ENTITY_LIST, blank=True, default=0,
#                                  verbose_name="所属实体")
#
#     def is_self_setting(self):
#         return True
#
#     def __str__(self):
#         return self.tag.name


# 岗位类别表
class PositionClass(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10, verbose_name='岗位类别名称')
    desc = models.CharField(max_length=50, verbose_name='岗位类别描述', blank=True, null=True)
    parent = models.ForeignKey('self', default=0, null=True, blank=True, related_name='children', verbose_name='上级分类',
                               limit_choices_to={'is_root': True}, on_delete=models.SET_DEFAULT)
    is_root = models.BooleanField(default=False, verbose_name='是否是一级分类')
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    # image = models.ImageField(upload_to='static/img/field', verbose_name='分类图片', null=True, blank=True)

    class Meta:
        verbose_name = '岗位类别表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Field(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15, verbose_name='领域名称')
    desc = models.CharField(max_length=50, verbose_name='领域描述', blank=True, null=True)
    parent = models.ForeignKey('self', default=0, null=True, blank=True, related_name='children',
                               verbose_name='上级分类', limit_choices_to={'is_root': True}, on_delete=models.SET_DEFAULT)
    is_root = models.BooleanField(default=False, verbose_name='是否是一级分类')
    is_enable = models.BooleanField(default=True, verbose_name="是否启用")

    # image = models.ImageField(upload_to='static/img/field', verbose_name='分类图片', null=True, blank=True)

    class Meta:
        verbose_name = '领域表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 员工规模表
class NumberOfStaff(models.Model):
    id = models.AutoField(primary_key=True)
    min_number = models.IntegerField(null=True, blank=True, verbose_name='当前规模下限(人)')
    max_number = models.IntegerField(null=True, blank=True, verbose_name='当前规模上限(人)')

    class Meta:
        verbose_name = '员工规模表'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.min_number and self.max_number:
            return str(self.min_number) + "-" + str(self.max_number)
        elif self.min_number:
            return ">" + str(self.min_number)
        else:
            return "<" + str(self.max_number)


# 企业信息表
class EnterpriseInfo(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=18, verbose_name='企业名称')
    field = models.ForeignKey(Field, null=True, blank=True, verbose_name='业务领域',
                              # limit_choices_to={'is _root': True},
                              on_delete=models.SET_NULL)
    staff_size = models.ForeignKey(NumberOfStaff, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name="企业规模（人）")

    address = models.CharField(max_length=50, verbose_name="公司地址")
    site_url = models.URLField(verbose_name="企业官网", blank=True, null=True)
    logo = models.ImageField(upload_to='static/img/enterprise_logo/',
                             null=True, blank=True, default="static/img/default_img.jpg", verbose_name='企业logo')

    nature = models.IntegerField(choices=NATURE_CHOICES,
                                 null=True, blank=True, verbose_name='企业性质')

    financing_status = models.IntegerField(choices=FINANCING_STATUS_CHOICES,
                                           null=True, blank=True, verbose_name="上市/投融资状态")
    establish_year = models.IntegerField(verbose_name="企业成立年份", default=2000)
    introduction = models.TextField(max_length=500, default="暂无公司简介……", verbose_name="企业基本介绍")

    tags = TaggableManager(through=TaggedWhatever, blank=True)

    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    class Meta:
        verbose_name = "企业信息表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 岗位信息表
class Position(models.Model):
    id = models.AutoField(primary_key=True)
    enterprise = models.ForeignKey(EnterpriseInfo, on_delete=models.CASCADE, verbose_name='企业')
    pst_class = models.ForeignKey(PositionClass, limit_choices_to={'is_root': False}, on_delete=models.SET_NULL,
                                  null=True, blank=True, verbose_name="岗位类别")
    fullname = models.CharField(max_length=10, verbose_name='岗位扩展名称（别称，默认为岗位类别）', null=True, blank=True)
    job_content = models.CharField(max_length=150, verbose_name='工作内容', null=True, blank=True)
    requirement = models.CharField(max_length=150, verbose_name='岗位基本要求', null=True, blank=True)
    extra_info = models.CharField(max_length=150, verbose_name='补充说明', null=True, blank=True)
    # is_posting = models.BooleanField(default=False, verbose_name='是否正在发布招聘')

    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    class Meta:
        verbose_name = "岗位信息表"
        verbose_name_plural = verbose_name

    def name(self):
        if not is_null(self.fullname):
            return str(self.fullname)
        else:
            return str(self.pst_class.name)

    def __str__(self):
        return self.name()

    def was_updating_recently(self):
        now = timezone.now()
        return now - timedelta(days=7) <= self.update_time <= now

    def is_posting(self):
        try:
            post_info = Recruitment.objects.get(position_id=self.id, is_closed=False)
        except:
            return False
        now = timezone.now().date()
        if post_info and post_info.post_limit_time >= now:
            return True
        else:
            return False


# 招聘表
class Recruitment(models.Model):
    id = models.AutoField(primary_key=True)
    enterprise = models.ForeignKey(EnterpriseInfo, verbose_name="企业名字", on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name="岗位名称")
    number_of_employers = models.IntegerField(null=True, blank=True, verbose_name="招聘人数")
    education = models.IntegerField(choices=EDUCATION_LEVELS, null=True, blank=True, verbose_name="最低学历要求")
    city = models.IntegerField(choices=PROVINCES_CHOICES, null=True, blank=True, verbose_name="工作地点")

    salary_min = models.IntegerField(null=False, verbose_name="最低入职工资")
    salary_max = models.IntegerField(null=False, verbose_name="最高入职工资")
    salary_unit = models.IntegerField(choices=TIME_UNIT_CHOICES, default=1,
                                      null=False, verbose_name="待遇水平单位")

    job_experience = models.IntegerField(choices=YEAR_CHOICES, default=1,
                                         null=False, verbose_name="工作经验要求")

    job_nature = models.IntegerField(choices=JOB_NATURE_CHOICES, default=1,
                                     null=False, verbose_name="工作性质")
    post_limit_time = models.DateField(null=True, verbose_name="发布截止时限")

    # 中途撤销，默认否，撤销操作后True
    is_closed = models.BooleanField(null=True, blank=True, verbose_name="是否已经撤销/过期", default=False)

    class Meta:
        verbose_name_plural = "招聘行为表"

    def refresh_is_closed(self):
        if self.post_limit_time <= datetime.now():
            self.is_closed = True

    # def __str__(self):
    #     return self.enterprise + "/" + self.position


# 应聘行为表
class Applications(models.Model):
    id = models.AutoField(primary_key=True)
    cv = models.ForeignKey("cv.CV", on_delete=models.CASCADE, verbose_name="所投简历")
    recruitment = models.ForeignKey(Recruitment, on_delete=models.CASCADE, verbose_name="招聘信息")

    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')

    progress = models.IntegerField(null=False, verbose_name="应聘进度", default=0, blank=True)

    def candidate_age(self):
        return self.cv.user_id.personalinfo.age()

    def candidate_education_level(self):
        return self.cv.user_id.personalinfo.education

    def is_edu_match(self):
        user_edu = self.cv.user_id.personalinfo.education
        if is_null(user_edu):
            return False
        rcm_edu = self.recruitment.education
        return user_edu >= rcm_edu

    def is_jobExp_match(self):
        rcm_pst = self.recruitment.position.pst_class
        user_pst = self.cv.user_id.personalinfo.jobexperience_set.all()
        for i in user_pst:
            if i.position == rcm_pst:
                return True
        return False

    def is_salary_match(self):
        user_slr = self.cv.expected_salary
        if is_null(user_slr):
            return True
        rcm_slr = self.recruitment.salary_max
        rcm_unit = self.recruitment.salary_unit
        if is_null(rcm_slr):
            return True
        if rcm_unit == 0:
            return rcm_slr / 12 >= user_slr
        elif rcm_unit == 1:
            return rcm_slr >= user_slr
        else:
            return rcm_slr * 21.75 >= user_slr

    def is_workingYears_match(self):
        user_job_set = self.cv.user_id.personalinfo.jobexperience_set.all()
        rcm_years = self.recruitment.job_experience
        if is_null(rcm_years):
            return True
        working_years = 0
        for job in user_job_set:
            working_years += job.working_years()
        if rcm_years in [0, 1]:
            return True
        elif rcm_years <= 2 and working_years > 0:
            return True
        elif rcm_years <= 3 and working_years >= 1:
            return True
        elif rcm_years <= 4 and working_years >= 3:
            return True
        elif rcm_years <= 5 and working_years >= 5:
            return True
        elif rcm_years <= 6 and working_years >= 10:
            return True
        else:
            return False

    def is_field_match(self):
        user_field = self.cv.industry.id
        rcm_field = self.recruitment.enterprise.field.parent_id
        if rcm_field is None:
            rcm_field = self.recruitment.enterprise.field.id
        return user_field == rcm_field

    def refresh_progress(self):
        if (self.recruitment.post_limit_time <= datetime.now()) or (self.recruitment.is_closed is True):
            self.progress = 3
        else:
            pass

    class Meta:
        verbose_name_plural = "应聘行为表"


class PositionsData(models.Model):
    """
    职位数据表：浏览次数、参与次数、收藏次数、热度
    """
    id = models.IntegerField(primary_key=True)
    view = models.IntegerField(default=0)
    join = models.IntegerField(default=0)
    collect = models.IntegerField(default=0)

    def hot(self):
        return self.view + self.join + self.collect

    class Meta:
        verbose_name_plural = "职位数据表"


# 人才收藏表
class JobHuntersCollection(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    enterprise_id = models.IntegerField(null=True, blank=True)
    collector = models.IntegerField(null=True, blank=True, verbose_name="企业协作id")

    def get_user_obj(self):
        try:
            return User.objects.get(id=self.user_id)
        except:
            return None

    class Meta:
        verbose_name_plural = "求职者收藏表"


# 协作表
class EnterpriseCooperation(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    enterprise_id = models.IntegerField(null=True, blank=True)
    join_date = models.DateField(auto_now_add=True, verbose_name="加入时间")
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=0)

    def get_user_object(self):
        try:
            return User.objects.get(id=self.user_id)
        except:
            return None

    def get_enterprise_object(self):
        try:
            return EnterpriseInfo.objects.get(id=self.enterprise_id)
        except:
            return None

# 分页器，不需要迁移
class StandardResultSetPagination(LimitOffsetPagination):
    # 默认页尺寸，一页返回20条记录
    default_limit = 20
    # 页尺寸在URL中的赋值名
    limit_query_param = "limit"
    # 偏移量，从偏移量的数字后开始拿数据
    offset_query_param = "offset"
    # 页尺寸上限
    max_limit = None




