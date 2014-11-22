nginx有一个启动模式-单进程启动模式，这个模式主要是为了我们的调试使用
========================

因为单进程模式下，当有事件发生的时候，我们和容易跟踪。

假设现在我们已经做好了nginx的初始化工作，处于运行状态，也就是监听事件的状态。

那么nginx就会阻塞在 `src/event/modules/ngx_epoll_module.c:581`的`events = epoll_wait(ep, event_list, (int) nevents, timer)`上，这个是我们的linux系统上

一个高效的i/o复用模型，也叫做事件驱动模型。

发出一个http的geti请求总共会有三次的事件发生：

第一次
------------------------------

假设现在我们使用wget对监听端口发起一个请求，那么nginx程序就会从这一行执行下去，也就是由事件驱动了。

有个疑问？这个时候是什么事件，答案是：监听套接字的读事件（因为这个时候监听套接字收到了一个来之于客户端的请求，导致我们的监听套接字可读-也就是发生了可读事件），

这个时候events将赋值为1（如果只有一个监听套接字，并且只有一个客户端发来连接请求）

接下来我们轮询发生事件就行了：

```
617│     for (i = 0; i < events; i++) { /**/
618│         c = event_list[i].data.ptr; /*connection*/
619
```	

这里看循环就知道，比select和poll的模型高效好多，因为这里只要轮询我们发生了事件的文件描述符就行了。

下面做一些初始化，然后到了 691 行，调用事件的回调函数，进入`ngx_event_accept()`,这个函数定义在`src/event/ngx_event_accept.c`文件中。

```
64│             s = accept4(lc->fd, (struct sockaddr *) sa, &socklen,
65│                         SOCK_NONBLOCK); 
```

这里我们创建了与客户端通信的套接字.然后就是一些初始化，设置的工作了。

在这里我们的设置包括把这个新建的套接字-连接的可读，可写事件加入到epoll模型中。

这样我们的监听套接字的文件描述符的可读时间就算处理完毕了。

第二次
------------------------------

然后进行我们的第二次处理：

从epoll_wait()开始，这个时候，会返回两个发生的事件，这两个事件对应我们先前创建的套接字对应的可读，可写事件。

可读事件稍微提一下，可读时间的回调函数也会进入，ngx_event_accept()函数，只不过这里就没有创建套接字。

可写事件就不一样了，这里回调函数进入的是 

```
#0  ngx_http_wait_request_handler (rev=0x21cc260) at src/http/ngx_http_request.c:384
#1  0x0000000000434152 in ngx_epoll_process_events (cycle=0x21aaef0, timer=60000, flags=1) at src/event/modules/ngx_epoll_module.c:691
#2  0x0000000000427256 in ngx_process_events_and_timers (cycle=0x21aaef0) at src/event/ngx_event.c:248
#3  0x00000000004313d2 in ngx_single_process_cycle (cycle=0x21aaef0) at src/os/unix/ngx_process_cycle.c:315
#4  0x0000000000403b2d in main (argc=1, argv=0x7ffff843eec8) at src/core/nginx.c:404
```

我们可以通过这个堆栈看到，进入了`src/http/ngx_http_request.c`的`ngx_http_wait_request_handler`函数了。

在这里：

```
492├>    c->data = ngx_http_create_request(c); 
```
492行创建了request结构，

然后在912行进入了处理链接，入口`ngx_http_process_request_line`：

```
#0  ngx_http_process_request_line (rev=0x21cc260) at src/http/ngx_http_request.c:912
#1  0x0000000000444aaf in ngx_http_wait_request_handler (rev=0x21cc260) at src/http/ngx_http_request.c:499
#2  0x0000000000434152 in ngx_epoll_process_events (cycle=0x21aaef0, timer=60000, flags=1) at src/event/modules/ngx_epoll_module.c:691
#3  0x0000000000427256 in ngx_process_events_and_timers (cycle=0x21aaef0) at src/event/ngx_event.c:248
#4  0x00000000004313d2 in ngx_single_process_cycle (cycle=0x21aaef0) at src/os/unix/ngx_process_cycle.c:315
#5  0x0000000000403b2d in main (argc=1, argv=0x7ffff843eec8) at src/core/nginx.c:404
```

这个函数开始将会引起一系列的处理函数-分阶段处理，然后经过一系列的过滤函数。

