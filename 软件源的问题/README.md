软件源
=============

linux系统的软件源是非常重要的一个点.比如你如要要使用aptitude安装软件的时候,
有时候会遇到没有该软件的问题.举个例子,刚我安装python-dev都提示没有, 这个就
太明显了.

这个时候我们更新软件源:[镜像网站](http://mirrors.163.com/.help/debian.html)

更新`/etc/apt/sources.list`

然后`sudo aptitude update`
