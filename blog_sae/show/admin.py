#!/usr/bin/env python
# -*- coding:utf-8 -*-


from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from models import MyShow

class MyShowAdmin(SummernoteModelAdmin):
    """
    展示管理
    """
    list_display = ('title', "create_time", "last_modified")

admin.site.register(MyShow, MyShowAdmin)