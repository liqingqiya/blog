#!/usr/bin/env python
# -*- coding:utf-8 -*-

from models import Blog, Category
from django.contrib import admin


class BlogAdmin(admin.ModelAdmin):
    """
    博客后台管理
    """
    list_display = ('title',"hit", "create_time", "last_modified")
    list_filter = ('title', 'hit', "create_time", "last_modified")
    search_fields = ['title', "summary"]
    ordering = ["-last_modified"]


class CategoryAdmin(admin.ModelAdmin):
    """
    类别管理
    """
    # exclude = ('create_time', "last_modified")
    search_fields = ["name",]
    list_display = ("name", "create_time", "last_modified")
    list_filter = ("name", )


admin.site.register(Blog, BlogAdmin)
admin.site.register(Category, CategoryAdmin)