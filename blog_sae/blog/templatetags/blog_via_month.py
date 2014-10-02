#!/usr/bin/env python
# -*- coding:utf-8 -*-


from django import template
from blog_sae.blog.models import Blog

register = template.Library()

@register.filter
def generater_blog_number_by_month(value):
    """
    获取某个月的发表blog数目
    """
    month = value.month
    return Blog.objects.filter(create_time__month=month).count()
