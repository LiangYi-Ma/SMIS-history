# Generated by Django 3.2 on 2022-05-19 14:37

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # ('taggit', '0008_settingchinesetag_is_self_setting'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('cv', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnterpriseCooperation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('enterprise_id', models.IntegerField(blank=True, null=True)),
                ('join_date', models.DateField(auto_now_add=True, verbose_name='加入时间')),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='EnterpriseInfo',
            fields=[
                ('id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='auth.user')),
                ('name', models.CharField(max_length=18, verbose_name='企业名称')),
                ('address', models.CharField(max_length=50, verbose_name='公司地址')),
                ('site_url', models.URLField(blank=True, null=True, verbose_name='企业官网')),
                ('logo', models.ImageField(blank=True, default='static/img/default_img.jpg', null=True, upload_to='static/img/enterprise_logo/', verbose_name='企业logo')),
                ('nature', models.IntegerField(blank=True, choices=[(1, '国企'), (2, '民营'), (3, '合资'), (4, '外商独资'), (5, '股份制企业'), (6, '上市公司'), (7, '代表处'), (8, '国家机关'), (9, '事业单位'), (10, '银行'), (11, '医院'), (12, '学校/下级学院'), (13, '律师事务所'), (14, '社会团体'), (15, '港澳台公司'), (16, '其他')], null=True, verbose_name='企业性质')),
                ('financing_status', models.IntegerField(blank=True, choices=[(1, '未融资'), (2, '天使轮'), (3, 'A轮'), (4, 'B轮'), (5, 'C轮'), (6, 'D轮及以上'), (7, '已上市'), (8, '无融资计划')], null=True, verbose_name='上市/投融资状态')),
                ('establish_year', models.IntegerField(default=2000, verbose_name='企业成立年份')),
                ('introduction', models.TextField(default='暂无公司简介……', max_length=500, verbose_name='企业基本介绍')),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '企业信息表',
                'verbose_name_plural': '企业信息表',
            },
        ),
        migrations.CreateModel(
            name='JobHuntersCollection',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('enterprise_id', models.IntegerField(blank=True, null=True)),
                ('collector', models.IntegerField(blank=True, null=True, verbose_name='企业协作id')),
            ],
            options={
                'verbose_name_plural': '求职者收藏表',
            },
        ),
        migrations.CreateModel(
            name='NumberOfStaff',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('min_number', models.IntegerField(blank=True, null=True, verbose_name='当前规模下限(人)')),
                ('max_number', models.IntegerField(blank=True, null=True, verbose_name='当前规模上限(人)')),
            ],
            options={
                'verbose_name': '员工规模表',
                'verbose_name_plural': '员工规模表',
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fullname', models.CharField(blank=True, max_length=10, null=True, verbose_name='岗位扩展名称（别称，默认为岗位类别）')),
                ('job_content', models.CharField(blank=True, max_length=150, null=True, verbose_name='工作内容')),
                ('requirement', models.CharField(blank=True, max_length=150, null=True, verbose_name='岗位基本要求')),
                ('extra_info', models.CharField(blank=True, max_length=150, null=True, verbose_name='补充说明')),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')),
                ('enterprise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enterprise.enterpriseinfo', verbose_name='企业')),
            ],
            options={
                'verbose_name': '岗位信息表',
                'verbose_name_plural': '岗位信息表',
            },
        ),
        migrations.CreateModel(
            name='PositionsData',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('view', models.IntegerField(default=0)),
                ('join', models.IntegerField(default=0)),
                ('collect', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': '职位数据表',
            },
        ),
        migrations.CreateModel(
            name='TaggedWhatever',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.IntegerField(db_index=True, verbose_name='object ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enterprise_taggedwhatever_tagged_items', to='contenttypes.contenttype', verbose_name='content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enterprise_taggedwhatever_items', to='taggit.settingchinesetag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Recruitment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('number_of_employers', models.IntegerField(blank=True, null=True, verbose_name='招聘人数')),
                ('education', models.IntegerField(blank=True, choices=[(0, '无'), (1, '小学'), (2, '初中'), (3, '高中/中职/中专'), (4, '高职/高专'), (5, '本科/职业本科'), (6, '硕士研究生'), (7, '硕士博士生')], null=True, verbose_name='最低学历要求')),
                ('city', models.IntegerField(blank=True, choices=[(1, '上海'), (2, '江苏'), (3, '浙江'), (4, '安徽'), (5, '北京'), (6, '天津'), (7, '广东'), (8, '河北'), (9, '河南'), (10, '山东'), (11, '湖北'), (12, '湖南'), (13, '江西'), (14, '福建'), (15, '四川'), (16, '重庆'), (17, '广西'), (18, '山西'), (19, '辽宁'), (20, '吉林'), (21, '黑龙江'), (22, '贵州'), (23, '陕西'), (24, '云南'), (25, '内蒙古'), (26, '甘肃'), (27, '青海'), (28, '宁夏'), (29, '新疆'), (30, '海南'), (31, '西藏'), (32, '中国香港'), (33, '中国澳门'), (34, '中国台湾'), (35, '海外')], null=True, verbose_name='工作地点')),
                ('salary_min', models.IntegerField(verbose_name='最低入职工资')),
                ('salary_max', models.IntegerField(verbose_name='最高入职工资')),
                ('salary_unit', models.IntegerField(choices=[(0, '年'), (1, '月'), (2, '日')], default=1, verbose_name='待遇水平单位')),
                ('job_experience', models.IntegerField(choices=[(0, '无经验'), (1, '经验不限'), (2, '1年以下'), (3, '1-3年'), (4, '3-5年'), (5, '5-10年'), (6, '10年以上')], default=1, verbose_name='工作经验要求')),
                ('job_nature', models.IntegerField(choices=[(1, '全职'), (2, '兼职'), (3, '实习'), (4, '校园'), (0, '不限')], default=1, verbose_name='工作性质')),
                ('post_limit_time', models.DateField(null=True, verbose_name='发布截止时限')),
                ('is_closed', models.BooleanField(blank=True, default=False, null=True, verbose_name='是否已经撤销/过期')),
                ('enterprise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enterprise.enterpriseinfo', verbose_name='企业名字')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enterprise.position', verbose_name='岗位名称')),
            ],
            options={
                'verbose_name_plural': '招聘行为表',
            },
        ),
        migrations.CreateModel(
            name='PositionClass',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=10, verbose_name='岗位类别名称')),
                ('desc', models.CharField(blank=True, max_length=50, null=True, verbose_name='岗位类别描述')),
                ('is_root', models.BooleanField(default=False, verbose_name='是否是一级分类')),
                ('is_enable', models.BooleanField(default=True, verbose_name='是否启用')),
                ('parent', models.ForeignKey(blank=True, default=0, limit_choices_to={'is_root': True}, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='children', to='enterprise.positionclass', verbose_name='上级分类')),
            ],
            options={
                'verbose_name': '岗位类别表',
                'verbose_name_plural': '岗位类别表',
            },
        ),
        migrations.AddField(
            model_name='position',
            name='pst_class',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_root': False}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.positionclass', verbose_name='岗位类别'),
        ),
        migrations.CreateModel(
            name='Field',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=15, verbose_name='领域名称')),
                ('desc', models.CharField(blank=True, max_length=50, null=True, verbose_name='领域描述')),
                ('is_root', models.BooleanField(default=False, verbose_name='是否是一级分类')),
                ('is_enable', models.BooleanField(default=True, verbose_name='是否启用')),
                ('parent', models.ForeignKey(blank=True, default=0, limit_choices_to={'is_root': True}, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='children', to='enterprise.field', verbose_name='上级分类')),
            ],
            options={
                'verbose_name': '领域表',
                'verbose_name_plural': '领域表',
            },
        ),
        migrations.AddField(
            model_name='enterpriseinfo',
            name='field',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.field', verbose_name='业务领域'),
        ),
        migrations.AddField(
            model_name='enterpriseinfo',
            name='staff_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.numberofstaff', verbose_name='企业规模（人）'),
        ),
        migrations.AddField(
            model_name='enterpriseinfo',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='enterprise.TaggedWhatever', to='taggit.SettingChineseTag', verbose_name='Tags'),
        ),
        migrations.CreateModel(
            name='Applications',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间')),
                ('progress', models.IntegerField(blank=True, default=0, verbose_name='应聘进度')),
                ('cv', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cv.cv', verbose_name='所投简历')),
                ('recruitment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enterprise.recruitment', verbose_name='招聘信息')),
            ],
            options={
                'verbose_name_plural': '应聘行为表',
            },
        ),
    ]
