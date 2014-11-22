nginx服务器缓存机制
======================================

nginx服务器在该方面提供了两个方面的方案：

+ 负载均衡

+ web缓存

缓存技术简述
------------------------

传统的观点认为，影响网络访问速度的因素主要有三点：

1. 网络带宽

2. 访问距离

3. 服务器的处理能力

随着网络的介入速度的提升，网络带宽不断的拓容，目前的网络环境已经得到了极大的改善，影响网络的访问速度的主要瓶颈
出现在服务器的承载能力和处理能力上。在我们实际使用web服务器的过程中，我们能够看到，很多的产品为了提高自身负载能
力提供了各式各样的方法，比如镜像服务器，使用缓存服务器，实施负载均衡等等。

相应速度是衡量web应用和服务性能的重要指标之一，尤其是在我们生成一些动态内容的时候。对于这个的优化方案，现在很多
主要是把不需要实时更新的动态页面输出结果转化成静态页面并进行缓存，当再次遇到请求的时候，按照静态页面访问，这样提高
动态网站的响应速度。

web缓存技术被认为是减轻服务器负载，降低网络拥塞，增强网络可拓展性的有效途径之一。
基本思想是利用客户访问的时间局部性原理，将客户访问过的内容建立一个副本，在一段时间内存放在本地，当数据下次被访问的
时候，不必连接到后端服务器，而是由本地保留的副本数据响应。

web缓存技术的优点是：

1. 减轻了后端服务器的负载

2. 减少了web服务器和后端服务器之间的网络流量

3. 减轻网络拥塞，减少数据传输延迟，降低客户访问延迟

4. 如果后端服务器故障，或网络故障造成后端服务器无法响应客户请求，客户端可以从web服务器中获取缓存内容副本，
增强数据的可用性，使得后端服务器的鲁棒性得到增强。

nginx实现web缓存的几种方案
---------------------------

#### 404错误驱动web缓存

当nginx服务器在处理客户端请求的时候，发现请求的资源数据不存在，会产生404错误，然后服务器通过捕捉该错误，进一步转向后端服务器请求
数据，最后将后端服务器的响应数据传回给客户端，同时在本地缓存。

从实现原理看，nginx服务器向后端服务器发起数据请求，并完成web缓存，主要是产生404错误驱动的。

```
...
location / {
root /myweb/server/;
error_page 404 = 200 /errpage$request_uri;
}

location /errpage/ {
...
internal;
alias /home/html;
proxy_pass http://backend/;
proxy_set_header Accept-Encoding "'';
proxy_store on;
proxy_store_access user:rw group:rw all:r;
proxy_temp_path /myweb/server/tmp;
}
```

配置将404错误响应重定向，然后使用location块来捕捉重定向请求，向后端服务器发起请求获取响应数据，然后将数据转发给客户端的同时
缓存到本地。


#### 资源不存在驱动web缓存

原理：通过location块的location if条件判断直接驱动nginx服务器与后端服务器的通信和web缓存，而后者是对资源不存在引发的404错误
进行捕捉，进而驱动nginx服务器和后端服务器的通信和web缓存。

#### Proxy Cache缓存机制

该机制使用md5算法将请求链接hash后生成的文件系统目录保存响应数据。

nginx服务器在启动后，会生成专门的进程对磁盘傻瓜你的缓存文件进行扫描，在内存中建立缓存索引，提高访问效率，并且还会生成专门的管理进程
对磁盘的缓存文件进行过期判定，更新等方面的管理。Proxy Cache缓存机制支持对任意链接响应数据的缓存，不仅限于200状态的数据。
但是Proxy Cache缓存机制的一个缺陷是没有自动清理磁盘上缓存源数据的功能，在使用过一段时间后要手动的清理。以免造成对服务器存储的压力。

```
    http{
        proxy_cache_path /myweb/server/proxycache levels=1:2 max_size=2m inactive=5m loader_sleep=1m keys_zone=MYPROXYCACHE:10m;
        proxy_temp_path /myweb/server/tmp;
        server {
            location / {
                proxy_pass http://www.myweb.name/;
                proxy_cache MYPROXYCACHE;
                proxy_cache_valid 200 302 1h;
                proxy_cache_valid 301 1d;
                proxy_cache_valid any 1m;
            }
        }
    }
```

Nginx 配置范例
--------------------------------

```
user nobody nobody;
worker_processes 2;
error_log /usr/local/webserver/nginx/logs/nginx_error.log crit;
pid /usr/local/webserver/nginx/nginx.pid;

events {
    use epoll;
    worker_connections 65535;
}

http {
    include mime.types;
    default_type application/octet-stream;
    charset utf-8;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 60;
    tcp_nodelay on;
    client_body_buffer_size 512k;
    proxy_connect_timeout 5;
    proxy_read_timeout 60;
    proxy_send_timeout 5;
    proxy_buffer_size 16k;
    proxy_buffers 4 64k;
    proxy_busy_buffers_size 128k;
    proxy_temp_file_write_size 128k;
    gzip on;
    gzip_min_length 1k;
    gzip_buffers 4 16k;
    gzip_http_version 1.1;
    gzip_comp_level 2;
    gzip_types text/plain application/x-javascript text/css application/xml;
    gzip_vary on;

    #设置web缓存区名称为cache_one,内存缓存空间大小为200mb, 1天清理一次缓存，硬盘缓存空间大小为30GB
    proxy_temp_path /data0/proxy_temp_dir;
    proxy_cache_path /data0/proxy_cache_dir levels=1:2 keys_zone=cache_one:200m
    inactive=1d max_size=30g;

    #后端服务器,用于负载均衡
    upstream backend {
        server 192.168.1.3:80 weight=1 max_fails=2 faile_timeout=30s;
        server 192.168.1.4:80 weight=1 max_fails=2 faile_timeout=30s;
        server 192.168.1.5:80 weight=1 max_fails=2 faile_timeout=30s;
    }

    #虚拟主机
    server{
        listen 80;
        server_name myweb;
        index index.html index.htm;
        root /data0/htdocs/www;

        location / {
            #如果后端的服务器返回502,304,执行超时错误，将请求转发到另一台服务器
            proxy_next_upstream http_502 http_504 error timeout invalid_header;
            proxy_cache cache_one;

            #针对不同的http状态码设置不同的缓存时间
            proxy_cache_valid 200 304 12h;
            
            #web缓存的key值以域名、uri、参数组成
            proxy_cache_key $host$uri$is_args$args;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $remote_addr;
            proxy_pass http://backend_server;
            expires 1d;
        }

        #配置缓存清除功能
        location ~ /purge(/.*){
            #设置只允许指定的IP或者IP段才可清楚URL缓存
            allow 127.0.0.1;
            allow 192.168.0.0/16;
            deny all;
            proxy_cache_purge cache_one $host$1$is_args$args;
        }

        #配置数据不缓存
        location ~ .*\.(php|jsp|cgi)?${
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $remote_addr;
            proxy_pass http://backend;
        }
    }
}
```
