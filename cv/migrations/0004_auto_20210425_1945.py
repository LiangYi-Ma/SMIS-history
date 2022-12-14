# Generated by Django 2.1.5 on 2021-04-25 11:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cv', '0003_auto_20210421_1746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cv',
            name='industry',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_root': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.Field', verbose_name='目标行业领域'),
        ),
        migrations.AlterField(
            model_name='cv_positionclass',
            name='position_class_id',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_root': False}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enterprise.PositionClass', verbose_name='求职意向（岗位）类别'),
        ),
    ]
