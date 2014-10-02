#!/usr/bin/env python
# -*- coding:utf-8 -*-


from django.views.generic import ListView, DetailView
from models import Blog, Category
from django.shortcuts import get_object_or_404, render_to_response
from django.db.models import F


class BlogList(ListView):
    """列表"""
    # model = Blog
    queryset = Blog.objects.all()
    paginate_by = 10
    template_name = 'blog_list.html'

    def get_queryset(self):
        """
        自定义列表内容
        """
        return Blog.objects.all().order_by("-last_modified")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BlogList, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the categorys
        context['category_list'] = Category.objects.all()
        #阅读排行前十名
        context["blog_list_rank_ten"] = Blog.objects.all().order_by("-hit")[:10]
        #按日期
        context["blog_month_list"] = Blog.objects.dates("create_time", "month")
        return context


class BlogDetail(DetailView):
    """详情"""
    model = Blog
    template_name = 'blog_detail.html'

    def get_object(self, queryset=None):
        """
        定制一下访问博客数据时候的行为
        =====================================
        get_object 用在detailview的视图上
        """
        id = self.kwargs.get("pk")
        obj = get_object_or_404(Blog, pk=id)
        # F("hit") 渲染到页面有bug, 但是后台能够正常更新.
        # obj.hit = F("hit") + 1
        obj.hit += 1
        obj.save()
        return obj


def BlogCategoryList(request, category_name):
    """
    根据文章类别列举出博客
    """
    #1 method 获取所有引用这个类别的博客
    category = Category.objects.get(name=category_name)
    object_list = category.blog_category.all().order_by("-create_time")  #category.blog_category返回的是一个管理器对象, 要使用all才能转化为queryset.
    #2 method 获取所有引用这个类别的博客
    # Blog.category.filter(name__contains=category_name)

    template_name = "blog_list.html"
    return render_to_response(template_name, {
        "object_list":object_list,
        "category_list":Category.objects.all(),
        "blog_list_rank_ten":Blog.objects.all().order_by("-hit")[:10],
        "blog_month_list": Blog.objects.dates("create_time", "month")
    })


def BlogMonthList(request, month):
    """
    根据月份时间列举出博客
    """
    object_list = Blog.objects.filter(create_time__month=month).order_by("-create_time")
    template_name = "blog_list.html"

    return render_to_response(template_name, {
        "object_list":object_list,
        "category_list":Category.objects.all(),
        "blog_list_rank_ten":Blog.objects.all().order_by("-hit")[:10],
        "blog_month_list": Blog.objects.dates("create_time", "month")
    })


def BlogLikeTitleList(request, title):
    """
    根据blog标题模糊查询
    """
    object_list = Blog.objects.filter(title__contains=title).order_by("-create_time")
    template_name = "blog_list.html"

    return render_to_response(template_name, {
        "object_list":object_list,
        "category_list":Category.objects.all(),
        "blog_list_rank_ten":Blog.objects.all().order_by("-hit")[:10],
        "blog_month_list": Blog.objects.dates("create_time", "month")
    })