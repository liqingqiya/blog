简介说明
================

- mysite_nginx.conf为nginx需要看到的配置文件,是和nginx联系的纽带.
  mysite_nginx.conf为了能够让nginx程序看到, 必须创建一个符号链接
  `sudo ln -s ~/path/to/your/mysite/mysite_nginx.conf /etc/nginx/sites-enabled/`
  这样就能够在sites-enabled目录下创建一个符号链接文件.

- mysite_uwsgi.ini是uwsgi程序启动的配置文件,是uwsgi的纽带.
  其实我们也能够使用命令行来启动, 但是这样写成一个配置文件会更方便, 更灵活.
