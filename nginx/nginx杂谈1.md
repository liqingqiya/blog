关于nginx的请求处理过程一直有一点不明白, 那就是:

在nginx处理request时候, 先解析处理请求头, 在解析处理首部行, 最后异步处理主体(根本就没有处理),
接着就生成了相应.于是我就在纠结,为什么nginx不会留时间来处理请求的主体-entry-body?

这是因为nginx实现的就是一个静态web服务器, 也就是GET请求, GET请求是没有主体的.自然就不需要处理.
nginx自身实现的是一个静态的服务器, 动态的内容, 还有别的功能是通过反向代理来均衡到upstream服务器上的.
这个是nginx的特色.

web服务器处理惯例之一:对所发送的内容要求严格一点, 对所接受的内容要求宽容一点.

nginx在核心文件中,ngx_string.c文件, 有这么一个转化: `(void *) -1`, 咋一看是转化为-1, 
其实我们调试之后知道, 这个是一个非常大的值, 已经溢出了, 值为:0xffffffffffffffff.可以认为是
无穷大.

va_list取不定参数的时候, 如果某个不定参数是字符串, 比如 'web', 那么va怎么取?

```
void test(int a, fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    
}
```

```
    p = va_arg(args, u_char *)
```

