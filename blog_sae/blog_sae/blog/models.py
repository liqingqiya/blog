#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from datetime import datetime

class Category(models.Model):
    """
    标签
    """
    name = models.CharField(max_length=255, verbose_name=u"类别名称")
    tag_color = models.CharField(max_length=255, default="black", verbose_name=u"标签颜色")
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u"创建时间")
    last_modified = models.DateTimeField(default=datetime.now(), verbose_name=u"最近修改时间")

    def __unicode__(self):
        return self.name

    def get_related_number(self):
        """
        获取相关blog的数目
        """
        return self.blog_category.count()

    class Meta:
        verbose_name = u"类别"
        verbose_name_plural = verbose_name


class Blog(models.Model):
    """
    博客
    """
    title = models.CharField(max_length=255, verbose_name=u"标题")
    summary = models.TextField(verbose_name=u"摘要")
    content = models.TextField(verbose_name=u"内容")
    hit = models.IntegerField(default=0, verbose_name=u"查看次数")
    category = models.ManyToManyField(Category, related_name=u"blog_category", verbose_name=u"类别")
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u"创建时间")
    last_modified = models.DateTimeField(default=datetime.now(), verbose_name=u"最近修改时间")

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u"博客"
        verbose_name_plural = verbose_name

