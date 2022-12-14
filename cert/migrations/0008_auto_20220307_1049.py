# Generated by Django 3.2 on 2022-03-07 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cert', '0007_courseinfo_ads_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentinfo',
            name='xet_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='classcoursecertcon',
            name='cert_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cert.certificationinfo', verbose_name='证书'),
        ),
        migrations.AlterField(
            model_name='classcoursecertcon',
            name='course_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cert.courseinfo', verbose_name='课程'),
        ),
        migrations.AlterField(
            model_name='studentinfo',
            name='is_valid',
            field=models.IntegerField(blank=True, choices=[(0, '未认证'), (1, '已认证'), (2, '认证未通过'), (3, '审核中')], default=0, null=True, verbose_name='小鹅通账号认证'),
        ),
    ]
