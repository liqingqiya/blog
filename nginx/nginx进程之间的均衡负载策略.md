在我们配置了多进程的时候，工作进程会有多个，各个工作进程之间相互独立的接收客户端请求，处理，响应，所以就可能会出现
负载不均衡的现象。这个时候我们也需要解决进程之间的负载均衡问题。

事件源头来之于监听套接字，一旦某个工作进程独自拥有的某一个监听套接口，那么所有来自该监听套接口的请求都被该工作进程处理。
如果是多个进程共同拥有某个监听套接口，那么一旦出现请求，就会出现争抢，最后只有一个进程会抢占到这个请求，其他的将做的是
无用功，这种现象称做为惊群现象。

nginx在自身层面解决了惊群现象。

在nginx中，有一个全局变量，这个变量是nginx进程之间负载均衡措施的根本所在。

```
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
54 :   ngx_uint_t            ngx_use_accept_mutex;                  /*负载均衡锁*/
```

该变量的赋值语句在函数 `ngx_event_process_init()`， 也就是每个工作进程开始时候的初始化函数， 前后调用关系：

`ngx_worker_process_cycle() -> ngx_worker_process_init() -> ngx_event_process_init()`

在我的单进程设置下，cgdb调试是：

```
(gdb) bt
#0  ngx_event_process_init (cycle=0x6e0f70) at src/event/ngx_event.c:597
#1  0x0000000000431ea5 in ngx_single_process_cycle (cycle=0x6e0f70) at src/os/unix/ngx_process_cycle.c:305
#2  0x000000000040389d in main (argc=3, argv=0x7fffffffe688) at src/core/nginx.c:404
```

在`ngx_event_process_init()`中，代码：

```
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
600 :       if (ccf->master && ccf->worker_processes > 1 && ecf->accept_mutex) { /*多进程/用户配置开启*/
601 :           ngx_use_accept_mutex = 1;
602 :           ngx_accept_mutex_held = 0;
603 :           ngx_accept_mutex_delay = ecf->accept_mutex_delay;
604 :   
605 :       } else {
606 :           ngx_use_accept_mutex = 0;
607 :       }
```

从if的判定条件，我们看到：多进程，并且用户自主设置：ecf->accept_mutex字段。用户可以通过这个字段设置，来关闭进程均衡锁的功能。
原因是，如果在某些情况会消耗过多性能，我们就可以通过这个来关闭均衡锁。

一旦`ngx_use_accept_mutex`值为1, 也就开启了nginx进程均衡负载策略。在每个进程的初始化函数`ngx_event_process_init()`内，
所有监听套接字接口都不会被加入到其事件监听机制里。

```
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
840 :           rev->handler = ngx_event_accept; /*read事件的回调函数是ngx_event_accept()*/
841 :   
842 :           if (ngx_use_accept_mutex) {
843 :               continue;
844 :           }
845 :   
846 :           if (ngx_event_flags & NGX_USE_RTSIG_EVENT) {
847 :               if (ngx_add_conn(c) == NGX_ERROR) {
848 :                   return NGX_ERROR;
849 :               }
850 :   
851 :           } else {
852 :               if (ngx_add_event(rev, NGX_READ_EVENT, 0) == NGX_ERROR) { /*将read事件添加到事件监控机制中*/
853 :                   return NGX_ERROR;
854 :               }
855 :           }
```

真正将监听套接字加入到事件监控机制是在函数`ngx_process_events_and_timers()`里，工作进程的主要执行体是一个无限for循环，
而在该循环内最重要的函数调用就是`ngx_process_events_and_timers()`， 所以可以想象在该函数内动态添加或删除监听套接字是一种很
灵活的方式。

如果当前工作进程负载小，就将监听套接口加入到自身的监控机制里，从而带来新的用户请求，如果当前工作进程负载大，就将监听套接字从自身的事件监控机制中删除，
避免引入新的用户请求而带来更大的负载。

当然，这个加入和删除的动作是需要利用锁机制来做互斥与同步的，即避免监听套接口被同时加入到多个进程的事件监控机制里，有避免监听套接口在某一个时刻没有被任何一个进程监控。

