from django.db import models
import datetime
from django.utils import timezone

# from user import models
from user.models import User
from SMIS.constants import EDUCATION_LEVELS, NATIONS, MARTIAL_CHOICES, USER_CLASSES, SEX_CHOICE, SKILL_CHOICES, \
    NATURE_CHOICES, FINANCING_STATUS_CHOICES, PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, JOB_NATURE_CHOICES


# Create your models here.

# 技能熟练度描述表
# class Skill(models.Model):
#     SKILL_CHOICE = (
#         ('一般', '一般'),
#         ('了解', '了解'),
#         ('中等', '中等'),
#         ('熟悉', '熟悉'),
#         ('精通', '精通'),
#     )
#
#     skill_level = models.CharField(
#         max_length=4,
#         choices=SKILL_CHOICE,
#         default='中等'
#     )
#
#     def __str__(self):
#         return self.skill_level
#
#     class Meta:
#         verbose_name_plural = '技能水平描述表'


# 行业表
class Industry(models.Model):
    industry_name = models.CharField(max_length=10,
                                     null=True,
                                     verbose_name='行业名称'
                                     )
    industry_meaning = models.CharField(max_length=20,
                                        null=True, blank=True,
                                        verbose_name='行业描述'
                                        )

    def __str__(self):
        return self.industry_name

    class Meta:
        verbose_name_plural = '行业名称表'


# 简历表
class CV(models.Model):
    id = models.AutoField(primary_key=True, db_column='cv_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户姓名')

    # industry = models.ForeignKey(Industry,
    #                              on_delete=models.SET_NULL,
    #                              null=True,
    #                              blank=True,
    #                              verbose_name='所属行业/目标行业',
    #                              )
    # 将行业选择定为领域表的一级分类
    industry = models.ForeignKey("enterprise.Field",
                                 limit_choices_to={'is_root': True},
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 verbose_name='目标行业领域',
                                 )

    major = models.CharField(max_length=15,
                             null=True,
                             blank=True,
                             verbose_name='所学专业名称'
                             )

    courses = models.CharField(max_length=50, null=True, verbose_name='所修课程')
    # job_intention = models.CharField(max_length=50, null=True, verbose_name='求职意向')

    english_skill = models.IntegerField(choices=SKILL_CHOICES,
                                        null=True,
                                        blank=True,
                                        # related_name='english_skill_id',
                                        verbose_name='英语技能水平',
                                        )
    computer_skill = models.IntegerField(choices=SKILL_CHOICES,
                                         null=True,
                                         blank=True,
                                         # related_name='computer_skill_id',
                                         verbose_name='计算机技能水平'
                                         )

    expected_salary = models.IntegerField(null=True, blank=True, verbose_name='最低期望薪资')

    professional_skill = models.CharField(max_length=50, null=True, verbose_name='掌握专业技能')
    award = models.CharField(max_length=100, null=True, verbose_name='奖项、荣誉与证书')
    talent = models.CharField(max_length=8, null=True, verbose_name='特长/爱好')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')
    is_staring = models.BooleanField(verbose_name="是否星标", default=False, blank=True)

    def was_created_recently(self):
        return self.create_time >= timezone.now() - datetime.timedelta(days=7)

    def was_updated_recently(self):
        return self.update_time >= timezone.now() - datetime.timedelta(days=7)

    was_created_recently.boolean = True
    was_created_recently.short_description = '最近创建？'
    was_updated_recently.boolean = True
    was_updated_recently.short_description = '最近更新？'
    like_str = models.CharField(max_length=2500, verbose_name='全字段拼接', default='')

    def like_str_default(self):
        # 不做空值检测，因为外键本身会自动做空值校验，之所用，隔开是为了防止匹配时两字段合并匹配
        try:
            src = f'{self.industry.name},{self.major},{self.courses},{self.english_skill},{self.computer_skill}' \
                  f',{self.professional_skill},{self.award},{self.talent}'
            self.like_str = src
        except Exception:
            self.like_str = ''

    def display(self):
        return str(self.user_id)

    def image(self):
        return str(self.user_id.personalinfo.image)

    def age(self):
        return self.user_id.personalinfo.age()

    def education_level(self):
        return self.user_id.personalinfo.education

    def get_intention(self):
        try:
            cv_pc = CV_PositionClass.objects.get(cv_id__id=self.id)
            return str(cv_pc.position_class_id.name)
        except:
            return "未添加求职意向"

    # def image(self):
    #     try:
    #         return
    #     except:
    #         return None

    def __str__(self):
        return str(self.user_id) + '_cv.' + str(self.id)

    class Meta:
        verbose_name_plural = '简历表'


# from enterprise.models import PositionClass

# 每一份简历最多可以对应两个求职意向,求职意向来自岗位类别
class CV_PositionClass(models.Model):
    id = models.AutoField(primary_key=True)
    cv_id = models.ForeignKey(CV, on_delete=models.CASCADE, verbose_name='简历')
    position_class_id = models.ForeignKey("enterprise.PositionClass",
                                          limit_choices_to={'is_root': False},
                                          on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          verbose_name="求职意向（岗位）类别")

    class Meta:
        verbose_name_plural = '简历-求职意向表'


class CVFile(models.Model):
    id = models.OneToOneField(User, verbose_name='用户ID', on_delete=models.CASCADE, primary_key=True)
    upload_date = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to='static/files/',
                            null=True, blank=True, verbose_name='简历文件',
                            default=None)

    def get_owner(self):
        return self.id

    def get_creator(self):
        return self.id

    class Meta:
        verbose_name_plural = '简历上传表'