我们来看看调用堆栈：

```
#0  ngx_http_core_run_phases (r=0x21b5b40) at src/http/ngx_http_core_module.c:886
#1  0x00000000004397f4 in ngx_http_handler (r=0x21b5b40) at src/http/ngx_http_core_module.c:871
#2  0x0000000000447075 in ngx_http_process_request (r=0x21b5b40) at src/http/ngx_http_request.c:1902
#3  0x0000000000445d55 in ngx_http_process_request_headers (rev=0x21cc260) at src/http/ngx_http_request.c:1333
#4  0x00000000004452a3 in ngx_http_process_request_line (rev=0x21cc260) at src/http/ngx_http_request.c:1012
#5  0x0000000000444aaf in ngx_http_wait_request_handler (rev=0x21cc260) at src/http/ngx_http_request.c:499
#6  0x0000000000434152 in ngx_epoll_process_events (cycle=0x21aaef0, timer=60000, flags=1) at src/event/modules/ngx_epoll_module.c:691
#7  0x0000000000427256 in ngx_process_events_and_timers (cycle=0x21aaef0) at src/event/ngx_event.c:248
#8  0x00000000004313d2 in ngx_single_process_cycle (cycle=0x21aaef0) at src/os/unix/ngx_process_cycle.c:315
#9  0x0000000000403b2d in main (argc=1, argv=0x7ffff843eec8) at src/core/nginx.c:404
```

状态机处理最后是在`ngx_http_core_run_phases（）`函数中执行的。

执行代码如下：

```
 886├>    while (ph[r->phase_handler].checker) { /*M-hM-?~YM-i~G~LM-f~XM-/M-eM-.~^M-i~Y~EM-g~Z~DM-eM-$~DM-g~P~FM-i~SM->M-e~P~WM-oM-<~_M
 887│
 888│         rc = ph[r->phase_handler].checker(r, &ph[r->phase_handler]);
 889│ 
 890│         if (rc == NGX_OK) { /*M-eM-$~DM-g~P~FM-eM-.~LM-f~H~PM-oM-<~LM-hM-?~TM-e~[~^*/
 891│             return;
 892│         }
 893│     }

```

因为在nginx初始化的时候，是根据我们的模块顺序形成了一条处理链的，对应一系列状态机变化。

所以这里用了一个while循环，调用我们的handler函数.

最后结束：

```
#3  0x0000000000469af4 in ngx_http_index_handler (r=0x21b5b40) at src/http/modules/ngx_http_index_module.c:277
#4  0x000000000043a993 in ngx_http_core_content_phase (r=0x21b5b40, ph=0x21c8560) at src/http/ngx_http_core_module.c:1417
#5  0x0000000000439886 in ngx_http_core_run_phases (r=0x21b5b40) at src/http/ngx_http_core_module.c:888
#6  0x00000000004397f4 in ngx_http_handler (r=0x21b5b40) at src/http/ngx_http_core_module.c:871
#7  0x0000000000447075 in ngx_http_process_request (r=0x21b5b40) at src/http/ngx_http_request.c:1902
#8  0x0000000000445d55 in ngx_http_process_request_headers (rev=0x21cc260) at src/http/ngx_http_request.c:1333
#9  0x00000000004452a3 in ngx_http_process_request_line (rev=0x21cc260) at src/http/ngx_http_request.c:1012
#10 0x0000000000444aaf in ngx_http_wait_request_handler (rev=0x21cc260) at src/http/ngx_http_request.c:499
#11 0x0000000000434152 in ngx_epoll_process_events (cycle=0x21aaef0, timer=60000, flags=1) at src/event/modules/ngx_epoll_module.c:691
#12 0x0000000000427256 in ngx_process_events_and_timers (cycle=0x21aaef0) at src/event/ngx_event.c:248
#13 0x00000000004313d2 in ngx_single_process_cycle (cycle=0x21aaef0) at src/os/unix/ngx_process_cycle.c:315
#14 0x0000000000403b2d in main (argc=1, argv=0x7ffff843eec8) at src/core/nginx.c:404
```

第三次
------------------------------

最后还有一轮的处理，这个时候epoll_wait（）收到的还是与客户连接的套接字的一个可读事件，用于关闭连接。