```
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
224 :       if (ngx_use_accept_mutex) {             /*检查accept_mutex锁是否打开*/
225 :           if (ngx_accept_disabled > 0) {      /*通过检验ngx_accept_disabled是否大于0来判断当前进程是否过载*/
226 :               ngx_accept_disabled--;          /*当前进程连接数超过阀值*/
227 :   
228 :           } else {
229 :               if (ngx_trylock_accept_mutex(cycle) == NGX_ERROR) {  /*非阻塞尝试获取锁*/
230 :                   return;
231 :               }
232 :   
233 :               if (ngx_accept_mutex_held) {                            /*当前进程获取到了锁*/
234 :                   flags |= NGX_POST_EVENTS;                           /*标记当前到来的事件已经被该工作进程接收*/
235 :   
236 :               } else {
237 :                   if (timer == NGX_TIMER_INFINITE
238 :                       || timer > ngx_accept_mutex_delay)
239 :                   {
240 :                       timer = ngx_accept_mutex_delay;                 /*推迟一段时间，再去抢锁*/
241 :                   }
242 :               }
243 :           }
244 :       }
```

以上的代码，如果	`ngx_accept_disabled` 大于0, 那么就代表该工作进程负载达到了一个阀值。这次就不争抢锁，并把 `ngx_accept_disabled--`

争抢到锁的进程会把所有的监听套接字加入到自身的事件监听机制里。争抢失败就会把监听套接口从自身监控机制里删除。

实现在函数`ngx_trylock_accept_mutex()`:

```
文件名： ../nginx/src/event/ngx_event_accept.c 
======================================================================
369 :   ngx_int_t
370 :   ngx_trylock_accept_mutex(ngx_cycle_t *cycle)
371 :   {   /*进程间的同步锁，试图获取accept_mutex锁.ngx_shmtx_trylock是非阻塞的，拿到锁就返回1,失败则是0*/
372 :       if (ngx_shmtx_trylock(&ngx_accept_mutex)) {
373 :   
374 :           ngx_log_debug0(NGX_LOG_DEBUG_EVENT, cycle->log, 0,
375 :                          "accept mutex locked");
376 :   
377 :           if (ngx_accept_mutex_held
378 :               && ngx_accept_events == 0
379 :               && !(ngx_event_flags & NGX_USE_RTSIG_EVENT)) /*ngx_accept_mutex_held是标志位，为1时，表示当前进程已经拿到锁了*/
380 :           {
381 :               return NGX_OK;
382 :           }
383 :           /*将所有监听连接的读事件添加到当前的epoll等事件驱动模块中/添加到自身的进程的事件监听机制中*/
384 :           if (ngx_enable_accept_events(cycle) == NGX_ERROR) {
385 :               ngx_shmtx_unlock(&ngx_accept_mutex); /*添加失败，那么就必须释放ngx_accept_mutex锁*/
386 :               return NGX_ERROR;
387 :           }
388 :           /*经过ngx_enable_accept_events()调用，当前进程的事件驱动模块已经开始监听所有的端口，这个时候需要吧ngx_accept_mutex_held设置为1,方便其他模块了解它目前已经获取到了锁*/
389 :           ngx_accept_events = 0;
390 :           ngx_accept_mutex_held = 1;
391 :   
392 :           return NGX_OK;
393 :       }
394 :   
395 :       ngx_log_debug1(NGX_LOG_DEBUG_EVENT, cycle->log, 0,
396 :                      "accept mutex lock failed: %ui", ngx_accept_mutex_held);
397 :   
398 :       if (ngx_accept_mutex_held) {
399 :           if (ngx_disable_accept_events(cycle) == NGX_ERROR) {
400 :               return NGX_ERROR;
401 :           }
402 :   
403 :           ngx_accept_mutex_held = 0;
404 :       }
405 :   
406 :       return NGX_OK;
407 :   }
```

第384，399行分别是加入到自身监控机制和从自身监控机制中删除的实现。

争抢到锁，会给flags变量打个NGX_POST_EVENTS标记，这表示所有发生的事件都将延后处理。

架构设计必须遵循的一个约定就是：持锁者必须尽量缩短自身持锁的时间。

nginx的设计也是，大部分事件延迟到释放锁之后再去处理，把锁尽量释放，缩短自身持锁的时间能让其他进程尽可能的有机会获取到锁。

