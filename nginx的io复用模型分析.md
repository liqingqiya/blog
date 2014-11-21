事件管理机制
===========

nginx是以事件驱动的，一般情况，nginx将阻塞在epoll_wait()这样的系统调用上。
nginx关注的时间有两类：I/O事件，定时器事件。

在linux平台上，有三种事件驱动模型：select, poll, epoll，其中epoll最为高效。

但是无论是哪一种的I/O复用模型，基本原理都是相同的：事件驱动模型库能够让应用程序可以对多个I/O端口进行监控
以判断其上的操作是否可以进行，达到复用的目的。

nginx的接口设计极度简化，通用的事件模型接口是在ngx_event_actions_t的成员。在nginx中，I/O多路复用模型就是被封装
在这个结构体中，包含的字段为回调函数。

```
文件名： ../nginx/src/event/ngx_event.h 
======================================================================
220 :   typedef struct {
221 :       ngx_int_t  (*add)(ngx_event_t *ev, ngx_int_t event, ngx_uint_t flags);      /*将某描述符的事件添加到事件驱动列表中*/
222 :       ngx_int_t  (*del)(ngx_event_t *ev, ngx_int_t event, ngx_uint_t flags);      /*将某描述符的事件从事件驱动列表中删除*/
223 :   
224 :       ngx_int_t  (*enable)(ngx_event_t *ev, ngx_int_t event, ngx_uint_t flags);   /*启动对某个事件的监控*/
225 :       ngx_int_t  (*disable)(ngx_event_t *ev, ngx_int_t event, ngx_uint_t flags);  /*禁止对某个事件的监控*/
226 :   
227 :       ngx_int_t  (*add_conn)(ngx_connection_t *c);                                    /*将指定的连接关联的描述符添加到多路io复用的监控里*/
228 :       ngx_int_t  (*del_conn)(ngx_connection_t *c, ngx_uint_t flags);                /*将指定的连接关联的描述符从多路复用的监控里删除*/
229 :   
230 :       ngx_int_t  (*process_changes)(ngx_cycle_t *cycle, ngx_uint_t nowait);
231 :       ngx_int_t  (*process_events)(ngx_cycle_t *cycle, ngx_msec_t timer,
232 :                      ngx_uint_t flags);                                                   /*阻塞等待事件发生,对发生的事件进行逐个处理*/
233 :   
234 :       ngx_int_t  (*init)(ngx_cycle_t *cycle, ngx_msec_t timer);                       /*初始化*/
235 :       void       (*done)(ngx_cycle_t *cycle);                                            /*释放资源*/
236 :   } ngx_event_actions_t;                                                                 /*I/O多路复用模型统一接口*/
```

事件的行为都封装在这个结构体中，接口极度的简化。然后在接口之后，为每一个模块都会实现自己的事件模型行为。

并且nginx为了简化使用,首先在`ngx_event.c`文件中定义了一个全局变量

'''
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
45 :   ngx_event_actions_t   ngx_event_actions;                    /*类型为ngx_event_actions_t的全局变量，所有的事件接口都在这里*/
'''

定义了几个宏:

```
文件名： ../nginx/src/event/ngx_event.h 
======================================================================
443 :   #define ngx_process_changes  ngx_event_actions.process_changes    /*定义宏，简化使用*/
444 :   #define ngx_process_events   ngx_event_actions.process_events     /*阻塞等待事件发生，对发生的事件逐个处理, 定义宏，简化使用*/
445 :   #define ngx_done_events      ngx_event_actions.done                 /*定义宏，简化使用*/
446 :   
447 :   #define ngx_add_event        ngx_event_actions.add                  /*添加事件*/
448 :   #define ngx_del_event        ngx_event_actions.del                  /*删除事件*/
449 :   #define ngx_add_conn         ngx_event_actions.add_conn
450 :   #define ngx_del_conn         ngx_event_actions.del_conn
451 :   
452 :   #define ngx_add_timer        ngx_event_add_timer                    /*定时器事件？？todo*/
453 :   #define ngx_del_timer        ngx_event_del_timer                    /*定时器事件？？todo*/
```

我们在什么时候赋值给全局变量`ngx_event_actions`, 时机是在各个事件模块的初始化的时候，拿我的电脑来讲，是debian 7.7 的操作系统。

那么使用的就是epoll模型库，初始化该全局变量的时机就在启动初始化的时候：

cgdb调试的结果：

```
(gdb) bt
#0  ngx_epoll_init (cycle=0x6e0f70, timer=0) at src/event/modules/ngx_epoll_module.c:299
#1  0x0000000000428701 in ngx_event_process_init (cycle=0x6e0f70) at src/event/ngx_event.c:642
#2  0x0000000000431ea5 in ngx_single_process_cycle (cycle=0x6e0f70) at src/os/unix/ngx_process_cycle.c:305
#3  0x000000000040389d in main (argc=3, argv=0x7fffffffe688) at src/core/nginx.c:404
```

我们来看看初始化：

```
文件名： ../nginx/src/event/modules/ngx_epoll_module.c 
======================================================================
294 :   static ngx_int_t
295 :   ngx_epoll_init(ngx_cycle_t *cycle, ngx_msec_t timer)
296 :   {
297 :       ngx_epoll_conf_t  *epcf;
298 :   
299 :       epcf = ngx_event_get_conf(cycle->conf_ctx, ngx_epoll_module);       /*获取配置*/
300 :   
301 :       if (ep == -1) {
302 :           ep = epoll_create(cycle->connection_n / 2);                       /*系统调用，创建epoll对象*/
303 :   
304 :           if (ep == -1) {
305 :               ngx_log_error(NGX_LOG_EMERG, cycle->log, ngx_errno,
306 :                             "epoll_create() failed");
307 :               return NGX_ERROR;
308 :           }
309 :   
310 :   #if (NGX_HAVE_FILE_AIO)
311 :   
312 :           ngx_epoll_aio_init(cycle, epcf);        /*异步？？todo默认编译不会被执行到*/
313 :   
314 :   #endif
315 :       }
316 :   
317 :       if (nevents < epcf->events) {
318 :           if (event_list) {
319 :               ngx_free(event_list);
320 :           }
321 :   
322 :           event_list = ngx_alloc(sizeof(struct epoll_event) * epcf->events,
323 :                                  cycle->log);                                         /*创建事件列表,epcf->events为512*/
324 :           if (event_list == NULL) {                                                  /*事件列表*/
325 :               return NGX_ERROR;
326 :           }
327 :       }
328 :   
329 :       nevents = epcf->events; 
330 :   
331 :       ngx_io = ngx_os_io;                                         /*todo*/
332 :   
333 :       ngx_event_actions = ngx_epoll_module_ctx.actions;       /*在特定的事件驱动模块里对全局变量ngx_event_actions进行赋值*/
334 :   
335 :   #if (NGX_HAVE_CLEAR_EVENT)
336 :       ngx_event_flags = NGX_USE_CLEAR_EVENT
337 :   #else
338 :       ngx_event_flags = NGX_USE_LEVEL_EVENT
339 :   #endif
340 :                         |NGX_USE_GREEDY_EVENT
341 :                         |NGX_USE_EPOLL_EVENT;
342 :   
343 :       return NGX_OK;
344 :   }
```

这样初始化之后，全局变量`ngx_event_actions`就指向了他的封装。调用`ngx_add_event()`函数对应执行的就是`ngx_epoll_add_event()`函数。

这样，nginx内对I/O多路复用模型的整体封装，前后就衔接起来。
