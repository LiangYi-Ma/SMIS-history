# Generated by Django 3.2 on 2022-05-25 14:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserClass',
            fields=[
                ('user_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='auth.user')),
                ('user_class', models.IntegerField(choices=[(0, '所有人'), (1, '求职者'), (2, '求职者与学员'), (3, '企业HR（管理）'), (4, '企业HR（协作）'), (1001, '系统超级管理员'), (1002, '系统运营管理员'), (1003, '系统组织管理员'), (2001, '学校超级管理员'), (2002, '学校管理员'), (3001, '社会超级管理员'), (3002, '社会管理员'), (4001, '企业超级管理员'), (4002, '企业管理员')], default=0)),
            ],
        ),
    ]