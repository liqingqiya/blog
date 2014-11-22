`ngx_conf_parse()`
=============================

`ngx_conf_parse()`在`ngx_init_cycle（）`中被调用，用于解析我们的配置文件`nginx.conf`

由于`nginx.conf`是Igor Sysoev自己定义的一种格式，key-value格式的配置，具有很好的拓展性。

所以nginx程序里有很大的一部分代码是用来解析这个文件的，如果就是 `ngx_conf_parse()`, 通过这个解析函数
将我们nginx.conf里配置的值，存到我们的全局变量里。

我们就着一个简单的配置例子：

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

上面的是我们最基本的一个配置。现在我们来看看nginx是怎么解析的， 解析之后又是怎么存储的。

运行这个解析函数是在我们初始化的时候，也就是刚刚运行的时候。

我们看一下运行堆栈：

```
(gdb) bt
#0  ngx_conf_parse (cf=0x7fffffffe2a0, filename=0x6e00c0) at src/core/ngx_conf_file.c:115
#1  0x00000000004198c6 in ngx_init_cycle (old_cycle=0x7fffffffe3e0) at src/core/ngx_cycle.c:274
#2  0x00000000004038ec in main (argc=3, argv=0x7fffffffe6b8) at src/core/nginx.c:333
```

这个时候，就开始解析我们的配置文件了。

`ngx_conf_parse()`函数中定义了三个量，用来记录当前解析的状态：

```
 108│     enum {
 109│         parse_file = 0,                             /*解析配置文件*/
 110│         parse_block,                                /*解析复杂项*/
 111│         parse_param                                 /*解析命令行*/
 112│     } type;
```

这个时候,nginx会在稍后设置成parse_file状态。

然后打开nginx.conf文件.进行一些初始化的设置，接着就进入我们的重头戏-循环解析文件：

主要在两个函数中：

```
 170│     for ( ;; ) {
 171├>        rc = ngx_conf_read_token(cf);

 246│
 247├>        rc = ngx_conf_handler(cf, rc);  /**/

```

函数`ngx_conf_read_token`负责解析我们的配置文件语法，有五种返回值：

1. NGX_ERROR             there is error

2. NGX_OK                the token terminated by ";" was found

3. NGX_CONF_BLOCK_START  the token terminated by "{" was found

4. NGX_CONF_BLOCK_DONE   the "}" was found

5. NGX_CONF_FILE_DONE    the configuration file is done

并且`ngx_conf_read_token`负责的还有将配置读取读取到我们的缓冲内存区`cf->args`，

我们看gdb调试的情况：

```
(gdb) p *(ngx_str_t*)((*cf->args).elts)
$6 = {len = 14, data = 0x6e1130 "master_process"}
(gdb) p *(ngx_str_t*)((*cf->args).elts+sizeof(ngx_str_t))
$7 = {len = 3, data = 0x6e1140 "off"}
```

我们现在已经将一行配置读取到了缓存中，现在就该将这个配置的值存储到我们的全局变量里了。也就是运行我们的`ngx_conf_handler(cf, rc)`.

`ngx_conf_handler()`怎么做的？看看我们现在有什么？我们现在缓存区有读取到的配置字符串。

1. 找到哪些模块定义了我们缓存区中的配置项. 怎么找？ 遍历模块，遍历每个模块的指令数组，也就是说有两层循环。

2. 找到对应指令之后，局部变量found设置为1

3. 回调这个指令预先设置的回调函数

4. 在这个回调函数中，会存储我们这个配置到相应的全局变量。

只要模块定义了他需要这个配置的指令，那么就会为他创建一个结构体，也就是说以模块方式组织的。

上面讲的是，在main级别中的简单配置项目，也就是简单的key-value配置，如果解析到了一个配置块：比如http{}

那么 `ngx_conf_read_token`， 会在缓存区读入 `http {`， 返回1,

进入 `ngx_conf_handler()`, 通过回调函数进入：`ngx_http_block()`

在`ngx_http_block（）`中会间接的递归调用`ngx_conf_parse()`, 解析方式和前面一样。

生成的配置结构体也是按照模块来组织划分的，并且有一定的承接，嵌套关系。

