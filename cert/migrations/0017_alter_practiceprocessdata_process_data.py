# Generated by Django 3.2 on 2022-05-16 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cert', '0016_practiceprocessdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='practiceprocessdata',
            name='process_data',
            field=models.JSONField(null=True),
        ),
    ]
