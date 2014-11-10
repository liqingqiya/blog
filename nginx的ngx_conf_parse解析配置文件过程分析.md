`ngx_conf_parse()`
=============================

`ngx_conf_parse()`在`ngx_init_cycle（）`中被调用，用于解析我们的配置文件`nginx.conf`

由于`nginx.conf`是Igor Sysoev自己定义的一种格式，key-value格式的配置，具有很好的拓展性。

所以nginx程序里有很大的一部分代码是用来解析这个文件的，如果就是 `ngx_conf_parse()`, 通过这个解析函数
将我们nginx.conf里配置的值，存到我们的全局变量里。

1. 进入main级别的解析

2. 进入http{}， event{}， mail{}配置块的解析
