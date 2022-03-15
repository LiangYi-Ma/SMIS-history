from django.contrib import admin
from .models import CV, Industry, CV_PositionClass

# Register your models here.
# from django.contrib import admin
#
# admin.site.site_header = '求职人员信息管理系统'  # 设置header
# admin.site.site_title = '求职人员信息管理系统'          # 设置title


class CVAdmin(admin.ModelAdmin):

    list_display = ['user_id', 'was_created_recently', 'was_updated_recently']
    search_fields = ['user_id', 'industry']
    list_filter = ['update_time', 'industry']
    date_hierarchy = 'create_time'
    save_as = True


class IndustryAdmin(admin.ModelAdmin):

    list_display = ('id', 'industry_name', 'industry_meaning')



admin.site.register(CV, CVAdmin)
# admin.site.register(Industry, IndustryAdmin)
admin.site.register(CV_PositionClass)