如果当前进程没有拥有锁，那么就把事件监控机制阻塞点的超时时间限制在一个比较短的范围内，超时更快，这样就更频繁的从阻塞中跳出来，也就有更多的机会去争抢到互斥锁。

没有拥有锁的进程接下来的操作和无负载均衡情况没有什么不同，拥有锁的进程对事件的处理，也就是前面提到的延后处理。

当一个事件发生时，一般处理会立即调用事件对应的回调函数，而延迟处理则会将该事件以链表的形式缓存起来。

```
文件名： ../nginx/src/event/modules/ngx_epoll_module.c 
======================================================================
684 :               if (flags & NGX_POST_EVENTS) { /*获取到锁的进程，处理事件延后，事件缓存*/
685 :                   queue = (ngx_event_t **) (rev->accept ?
686 :                                  &ngx_posted_accept_events : &ngx_posted_events);
687 :   
688 :                   ngx_locked_post_event(rev, queue);  /*事件缓存*/
689 :   
690 :               } else { /*调用事件回调函数*/
691 :                   rev->handler(rev); /*读事件的回调函数, handler->filter*/
692 :               }
```

如果有延后处理的标记，那么就加入到延迟处理队列。如果没有，那么就立即处理，立即执行回调函数.

`ngx_posted_accept_events`链表是新建连接事件，也就是监听套接口上发生的可读事件，ngx_posted_events是套接口的事件链表。

我们可以来看看 `ngx_process_event_and_timers()`:

```
文件名： ../nginx/src/event/ngx_event.c 
======================================================================
255 :       if (ngx_posted_accept_events) {                  /*存放事件的队列*/
256 :           ngx_event_process_posted(cycle, &ngx_posted_accept_events); /*处理缓存队列事件,此时还不能释放锁，因为当前进程还在处理监听套接字接口上的事件，还要读取上面的请求，这个队列事件处理完了之后，就能够释放了*/
257 :       }
258 :   
259 :       if (ngx_accept_mutex_held) {
260 :           ngx_shmtx_unlock(&ngx_accept_mutex);        /*释放accept_mutex互斥量*/
261 :       }
262 :   
263 :       if (delta) {
264 :           ngx_event_expire_timers();
265 :       }
266 :   
267 :       ngx_log_debug1(NGX_LOG_DEBUG_EVENT, cycle->log, 0,
268 :                      "posted events %p", ngx_posted_events);
269 :   
270 :       if (ngx_posted_events) {/*非网络请求事件,这些事件来自与事件驱动模块本身，都调用每个事件自己的处理方法进行处理*/
271 :           if (ngx_threaded) {
272 :               ngx_wakeup_worker_thread(cycle);
273 :   
274 :           } else {
275 :               ngx_event_process_posted(cycle, &ngx_posted_events);  /*处理缓存事件*/
276 :           }
277 :       }
```

这里我们先处理`ngx_posted_accept_events`，此时还不能释放锁，因为我们还在处理监听套接口上的事件，还要读取上面的请求数据，所以必须独占。
一旦这个链表处理完毕，那么就立即释放持有的锁。
对于连接套接口上的事件`ngx_posted_events`链表的处理可以在释放所之后进行。这样就算这些数据的处理比较费时间，我们也不会影响到别的进程，
因为早已经释放了锁。

如果在处理`ngx_posted_accept_events`事件队列的时候，监听套接口又有了新的请求会怎么样？
新的请求将被阻塞在监听套接口上，我们的监听套接口是以水平方式触发而被抓取出来的，所以等到下一次就会被某个获得锁的工作进程抓取出来。

在上面的代码，第260行，我们把锁释放了，但是并没有把监听套接口从当前进程的事件监听机制里删除，所以有可能导致在处理接下来的`ngx_posted_events`
缓存事件的过程中，互斥锁被另一个进程争抢到并且把所有的监听套接口加入到他的事件监听机制中。因此，严格的说，在同一个时刻，监听套接口可能被多个进程拥有，
但是监听套接口只能是被一个进程监控，因为进程在处理完`ngx_posted_events`缓存事件后去争用锁，发现锁被其他进程占有而争用失败，
会把所有监听套接口从自身的事件监控机制里删除，然后在进行事件监控。

这样能够保证，在任何的时刻，监听套接口只可能被一个进程监控，这样就意味着nginx根本不会受到惊群的影响，在自身的层面上解决了惊群问题。
