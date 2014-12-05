nginx具有非常强的定制性.很大的一个原因就是nginx自定义的配置文件.nginx的配置文件的结构
主体来说是灵活,可拓展的一种结构, 本质是通过key-value来定义的.

拿一个简单的配置文件来说:

```
master_process off;
daemon off;

events {
    worker_connections  1024;
}


http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;

    keepalive_timeout  65;

    server {
        listen       8000;
        server_name  localhost;

        location / {
            root   html;
            index  index.html index.htm;
        }

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}
```

我们是在`ngx_init_cycle()->ngx_conf_parse()`中解析了这个文件.具体怎么解析的算法可以看源码.
我们这里主要将配置的结构机制.
首先我们进入这个配置结构, 级别就是main, 也就是最高的级别.我们的配置结构是模块化的.
对于每一个模块, 如果它对于这个级别会有兴趣的配置, 那么就会在合适的位置创建它的配置结构.这个级别会为所有的模块预留一个
位置存储配置结构.如果有感兴趣的, 那么实现就行了.`cycle->conf_ctx`指向这个数组.这样对于一个在这个级别有配置的模块,
如果想要提取这个结构的数据, 那么就从这个数组中提取就行了.`cycle->conf_ctx[index]`

现在分析http的框架.因为对于默认的nginx,http是主要的服务.

http定义有自己的框架.但是也和前面的一样. 是根据模块来组织的.碰到了http{}配置的时候, 会创建一个`ngx_http_conf_ctx_t`结构,
然后如果在http{}配置块中又碰到了server{}, 那么也是创建一个`ngx_http_conf_ctx_t`, 如果在server{}配置块中碰到了
location{}, 那么也会创建一个`ngx_http_conf_ctx_t`.

我们在第一级别的http{}配置中, 也就是http的main级别. `ngx_http_conf_ctx_t`, 这个会指挥三个数组. 

- main_conf

- srv_conf

- loc_conf

直观的感觉, 当我们在main级别中, 只需要一个main_conf数组就行了. 这个数组所有模块在这个级别的配置结构. 这样不就行了吗?
nginx考虑到如果一个配置项能够出现在main, server, locaiton级别, 那么任何一个模块都有权利选择到底是要使用哪个配置结构.
所以也会创建`srv_conf`, `loc_conf`级别的配置结构来存储这里main级别的配置(因为main, server, location都可以).这里创建
起来, 以便以后用于合并(选择).

我们需要明白一点, http的框架是又`ngx_http_core_module`模块建立的. 所以作为http的第一个模块, 就能代表http的模块框架.

- `ngx_http_core_main_conf_t`代表一个http{}配置.

- `ngx_http_core_srv_conf_t`代表一个server{}配置块.

- `ngx_http_core_loc_conf_t`代表一个location{}配置块.

这三个结构都是第一个http模块创建的.放在`ngx_http_conf_ctx_t`三个数组的第一个位置.

然后每个模块都会在每个配置块中创建属于自己的配置结构.`ngx_http_conf_ctx_t` 的三个数组都是以模块的方式组织的.

现在解决了配置的存储问题. 现在想一下怎么解决那些配置结构的存储层次问题, 因为我们的配置项目都是有层次结构的. 
所以我们的配置结构也是要有层次结构的, 这样才是正确的.

这里基准点是`ngx_http_conf_ctx_t`结构的, 数组`main_conf`的第一个成员.这个成员就代表了我们的http{}配置块.

`ngx_http_core_main_conf_t`成员servers把http{}的所有的server{}关联起来了.对于每一个server{}结构, 都能找到所属的
`ngx_http_conf_ctx_t`, 这样就能找到该层次的每个模块的配置结构.根据`ngx_http_conf_ctx_t`的数组`srv_conf`就行.

同一个location{}是有一个队列组织起来的.那么location怎么和server{}关联起来?

假如现在有一个层次:`ngx_http_conf_ctx_t`, `srv_conf[0]`代表当前的server{},那么`loc_conf[0]`(也就是
`ngx_http_core_loc_conf_t`)的locations成员指向我们的一个双端队列. 这个队列就是该server{}下所有的location{}.

这样就把http{}, server{}, location{}的基准点联系了起来. 能够准确的找到层次, 然后根据模块找到该层次的模块配置结构. 

如果在http模块

