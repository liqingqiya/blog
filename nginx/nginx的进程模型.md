nginx的进程模型架构也是非常优秀的
===============================

nginx的系统架构是事件驱动模型，全异步处理方式

进程主要有两个，一个是主进程，一个是工作进程，其中主进程监听的是信号，工作进程等待的是事件。

也就是说主进程的关注点是我们的进程信号。

工作进程的阻塞点是select(), epoll_wait()这样的I/O多路复用的系统函数调用上，等待数据的可读，可写事件。

nginx的进程是怎么安排的？

1. 主进程负责监听整个程序，比如重启，如果有子进程异常退出，那么就重启一个子进程。所有的工作主要是维护整个程序的正常运行，不负责处理客户端来的请求。

2. 工作进程负责处理客户端来的请求，等待可写，可读的事件发生。

下面我们来看整个流程是怎么走的。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
403 :       if (ngx_process == NGX_PROCESS_SINGLE) { /*看是否是单进程模式*/
404 :           ngx_single_process_cycle(cycle);  /*单进程循环模式*/
405 :   
406 :       } else {
407 :           ngx_master_process_cycle(cycle);  /*启动 work process*/
408 :       }
409 :   
410 :       return 0;
411 :   }
```

假设现在我的配置是4个处理器，配置了一个主进程，4个工作进程，一个工作进程挂载到一个cpu上。

第407行，就是在我们的主函数里启动我们的进程。

现在我们看一下 `ngx_master_process_cycle`:

进程方面，与操作系统强相关，nginx为了可移植性，为所有的操作系统定义了统一的接口：`ngx_master_process_cycle`，然后是为每一个操作系统单独实现我们的进程。

我的操作系统是debian，所以也就是linux：

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
83 :   ngx_master_process_cycle(ngx_cycle_t *cycle) /*主进程*/
84 :   {
85 :       char              *title;
```

然后下面就是一些初始化的工作了，比如信号集的设置， 进程标题.

在下面就是创建我们的子进程:

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
136 :       ngx_start_worker_processes(cycle, ccf->worker_processes,
137 :                                  NGX_PROCESS_RESPAWN); /*打开子进程，各自进入循环*/
```

我们看到这里的`ngx_start_work_process()`，这个函数里会创建我们的进程映像，各自进入自己的工作循环。

我们先继续在 `ngx_master_process_cycle` 函数中往下走，待会在回过头来分析 `ngx_start_worker_process`:

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
144 :       /*主进程所在的循环*/
145 :       for ( ;; ) {

169 :           sigsuspend(&set); /*进程挂起，等待信号*/

176 :           if (ngx_reap) { /*有子进程退出*/
		...	
		}
182 :   
183 :           if (!live && (ngx_terminate || ngx_quit)) { /*收到退出信号*/
184 :               ngx_master_process_exit(cycle);
185 :           }
186 :   
187 :           if (ngx_terminate) { /*收到终止信号*/
196 :   
207 :           }
208 :   
209 :           if (ngx_quit) { /*收到退出信号*/
224 :           }
225 :   
226 :           if (ngx_reconfigure) { /*重新加载配置*/
259 :           }
260 :   
261 :           if (ngx_restart) { /*重新启动*/
267 :           }
268 :   
269 :           if (ngx_reopen) { /*重新打开*/
275 :           }
276 :   
277 :           if (ngx_change_binary) { /*改变二进制文件*/
281 :           }
282 :   
283 :           if (ngx_noaccept) { /*todo*/
288 :           }
289 :       }
```

我们看到这里的主进程调用了 一个挂起函数 sigsuspend()来等待信号的发生，这里的信号主要有 子进程异常退出，退出，重载配置文件，重启，等等。

大部分情况，我们的主进程是挂起的。

这里的方式是 设置信号，挂起等待信号。这种方式比起在一个while循环中，不断询问是否发生事件要高效一些。

