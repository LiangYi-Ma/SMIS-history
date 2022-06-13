# Generated by Django 3.2 on 2022-05-16 11:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cert', '0015_auto_20220506_1709'),
    ]

    operations = [
        migrations.CreateModel(
            name='PracticeProcessData',
            fields=[
                ('practice', models.AutoField(primary_key=True, serialize=False)),
                ('process_data', models.CharField(max_length=128)),
                ('upload_time', models.DateTimeField(auto_now=True)),
                ('class_student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cert.classstudentcon')),
            ],
        ),
    ]
