#!/usr/bin/env python
# -*- coding:utf-8 -*-


from django.shortcuts import render_to_response, redirect

from models import MyShow

def show_page(request):
    """
    展示
    """
    object_list = MyShow.objects.all()
    template_name = "my_show.html"
    return render_to_response(
        template_name,{
        "object_list":object_list
        }
    )

def homepage(request):
    """
    主页
    """
    return redirect("/blog/list")