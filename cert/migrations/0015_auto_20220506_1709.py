# Generated by Django 3.2 on 2022-05-06 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cert', '0014_auto_20220428_1938'),
    ]

    operations = [
        migrations.CreateModel(
            name='accessToken',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='id')),
                ('access_token', models.CharField(blank=True, max_length=128, null=True, verbose_name='token')),
                ('token_expire_at', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='failedupdaterecords',
            name='is_updated',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='是否已补更新'),
        ),
    ]