现在我们去看看 `ngx_start_worker_processes` ，这个是开启我们的工作进程的函数:

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
349 :   /*根据配置文件，启动子进程，子进程进入自己的事件循环*/
350 :   static void
351 :   ngx_start_worker_processes(ngx_cycle_t *cycle, ngx_int_t n, ngx_int_t type)
352 :   {
353 :       ngx_int_t      i;
354 :       ngx_channel_t  ch;
355 :   
356 :       ngx_log_error(NGX_LOG_NOTICE, cycle->log, 0, "start worker processes");
357 :   
358 :       ngx_memzero(&ch, sizeof(ngx_channel_t));
359 :   
360 :       ch.command = NGX_CMD_OPEN_CHANNEL;
361 :   
362 :       for (i = 0; i < n; i++) {
363 :   
364 :           ngx_spawn_process(cycle, ngx_worker_process_cycle,
365 :                             (void *) (intptr_t) i, "worker process", type); /*fork子进程，进入自己的工作循环*/
366 :   
367 :           ch.pid = ngx_processes[ngx_process_slot].pid;
368 :           ch.slot = ngx_process_slot;
369 :           ch.fd = ngx_processes[ngx_process_slot].channel[0];
370 :   
371 :           ngx_pass_open_channel(cycle, &ch);
372 :       }
373 :   }
```

这里有一个for循环，我们利用`ngx_spawn_process`依次fork出我们的子进程:

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process.c 
======================================================================
86 :   ngx_pid_t
87 :   ngx_spawn_process(ngx_cycle_t *cycle, ngx_spawn_proc_pt proc, void *data,
88 :       char *name, ngx_int_t respawn) /*进程的初始化*/
89 :   {
```

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process.c 
======================================================================
186 :       pid = fork(); /*创建新的进程映像*/
187 :   
188 :       switch (pid) {
189 :   
190 :       case -1: /*创建失败*/
191 :           ngx_log_error(NGX_LOG_ALERT, cycle->log, ngx_errno,
192 :                         "fork() failed while spawning \"%s\"", name);
193 :           ngx_close_channel(ngx_processes[s].channel, cycle->log);
194 :           return NGX_INVALID_PID;
195 :   
196 :       case 0: /*子进程*/
197 :           ngx_pid = ngx_getpid();
198 :           proc(cycle, data); /*子进程进入自己的事件循环*/
199 :           break;
200 :   
201 :       default: /*父进程*/
202 :           break;
203 :       }
```

这里是一个非常经典的多进程的一段代码。在我们的第198行，这里进入的是子进程循环，那么proc是什么函数，注意到上面我们传的函数参数，就会知道：

proc是`ngx_worker_process_cycle()`:

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
729 :   /*work process 工作进程主体函数*/
730 :   static void
731 :   ngx_worker_process_cycle(ngx_cycle_t *cycle, void *data)    
732 :   {
733 :       ngx_int_t worker = (intptr_t) data; /*进程编号*/
734 :   
735 :       ngx_uint_t         i;
736 :       ngx_connection_t  *c;
737 :   
738 :       ngx_process = NGX_PROCESS_WORKER; /*工作进程标志*/
739 :   
740 :       ngx_worker_process_init(cycle, worker); /*process init 初始化*/
741 :   
742 :       ngx_setproctitle("worker process");     /*设置进程标题*/
743 :   /*是否开启线程*/
744 :   #if (NGX_THREADS)
	...
788 :   #endif
789 :   
790 :       for ( ;; ) {
791 :   
792 :           if (ngx_exiting) { /*退出信号*/
		....
803 :                   }
804 :               }
805 :   
		....
816 :           ngx_process_events_and_timers(cycle); /*阻塞等待事件发生*/
817 :   
818 :           if (ngx_terminate) { /*终止信号*/
		...
822 :           }
823 :   
824 :           if (ngx_quit) { /*终止信号*/
		....
834 :           }
835 :   
836 :           if (ngx_reopen) { /*重新打开信号*/
		....
840 :           }
841 :       }
842 :   }
```

这里进入的是工作进程自己的循环，有一个永久的for循环是为了处理发生的事件，第816行，阻塞等待事件的发生。可读/可写事件.
