# Generated by Django 2.1.5 on 2021-03-04 02:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise', '0006_auto_20210226_0936'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='enterpriseinfo',
            options={'verbose_name': '企业信息表', 'verbose_name_plural': '企业信息表'},
        ),
        migrations.AlterModelOptions(
            name='numberofstaff',
            options={'verbose_name': '员工规模表', 'verbose_name_plural': '员工规模表'},
        ),
        migrations.AddField(
            model_name='enterpriseinfo',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间'),
        ),
        migrations.AddField(
            model_name='enterpriseinfo',
            name='update_time',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='enterpriseinfo',
            name='staff_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.NumberOfStaff', verbose_name='企业规模（人）'),
        ),
        migrations.AlterField(
            model_name='position',
            name='extra_info',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='补充说明'),
        ),
        migrations.AlterField(
            model_name='position',
            name='job_content',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='工作内容'),
        ),
        migrations.AlterField(
            model_name='position',
            name='requirement',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='岗位基本要求'),
        ),
    ]
