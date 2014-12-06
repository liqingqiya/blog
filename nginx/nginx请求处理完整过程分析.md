nginx的处理
============================

nginx是基于事件驱动模型(也就是i/o复用模型), 当有可读/写事件发生, 那么就创建请求, 并处理.
我们现在看一下源码分析.我们从事件驱动模型开始说起.

首先, 假设我们的nginx已经做好了初始化工作, 正在正常运行, 那么就是在工作进程中等待事件发生了.
假设现在我们处在一个调试的状态, 也就是说, 只有一个single master进程. 那么就是在`ngx_single_process_cycle()`, 
这个是我们的工作核心. 因为是在调试状态, 那么主进程和工作进程都是同一个. 那我们的工作进程又是怎么使用事件驱动模型来
监听我们的事件发生呢? 
这是通过`ngx_process_events_and_timers()`函数. 这个接口是nginx定义的一个简单的,统一的事件接口.
定义在`src/event/ngx_event.c`我们使用的事件驱动模型就是通过这个简单的接口来调用的. 优秀的框架设计原则就是接口尽量的简化.
这个函数是一个优秀的入口, 使用我们事件驱动模型的入口. 那么它实际调用的是epoll模型库, 怎么调用?
这个是通过一个接口

`(void) ngx_process_events(cycle, timer, flags);`

这个接口也是定义在这个文件中的, 但是在前面初始化赋值的时候, 已经赋值了相应的,具体的事件驱动模型函数.
也就是`ngx_epoll_process_events()`这个是linux平台下的高效事件驱动模型库. 在之前就被赋值给了通用接口:`ngx_process_events()`,
这样就能在保证可移植性的同时, 屏蔽具体的平台的事件驱动.

所以说, 实际的事件模型的使用是在`ngx_epoll_process_events()`, 我们看一下源码.
在这个函数, 首先会有一个进程阻塞点 `epoll_wait()`, 这里等待我们的事件发生, 比如监听套接字的可读事件, 套接字的可读,可写事件.
当有事件发生的时候, 就会从阻塞中退出来, 该nginx获得程序控制权.

现在拿一个真是的例子来讲:现在wget作为客户端发出一个请求.使得监听套接字可读. 拥有监听套接字的进程从阻塞中退出.
这个时候, 到达`ngx_epoll_process_events()`的可读事件处理, 调用可读事件回调函数:`rev->handler(rev);`. 现在监听套接字可读时间的
回调函数是创建套接字. 分配一个连接, 一个可读, 一个可写事件, 并且加入到事件监听机制中进行监听.这就算处理完成了.

我们具体看一下这个可读事件的回调函数:`ngx_event_accept()`, 这个函数定义在:`src/event/ngx_event_accept.c:35`

```
#if (NGX_HAVE_ACCEPT4)
        if (use_accept4) {
            s = accept4(lc->fd, (struct sockaddr *) sa, &socklen,
                        SOCK_NONBLOCK);  /*请求连接，创建连接套接字*/
        } else {
            s = accept(lc->fd, (struct sockaddr *) sa, &socklen); /*请求连接，创建连接套接字*/
        }
```

这个函数创建使用`accept4()`调用创建了与客户端通信的套接字.网络编程最基本的通信,就是通过套接字来进行通信的.nginx也不例外.

然后我们要分配连接了,还有对应的一个可读,可写事件.


```
        ngx_accept_disabled = ngx_cycle->connection_n / 8
                              - ngx_cycle->free_connection_n;  /*用于判断当前进程是否过载的一个量*/

        c = ngx_get_connection(s, ev->log);
```

先计算是否过载, 然后从连接池拿出一个空闲连接绑定到这个套接字.当然这个连接结构是已经对应了一个可读和一个可写事件的.之后就是一些设置性的工作了.
这里要把新的套接字加入到事件监听机制中. 在什么时机加入的?
我们拿到连接结构之后, 肯定要初始化的. 也就是`ngx_http_init_connection()` , 在这个结构中, 调用了`ngx_handle_read_event()`, 这个
函数就是负责将我们的可读事件结构事件监听机制中. 有就是将刚刚创建的与客户端通信的套接字加入到监听机制. 监听它的可读,可写事件.


现在回到`epoll_wait()`, 刚刚加入到监听机制中的套接字是肯定可读的,因为wget发出的http数据包. 这个时候直接能够从阻塞中退出(或者可以说是不阻塞)
进入到可读的回调函数:`ngx_http_wait_request_handler()`. 这个才是重戏.在这个函数, 我们将处理客户来的请求, 并构造响应,并发出响应.
我们会从套接字中读取数据:`n = c->recv(c, b->last, size);`, 然后创建请求结构:`c->data = ngx_http_create_request(c);`, 这样就开始我们的
请求处理:`ngx_http_process_request_line(rev);`

处理的过程是这样的:先处理请求行, 在处理请求首部行, 在异步读取包体(GET请求是没有包体的), 然后正式的处理,这个正式的处理当然是按照nginx的状态机分阶段
处理的. 最后将request通过响应过滤, 发出到客户端就行了.

具体的函数调用如下:

```
ngx_http_process_request (r=0x6ebbc0) at src/http/ngx_http_request.c:1902
ngx_http_process_request_headers (rev=0x706370) at src/http/ngx_http_request.c:1333
ngx_http_process_request_line (rev=0x706370) at src/http/ngx_http_request.c:1012
ngx_http_wait_request_handler (rev=0x706370) at src/http/ngx_http_request.c:499
ngx_epoll_process_events (cycle=0x6e0f70, timer=60000, flags=1) at src/event/modules/ngx_epoll_module.c:691
ngx_process_events_and_timers (cycle=0x6e0f70) at src/event/ngx_event.c:248
ngx_single_process_cycle (cycle=0x6e0f70) at src/os/unix/ngx_process_cycle.c:315
```

这个是我们的调用堆栈, 我们可以看到`ngx_http_process_request_line()->ngx_http_process_request_headers()->ngx_http_process_request()`, 
从函数名称我们也很容易看出来这几个函数的作用.其中在`ngx_http_process_request()`会调用`ngx_http_handler()`进行处理.然后`ngx_http_handler()`
会调用`ngx_http_core_run_phases()`函数进行处理.这个函数实现的是nginx特色的状态机分阶段处理请求的方式.每一个阶段都关注自己的一个小方面, 就跟管道一样.
这样是模块构造起来更加的简单了.最后内容生成阶段`ngx_http_core_content_phase()`会把请求输入到out filter, 进行过滤. 
过滤之后, 会把构造好的响应发送给客户.到这个阶段是已经完成了的.

但是有些时候, 还可能会有一个阶段, 就是关闭连接. 如果要关闭连接, 这个时候也会产生一个可读事件. 我们处理就是将连接关闭, 回收一个connection结构.

当然, 一般我们的http协议是1.1的协议, 默认是开启长连接的. 所以这个过程也可能没有. 那么发送玩响应就结束了.

(在这里发现这么一个事情, 如果是用chrome浏览器发送请求, 那么就会有三次1, 2, 1, 如果是wget发出, 那么就只有两次1,1)todo
