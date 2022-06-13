# Generated by Django 3.2 on 2022-02-08 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cert', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacherinfo',
            name='teaching_field',
            field=models.IntegerField(choices=[(0, '综合领域'), (1, 'PLC'), (2, '工业机器人'), (3, '机器视觉')], default=0, verbose_name='教师授课领域'),
        ),
    ]