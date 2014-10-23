nginx启动的一个完整流程分析.
===================================

程序初始化过程包括了对nginx程序全局变量，主要数据结构，基础功能模块的初始化工作。

流程如下：
-------------

1. 解析输入参数，通过输入参数确定nginx服务器的具体行为。

2. 初始化时间和日志，备份输入参数，并初始化相关的全局变量。一些变量的值是依赖于nginx服务器所在的操作系统，比如内存页面大小，系统支持的最大文件打开数目。

3. 保存输入参数

4. 初始化网络套接字的相关结构

5. 初始化ngx_module_t数组

6. 读取并保存nginx配置参数

7. 初始化ngx_cycle_s结构体

8. 保存工作进程id到pid文件

我现在为了调试方便，是将nginx的工作方式设置到了单进程状态，配置文件如下：

```
文件名： /usr/local/nginx/conf/nginx.conf 
======================================================================
3 :   master_process off;
4 :   daemon off;
```

nginx是一个全异步网络服务器，一般电脑有几个cpu就配置几个工作进程，一个cpu负责一个挂载一个工作进程，每一个工作进程的方式是异步非阻塞的工作方式，这样cpu的利用率就能很高，

几乎能够跑满cpu。

现在我使用single模型是为了调试，在程序中，通过全局变量ngx_process的值来判断nginx服务器当前的工作模式，进而启动相应的模式进程。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
403 :       if (ngx_process == NGX_PROCESS_SINGLE) { /*看是否是单进程模式*/
404 :           ngx_single_process_cycle(cycle);  /*单进程循环模式*/
405 :   
406 :       } else {
407 :           ngx_master_process_cycle(cycle);  /*启动 work process*/
408 :       }
```

下面我们就用源码来走过一个完整的启动流程：
------------------------------------

首先，在main函数开始，我们主要调用了init类型的函数，完成初始化。比如下面，初始化nginx自定义的错误输出列表。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
211 :       if (ngx_strerror_init() != NGX_OK) {    /*初始化nginx自定义的错误输出列表*/
212 :           return 1;
213 :       }

```

下一步，解析我们的命令行参数：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
215 :       if (ngx_get_options(argc, argv) != NGX_OK) {    /*解析获取命令行参数*/
216 :           return 1;
217 :       }
```

我们的ngx_get_options（argc, argv）函数定义在/nginx-d0e39ec4f23f/src/core/nginx.c 的 line:667:

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
667 :   static ngx_int_t
668 :   ngx_get_options(int argc, char *const *argv)
669 :   {
...

673 :       for (i = 1; i < argc; i++) {
674 :   
675 :           p = (u_char *) argv[i]; /*为了兼容性，这里先要转化成 u_char*类型 */
676 :   
677 :           if (*p++ != '-') {  /*第一个参数要是 ‘-’ */
678 :               ngx_log_stderr(0, "invalid option: \"%s\"", argv[i]);
679 :               return NGX_ERROR;
680 :           }
681 :   
682 :           while (*p) {
683 :   
684 :               switch (*p++) {
685 :   
686 :               case '?':
687 :               case 'h':
688 :                   ngx_show_version = 1;
689 :                   ngx_show_help = 1;
690 :                   break;
691 :   
692 :               case 'v':
693 :                   ngx_show_version = 1;
694 :                   break;
695 :   
696 :               case 'V':
697 :                   ngx_show_version = 1;
698 :                   ngx_show_configure = 1;
699 :                   break;
700 :   
701 :               case 't':
702 :                   ngx_test_config = 1;
703 :                   break;
704 :   
705 :               case 'q':
706 :                   ngx_quiet_mode = 1;
707 :                   break;
708 :   
709 :               case 'p':
710 :                   if (*p) {
711 :                       ngx_prefix = p;
712 :                       goto next;
713 :                   }
714 :   
...

722 :   
723 :               case 'c':
724 :                   if (*p) {
725 :                       ngx_conf_file = p;
726 :                       goto next;
727 :                   }
...

736 :   
737 :               case 'g':
738 :                   if (*p) {
739 :                       ngx_conf_params = p;
740 :                       goto next;
741 :                   }
.....

751 :               case 's':
752 :                   if (*p) {
753 :                       ngx_signal = (char *) p;
......

```

通过上面的源代码我们知道，nginx通过循环结构对保存在argv变量中进行解析，针对不同的参数对相应的####全局变量####进行赋值。

在main（）下文中，程序根据这些全局变量确定nginx服务器要实现的具体功能。

这个函数主要对以下的文件域的全局变量进行设置：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
188 :   /*下面的几个文件域的静态变量存储解析命令行参数时候的值*/
189 :   static ngx_uint_t   ngx_show_help;      /**/
190 :   static ngx_uint_t   ngx_show_version;   /**/
191 :   static ngx_uint_t   ngx_show_configure; /**/
192 :   static u_char      *ngx_prefix;         /*服务器程序安装路径*/
193 :   static u_char      *ngx_conf_file;      /*我们的使用的配置文件路径*/
194 :   static u_char      *ngx_conf_params;    /**/
195 :   static char        *ngx_signal;          /**/
```
我们回到main（）函数，

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
219 :       if (ngx_show_version) {
220 :           ngx_write_stderr("nginx version: " NGINX_VER NGX_LINEFEED);
221 :   
222 :           if (ngx_show_help) {
223 :               ngx_write_stderr(
224 :                   "Usage: nginx [-?hvVtq] [-s signal] [-c filename] "
225 :                                "[-p prefix] [-g directives]" NGX_LINEFEED
226 :                                NGX_LINEFEED
227 :                   "Options:" NGX_LINEFEED
228 :                   "  -?,-h         : this help" NGX_LINEFEED
229 :                   "  -v            : show version and exit" NGX_LINEFEED
230 :                   "  -V            : show version and configure options then exit"
231 :                                      NGX_LINEFEED
232 :                   "  -t            : test configuration and exit" NGX_LINEFEED
233 :                   "  -q            : suppress non-error messages "
234 :                                      "during configuration testing" NGX_LINEFEED
235 :                   "  -s signal     : send signal to a master process: "
236 :                                      "stop, quit, reopen, reload" NGX_LINEFEED
237 :   #ifdef NGX_PREFIX
238 :                   "  -p prefix     : set prefix path (default: "
239 :                                      NGX_PREFIX ")" NGX_LINEFEED
240 :   #else
241 :                   "  -p prefix     : set prefix path (default: NONE)" NGX_LINEFEED
242 :   #endif
243 :                   "  -c filename   : set configuration file (default: "
244 :                                      NGX_CONF_PATH ")" NGX_LINEFEED
245 :                   "  -g directives : set global directives out of configuration "
246 :                                      "file" NGX_LINEFEED NGX_LINEFEED
247 :                   );
248 :           }
249 :   
250 :           if (ngx_show_configure) {
251 :               ngx_write_stderr(
252 :   #ifdef NGX_COMPILER
253 :                   "built by " NGX_COMPILER NGX_LINEFEED
254 :   #endif
255 :   #if (NGX_SSL)
256 :   #ifdef SSL_CTRL_SET_TLSEXT_HOSTNAME
257 :                   "TLS SNI support enabled" NGX_LINEFEED
258 :   #else
259 :                   "TLS SNI support disabled" NGX_LINEFEED
260 :   #endif
261 :   #endif
262 :                   "configure arguments:" NGX_CONFIGURE NGX_LINEFEED);
263 :           }
264 :   
265 :           if (!ngx_test_config) {
266 :               return 0;
267 :           }
268 :       }
```

上面的代码主要是根据我们在ngx_get_options（）函数里设置的ngx_show_version,ngx_show_configure这两个变量来打印相关信息。

第223行的ngx_write_stderr负责向标准输出端输出版本信息和帮助信息。

第251行的ngx_write_stderr负责向标准输出端输出nginx在配置时候的相关配置信息。

全局变量 ngx_test_config 的赋值决定是否对nginx配置文件进行语法检查。该变量定义在ngx_cycle.c中line：26。

紧接着下面的代码：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
272 :       ngx_time_init();      /*初始化时间*/
273 :   
274 :   #if (NGX_PCRE)            /*是否支持正则表达式*/
275 :       ngx_regex_init();     /*完成支持正则表达式的准备工作*/
276 :   #endif
277 :   
278 :       ngx_pid = ngx_getpid();   /*获取当前nginx进程的进程号, 这个是宏定义的系统调用*/
279 :   
280 :       log = ngx_log_init(ngx_prefix);   /*初始化日志*/
281 :       if (log == NULL) {
282 :           return 1;
283 :       }
```

1. 初始化时间模块

2. 初始化正则表达式，当然要看看是否编译了正则表达式的支持。默认编译的nginx一般都是支持的。

3. 获取当前nginx进程的进程号。

4. 初始化日志模块。

这里提一下ngx_getpid()这个函数，这个函数是nginx为了跨平台而封装的一个函数，因为不同的操作系统有这不同的系统调用。

比如当前我的操作系统是debian，那么这里使用的就是定义在nginx/os/unix/ngx_process.h文件中的一个宏定义。

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process.h 
======================================================================
56 :   #define ngx_getpid   getpid     /*系统调用，获取进程id号*/
```

nginx之所以如此流行，和他的跨平台的性质分不开，所以nginx一般会有自己的一套封装，主要是为了可移植。

继续在main（）函数往下面走：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
295 :       ngx_memzero(&init_cycle, sizeof(ngx_cycle_t));    /*给ngx_cycle_t结构体内存块赋零值，定义在ngx_string.h*/
296 :       init_cycle.log = log;       /*初始化cycle结构的log*/
297 :       ngx_cycle = &init_cycle;    
```

上面完成了的动作有：

1. 清零ngx_cycle_t的结构内存，初始化为0。

2. 初始化init_cycle.log，以后整个程序的日志都是使用这个句柄。

3. 赋值ngx_cycle。

这里的ngx_memzero是nginx对memset的一个封装：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_string.h 
======================================================================
86:   #define ngx_memzero(buf, n)       (void) memset(buf, 0, n)
```

main()函数继续：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
299 :       init_cycle.pool = ngx_create_pool(1024, log);     /*创建内存池，初始化cycle结构的pool*/
300 :       if (init_cycle.pool == NULL) {
301 :           return 1;
302 :       }
303 :   
304 :       if (ngx_save_argv(&init_cycle, argc, argv) != NGX_OK) { /*存储命令行参数到全局变量*/
305 :           return 1;
306 :       }
307 :   
308 :       if (ngx_process_options(&init_cycle) != NGX_OK) {     /*存储传入的参数到 init_cycle 结构的成员变量*/
309 :           return 1;
310 :       }
311 :   
312 :       if (ngx_os_init(log) != NGX_OK) {
313 :           return 1;
314 :       }
316 :       /*
```

上面的代码完成：

1. 创建一个内存池。

2. 保存传入的命令行参数到全局变量。

3. 保存传入的参数到init_cycle结构的相应成员变量里。

我们依个看看这几个函数：

首先ngx_save_argv()

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
790 :   static ngx_int_t
791 :   ngx_save_argv(ngx_cycle_t *cycle, int argc, char *const *argv)  /*存储命令行参数*/
792 :   {
793 :   #if (NGX_FREEBSD)
794 :   
795 :       ngx_os_argv = (char **) argv;
796 :       ngx_argc = argc;
797 :       ngx_argv = (char **) argv;
798 :   
799 :   #else
800 :       size_t     len;
801 :       ngx_int_t  i;
802 :   
803 :       ngx_os_argv = (char **) argv;
804 :       ngx_argc = argc;
805 :   
806 :       ngx_argv = ngx_alloc((argc + 1) * sizeof(char *), cycle->log);
807 :       if (ngx_argv == NULL) {
808 :           return NGX_ERROR;
809 :       }
810 :   
811 :       for (i = 0; i < argc; i++) {
812 :           len = ngx_strlen(argv[i]) + 1;
813 :   
814 :           ngx_argv[i] = ngx_alloc(len, cycle->log);
815 :           if (ngx_argv[i] == NULL) {
816 :               return NGX_ERROR;
817 :           }
818 :   
819 :           (void) ngx_cpystrn((u_char *) ngx_argv[i], (u_char *) argv[i], len);
820 :       }
821 :   
822 :       ngx_argv[i] = NULL;
823 :   
824 :   #endif
825 :   
826 :       ngx_os_environ = environ;
827 :   
828 :       return NGX_OK;
829 :   }
```

我linux操作系统的电脑是从800行开始编译的。这里主要是复制赋值了ngx_argv数组，和ngx_os_environ，这里的ngx_argv数组是一个与系统相关的变量，nginx进行了封装。

接下来看ngx_process_options(ngx_cycle_t *cycle)。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
832 :   static ngx_int_t
833 :   ngx_process_options(ngx_cycle_t *cycle)
834 :   {
835 :       u_char  *p;
836 :       size_t   len;
837 :   
838 :       if (ngx_prefix) {         //ngx_prefix存储服务器程序安装路径
839 :           len = ngx_strlen(ngx_prefix);
840 :           p = ngx_prefix;
841 :   
842 :           if (len && !ngx_path_separator(p[len - 1])) {
843 :               p = ngx_pnalloc(cycle->pool, len + 1);
844 :               if (p == NULL) {
845 :                   return NGX_ERROR;
846 :               }
847 :   
848 :               ngx_memcpy(p, ngx_prefix, len);
849 :               p[len++] = '/';
850 :           }
851 :   
852 :           cycle->conf_prefix.len = len;   //conf_prefix存放的是服务器配置文件的路径
853 :           cycle->conf_prefix.data = p;
854 :           cycle->prefix.len = len;
855 :           cycle->prefix.data = p;
856 :   
857 :       } else {
858 :   
859 :   #ifndef NGX_PREFIX
860 :   
861 :           p = ngx_pnalloc(cycle->pool, NGX_MAX_PATH);
862 :           if (p == NULL) {
863 :               return NGX_ERROR;
864 :           }
865 :   
866 :           if (ngx_getcwd(p, NGX_MAX_PATH) == 0) {
867 :               ngx_log_stderr(ngx_errno, "[emerg]: " ngx_getcwd_n " failed");
868 :               return NGX_ERROR;
869 :           }
870 :   
871 :           len = ngx_strlen(p);
872 :   
873 :           p[len++] = '/';
874 :   
875 :           cycle->conf_prefix.len = len;
876 :           cycle->conf_prefix.data = p;
877 :           cycle->prefix.len = len;
878 :           cycle->prefix.data = p;
879 :   
880 :   #else
881 :   
882 :   #ifdef NGX_CONF_PREFIX
883 :           ngx_str_set(&cycle->conf_prefix, NGX_CONF_PREFIX);
884 :   #else
885 :           ngx_str_set(&cycle->conf_prefix, NGX_PREFIX);
886 :   #endif
887 :           ngx_str_set(&cycle->prefix, NGX_PREFIX);
888 :   
889 :   #endif
890 :       }
891 :   
892 :       if (ngx_conf_file) {
893 :           cycle->conf_file.len = ngx_strlen(ngx_conf_file);   /*配置文件路径的字符串长度*/
894 :           cycle->conf_file.data = ngx_conf_file; /*配置文件路径的字符串*/
895 :   
896 :       } else {
897 :           ngx_str_set(&cycle->conf_file, NGX_CONF_PATH);
898 :       }
899 :   
900 :       if (ngx_conf_full_name(cycle, &cycle->conf_file, 0) != NGX_OK) {
901 :           return NGX_ERROR;
902 :       }
903 :   
904 :       for (p = cycle->conf_file.data + cycle->conf_file.len - 1;
905 :            p > cycle->conf_file.data;
906 :            p--)
907 :       {
908 :           if (ngx_path_separator(*p)) {
909 :               cycle->conf_prefix.len = p - ngx_cycle->conf_file.data + 1;
910 :               cycle->conf_prefix.data = ngx_cycle->conf_file.data;
911 :               break;
912 :           }
913 :       }
914 :   
915 :       if (ngx_conf_params) {
916 :           cycle->conf_param.len = ngx_strlen(ngx_conf_params);
917 :           cycle->conf_param.data = ngx_conf_params;
918 :       }
919 :   
920 :       if (ngx_test_config) {
921 :           cycle->log->log_level = NGX_LOG_INFO;
922 :       }
923 :   
924 :       return NGX_OK;
925 :   }
```

以上就是将ngx_process_options（）就将这些全局变量保存到cycle的结构成员中去。

ngx_os_init() 获取运行环境中的一些相关参数，因为nginx服务器的高效运行与运行环境具有密切的联系，也就是说和操作系统是强相关的。

在这个函数里，我们调用了ngx_os_specific_init（）来获得操作系统的内核，并设置到全局变量：

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_linux_init.c 
======================================================================
33 :   ngx_int_t
34 :   ngx_os_specific_init(ngx_log_t *log) /*linux平台上ngx_os_init真实调用的函数*/
35 :   {
36 :       struct utsname  u;
37 :   
38 :       if (uname(&u) == -1) { /*#include <sys/utsname.h>. 系统调用, 获取操作系统内核和其他信息*/
39 :           ngx_log_error(NGX_LOG_ALERT, log, ngx_errno, "uname() failed");
40 :           return NGX_ERROR;
41 :       }
42 :   
43 :       /*
44 :       调用uname（&u）之后，获得系统内核的相关信息
45 :       {
46 :           sysname = "Linux", '\000' <repeats 59 times>, 
47 :           nodename = "debian", '\000' <repeats 58 times>, 
48 :           release = "3.2.0-4-amd64", '\000'<repeats 51 times>, 
49 :           version = "#1 SMP Debian 3.2.57-3", '\000' <repeats 42 times>, 
50 :           machine = "x86_64", '\000' <repeats 58 times>, 
51 :           domainname = "(none)", '\000' <repeats 58 times>
52 :           }
53 :       */
```

这里我们通过uname（）系统调用来获取的。

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_posix_init.c 
======================================================================
32 :   ngx_int_t
33 :   ngx_os_init(ngx_log_t *log) /*获取系统相关的一些变量*/
34 :   {
43 :       ngx_init_setproctitle(log); /*设置进程名称*/
45 :       ngx_pagesize = getpagesize(); /*获取内存页大小*/
46 :       ngx_cacheline_size = NGX_CPU_CACHE_LINE; 
60 :       ngx_cpuinfo(); /*cpu的相关信息???todo*/
61 :       /*获得每个进程能够创建的各种系统资源的限制使用量*/
62 :       if (getrlimit(RLIMIT_NOFILE, &rlmt) == -1) { /*#include <sys/resource.h> getrlimit为系统调用*/
63 :           ngx_log_error(NGX_LOG_ALERT, log, errno,
64 :                         "getrlimit(RLIMIT_NOFILE) failed)");
65 :           return NGX_ERROR;
66 :       }
68 :       ngx_max_sockets = (ngx_int_t) rlmt.rlim_cur; /*最大套接字，也就是能够打开的文件数*/
70 :   #if (NGX_HAVE_INHERITED_NONBLOCK || NGX_HAVE_ACCEPT4)
71 :       ngx_inherited_nonblocking = 1; /*linux设置非阻塞标记*/
72 :   #else
73 :       ngx_inherited_nonblocking = 0;
74 :   #endif
76 :       srandom(ngx_time()); /*初始化随机种子*/
78 :       return NGX_OK;
79 :   }
```
以上主要获取和系统强相关的一些变量，比如内存页的大小，系统资源的限制使用量，并且进行了一些初始化的设置，比如设置进程名称标题，初始化随机种子。

main（）函数接下来是建立循环冗余检验表

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
316 :       /*
317 :        * ngx_crc32_table_init() requires ngx_cacheline_size set in ngx_os_init()
318 :        */
319 :   
320 :       if (ngx_crc32_table_init() != NGX_OK) {  /*建立循环冗余检验表*/
321 :           return 1;
322 :       }
```

由注释我们知道，这个函数初始化是建立在ngx_cacheline_size被赋值的情况下。

这里我们不用讨论这里建立循环冗余检验的算法，主要注意这里建表的思想，这是非常典型的空间换取时间效率的行为，由于如果我们在每一次运行的时候，都要计算出值的话，

就太慢了，而这些值是非常固定的，而且存储量不大，那么我们就可以考虑事先建好一张表，到需要计算值的时候，就直接查表就行了。这样就高效很多。

再往下面就要继承我们的套接字描述符了：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
324 :       if (ngx_add_inherited_sockets(&init_cycle) != NGX_OK) { /*继承socket描述符*/
325 :           return 1;
326 :       }
```

现在我们去ngx_add_inherited_sockets(&init_cycle)里看看：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
414 :   static ngx_int_t
415 :   ngx_add_inherited_sockets(ngx_cycle_t *cycle)
416 :   {
417 :       u_char           *p, *v, *inherited;
418 :       ngx_int_t         s;
419 :       ngx_listening_t  *ls;
420 :       /*第一次启动nginx的时候，NGINX_VAR为空，到此就结束函数，返回NGX_OK*/
421 :       inherited = (u_char *) getenv(NGINX_VAR);   /*设置nginx的环境变量*/
422 :   
423 :       if (inherited == NULL) {
424 :           return NGX_OK;
425 :       }
	.....
464 :   }
```

我们第一次启动nginx的时候，NGINX_VAR是没有设置的，所以inherited就自然是0了，到424行，就退出了。

继续main（），

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
328 :       ngx_max_module = 0;
329 :       for (i = 0; ngx_modules[i]; i++) {    /*遍历所有的模块，建立模块索引*/
330 :           ngx_modules[i]->index = ngx_max_module++;
331 :       }
```

这里我们遍历了所有的模块变量，我们的模块定义在obj/modules.c中。该代码中的for循环中描述了每一个ngx_module_t结构体中的index成员。

这里的index是我们模块全局的一个索引。ctx_index是我们同类模块的一个索引。模块类型有：core,http,mail,event.

下面我们就要进入比较重要的一步了，初始化一个ngx_cycle结构，这个结构代表了一个周期，也就是nginx的一个生命周期，所以是非常重要的一个结构，如果要重启，升级，nginx都会

创建一个新的nginx生命周期，也就是对应的创建一个新的ngx_cycle_t结构。

在接下俩的main（）函数里有下面代码：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
333 :       cycle = ngx_init_cycle(&init_cycle);  /*创建新的cycle结构*/
334 :       if (cycle == NULL) {
335 :           if (ngx_test_config) {
336 :               ngx_log_stderr(0, "configuration file %s test failed",
337 :                              init_cycle.conf_file.data);
338 :           }
339 :   
340 :           return 1;
341 :       }
```

ngx_init_cycle（&init_cycle）传入的参数是刚刚初始化过部分成员的ngx_cycle_t结构，在ngx_init_cycle函数里，我们将在新建立的内存池里

重新给ngx_cycle_t结构分配内存，用cycle变量来指向该内存区域，并且把刚才初始化了的成员转移到这个新的结构中。

现在我们一步步来看看，这个函数源码到底做了些什么？

首先，对时间的一些设置操作：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
58 :       ngx_timezone_update();  /*初始化时区*/
60 :       /* force localtime update with a new timezone */
62 :       tp = ngx_timeofday();  /*获取时间缓存的时间,tp指向类似于{sec = 1413887501, msec = 331, gmtoff = 480}*/
63 :       tp->sec = 0;
65 :       ngx_time_update();  /*更新缓存时间*/
```

上面的代码主要完成：

1. 初始化时区

2. 获取缓存时间

3. 更新缓存时间

nginx的时间管理也是很有特色的，这个以后单独分析nginx的源码原理。

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
70 :       pool = ngx_create_pool(NGX_CYCLE_POOL_SIZE, log);  /*建立了新的内存池,该内存池将为nginx服务器程序运行的整个生命周期提供内存分配和管理*/
71 :       if (pool == NULL) {
72 :           return NULL;
73 :       }
74 :       pool->log = log;
75 :   
76 :       cycle = ngx_pcalloc(pool, sizeof(ngx_cycle_t));  /*为内存池分配 sizeof(ngx_cycle_t) 大小的空间*/
77 :       if (cycle == NULL) {
78 :           ngx_destroy_pool(pool);
79 :           return NULL;
80 :       }
```

由上面的代码我们能够看出这里的动作：

1. 创建一个新的内存池

2. 在这个内存池上分配一块ngx_cycle_t大小的内存空间，将地址赋值给cycle变量。

然后我们继续在ngx_init_cycle函数中往下分析：

下面的代码主要是进行把先前的cycle变量的成员的复制到新的cycle变量，

这里有日志，路径，配置等等信息。

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
82 :       cycle->pool = pool; /*内存池，整个nginx生命周期内提供内存分配和管理*/
83 :       cycle->log = log;   /*日志管理，整个nginx生命周期*/
84 :       cycle->old_cycle = old_cycle; /*old cycle*/
85 :       /*cycle->conf_prefix存储配置文件的路径*/
86 :       cycle->conf_prefix.len = old_cycle->conf_prefix.len;
87 :       cycle->conf_prefix.data = ngx_pstrdup(pool, &old_cycle->conf_prefix);
88 :       if (cycle->conf_prefix.data == NULL) {
89 :           ngx_destroy_pool(pool);
90 :           return NULL;
91 :       }
92 :       /*cycle->prefix存储安装路径*/
93 :       cycle->prefix.len = old_cycle->prefix.len;
94 :       cycle->prefix.data = ngx_pstrdup(pool, &old_cycle->prefix);
95 :       if (cycle->prefix.data == NULL) {
96 :           ngx_destroy_pool(pool);
97 :           return NULL;
98 :       }
99 :   
100 :       cycle->conf_file.len = old_cycle->conf_file.len;
101 :       cycle->conf_file.data = ngx_pnalloc(pool, old_cycle->conf_file.len + 1);
102 :       if (cycle->conf_file.data == NULL) {
103 :           ngx_destroy_pool(pool);
104 :           return NULL;
105 :       }
106 :       ngx_cpystrn(cycle->conf_file.data, old_cycle->conf_file.data,
107 :                   old_cycle->conf_file.len + 1);
108 :   
109 :       cycle->conf_param.len = old_cycle->conf_param.len;
110 :       cycle->conf_param.data = ngx_pstrdup(pool, &old_cycle->conf_param);
111 :       if (cycle->conf_param.data == NULL) {
112 :           ngx_destroy_pool(pool);
113 :           return NULL;
114 :       }
115 :   
116 :   
117 :       n = old_cycle->paths.nelts ? old_cycle->paths.nelts : 10;  /*元素容量*/
118 :   
119 :       cycle->paths.elts = ngx_pcalloc(pool, n * sizeof(ngx_path_t *));
120 :       if (cycle->paths.elts == NULL) {
121 :           ngx_destroy_pool(pool);
122 :           return NULL;
123 :       }
124 :   
125 :       cycle->paths.nelts = 0;  /*元素个数*/
126 :       cycle->paths.size = sizeof(ngx_path_t *);  /*节点尺寸*/
127 :       cycle->paths.nalloc = n; /*default 容量为10*/
128 :       cycle->paths.pool = pool; /*所在内存池*/
```


在往下：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
148 :       /*nginx根据以往的经验（old_cycle）预测这一次的配置需要分配多少内存。*/
149 :       if (old_cycle->shared_memory.part.nelts) {
150 :           n = old_cycle->shared_memory.part.nelts;
151 :           for (part = old_cycle->shared_memory.part.next; part; part = part->next)
152 :           {
153 :               n += part->nelts;
154 :           }
155 :   
156 :       } else {
157 :           n = 1;
158 :       }
159 :       /*遍历old_cycle，统计上一次系统中分配了多少块共享内存，接着就按这个数据初始化当前cycle中共享内存的规模。*/
160 :       if (ngx_list_init(&cycle->shared_memory, pool, n, sizeof(ngx_shm_zone_t))
161 :           != NGX_OK)
162 :       {
163 :           ngx_destroy_pool(pool);
164 :           return NULL;
165 :       }
```

上面的代码主要是对共享内存的一些设置和初始化。

在往下，就是初始化cycle->listenting数组结构了，这个结构代表了我们的监听套接字，这里做了这么些事情：

1. 得出监听套接字结构数组的容量

2. 以这个容量分配内存

3. 初始化这个数组

源代码如下：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
167 :       n = old_cycle->listening.nelts ? old_cycle->listening.nelts : 10;
168 :   
169 :       cycle->listening.elts = ngx_pcalloc(pool, n * sizeof(ngx_listening_t)); /*为监听结构分配内存，容量为n==10*/
170 :       if (cycle->listening.elts == NULL) {
171 :           ngx_destroy_pool(pool);
172 :           return NULL;
173 :       }
174 :   
175 :       cycle->listening.nelts = 0;
176 :       cycle->listening.size = sizeof(ngx_listening_t);
177 :       cycle->listening.nalloc = n;
178 :       cycle->listening.pool = pool;
```

cycle->reusable_connections_queue挂载了一个双端队列，这个队列将存放可重用的网络连接，供nginx服务器回收使用已经打开却长时间为使用的网络连接。

```
181 :       ngx_queue_init(&cycle->reusable_connections_queue); /*初始化可重用网络连接队列*/
```

获取主机名称：

```
191 :       if (gethostname(hostname, NGX_MAXHOSTNAMELEN) == -1) {  /*获得主机名字, gethostname为系统调用*/
```

补充一下上面的内容你解析：

1. cycle->pathes数组分配空间，该数组用于管理nginx服务器程序运行过程中涉及的所有路径字符串

2. cycle->open_files链表分配空间，用于管理程序运行过程中打开的文件

3. cycle->shared_memory链表分配空间，用于管理共享内存

4. cycle->listening数组分配空间，用于管理套接字链接

5. cycle->resuable_connections_queue分配空间，管理可重用的网络连接，供nginx回收使用已经打开却长时间未被使用的网络连接。

core模块是nginx服务器运行的核心，下面的源代码就是建立core模块的上下文结构，类型为ngx_core_conf_t，代码如下：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
211 :       for (i = 0; ngx_modules[i]; i++) {
212 :           if (ngx_modules[i]->type != NGX_CORE_MODULE) { /*遍历模块数组，筛选出core模块*/
213 :               continue;
214 :           }
216 :           module = ngx_modules[i]->ctx;
218 :           if (module->create_conf) {
219 :               rv = module->create_conf(cycle);        /*建立cycle上下文结构,rv指向结构体 ngx_core_conf_t*/
220 :               if (rv == NULL) {
221 :                   ngx_destroy_pool(pool);
222 :                   return NULL;
223 :               }
224 :               cycle->conf_ctx[ngx_modules[i]->index] = rv;
225 :           }
226 :       }
```

这里的功能是：

1. 筛选出core类型的模块 line：212

2. 创建上下文结构 line：219

其中core模块的上下文结构是ngx_core_conf_t，cgdb调试打印如：

```
{
	name = {
			len = 4, data = 0x4a45b6 "core"
		}, 
	create_conf = 0x404ca2 <ngx_core_module_create_conf>, 
	init_conf = 0x404d84 <ngx_core_module_init_conf>
}
```

这里有两个回调函数，一个用于创建，一个用于初始化。

我们就分析一个第一个模块的create_conf回调函数，也就是modules[0]，回调函数为：ngx_core_module_create_conf，

源码很简单，就是在内存池里创建了一个ngx_core_conf_t的内存结构，然后用预定义的值赋值一下，这些值都没有具体的实际含义，所以下面还要进行的是init初始化，源码如下：

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
928 :   static void *
929 :   ngx_core_module_create_conf(ngx_cycle_t *cycle)
930 :   {
931 :       ngx_core_conf_t  *ccf;
932 :   
933 :       ccf = ngx_pcalloc(cycle->pool, sizeof(ngx_core_conf_t));  /*分配内存*/
934 :       if (ccf == NULL) {
935 :           return NULL;
936 :       }
937 :   
938 :       /*
939 :        * set by ngx_pcalloc()
940 :        *
941 :        *     ccf->pid = NULL;
942 :        *     ccf->oldpid = NULL;
943 :        *     ccf->priority = 0;
944 :        *     ccf->cpu_affinity_n = 0;
945 :        *     ccf->cpu_affinity = NULL;
946 :        */
947 :   
948 :       ccf->daemon = NGX_CONF_UNSET;
949 :       ccf->master = NGX_CONF_UNSET;
950 :       ccf->timer_resolution = NGX_CONF_UNSET_MSEC;
951 :   
952 :       ccf->worker_processes = NGX_CONF_UNSET;
953 :       ccf->debug_points = NGX_CONF_UNSET;
954 :   
955 :       ccf->rlimit_nofile = NGX_CONF_UNSET;
956 :       ccf->rlimit_core = NGX_CONF_UNSET;
957 :       ccf->rlimit_sigpending = NGX_CONF_UNSET;
958 :   
959 :       ccf->user = (ngx_uid_t) NGX_CONF_UNSET_UINT;
960 :       ccf->group = (ngx_gid_t) NGX_CONF_UNSET_UINT;
961 :   
962 :   #if (NGX_THREADS)  /*多线程运行nginx（实际没有使用多线程）*/
963 :       ccf->worker_threads = NGX_CONF_UNSET;
964 :       ccf->thread_stack_size = NGX_CONF_UNSET_SIZE;
965 :   #endif
966 :   
967 :       if (ngx_array_init(&ccf->env, cycle->pool, 1, sizeof(ngx_str_t))
968 :           != NGX_OK)
969 :       {
970 :           return NULL;
971 :       }
972 :   
973 :       return ccf;
974 :   }
```

最后把ngx_core_conf_t的结构体挂载到了cycle->conf_ctx上了，conf_ctx指向一个数组。

创建一个临时的内存池，用于配置文件的解析，解析完了之后，就释放

```
240 :       conf.temp_pool = ngx_create_pool(NGX_CYCLE_POOL_SIZE, log); 
```

初始化一个ngx_conf_t结构,这些用于储存配置的结构创建好了之后，就是解析配置了。

下面解析命令行配置：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
257 :       /*解析nginx命令行参数’-g’加入的配置*/
258 :       /*ngx_conf_param 用来解析命令行传递的配置*/
259 :       if (ngx_conf_param(&conf) != NGX_CONF_OK) {
260 :           environ = senv;
261 :           ngx_destroy_cycle_pools(&conf);
262 :           return NULL;
263 :       }
```

解析配置文件 nginx.conf：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
265 :       /*解析nginx配置文件*/
266 :       if (ngx_conf_parse(&conf, &cycle->conf_file) != NGX_CONF_OK) {
267 :           environ = senv;
268 :           ngx_destroy_cycle_pools(&conf);
269 :           return NULL;
270 :       }
```

把解析的值存入conf，这是一个ngx_conf_t的结构体.

然后就用一个for循环筛选出core模块，进行初始化，这个和create的回调很像，只不过这里使用的是init函数。

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
277 :       for (i = 0; ngx_modules[i]; i++) {
278 :           if (ngx_modules[i]->type != NGX_CORE_MODULE) {  /*遍历模块，选出core模块*/
279 :               continue;
280 :           }
282 :           module = ngx_modules[i]->ctx;
284 :           if (module->init_conf) {
285 :               if (module->init_conf(cycle, cycle->conf_ctx[ngx_modules[i]->index]) /*init模块*/
286 :                   == NGX_CONF_ERROR)
287 :               {
288 :                   environ = senv;
289 :                   ngx_destroy_cycle_pools(&conf);
290 :                   return NULL;
291 :               }
292 :           }
293 :       }
```

到这里，我们的core模块上下文结构的初始化就全部完成了。现在接着往下

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
321 :               if (ngx_create_pidfile(&ccf->pid, log) != NGX_OK) { /*创建新pid文件*/
322 :                   goto failed;
323 :               }
325 :               ngx_delete_pidfile(old_cycle);  /*删除旧的pid文件*/
```

这里就是创建pid文件，删除旧的pid文件。

ngx_init_cycle()函数接下来就是：

1. 填充cycle->paths数组

2. 遍历cycle->open_files链表并打开文件

3. 初始化shared_memory链表

4. 遍历cycle->listening数组并打开所有监听的socket，

5. 打开cycle->paths数组

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_cycle.c 
======================================================================
581 :       if (ngx_open_listening_sockets(cycle) != NGX_OK) {  /*todo 打开open标志为1的监听socket,创建实际的监听端口*/
582 :           goto failed;
583 :       }
```

ngx_open_listening_sockets负责绑定，监听我们的套接字。

到这里我们就完成了 ngx_init_cycle()函数执行的主要工作的梳理。现在我们回到main()函数.

下一步我们进行信号的设置。信号设置工作主要围绕存放信号信息的结构数组signals进行。数组的每一个元素都是ngx_signal_t结构体。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
352 :       if (ngx_signal) {
353 :           return ngx_signal_process(cycle, ngx_signal);
354 :       }
```

信号设置完成之后，就是开启我们的工作进程了。

```
文件名： ../nginx-d0e39ec4f23f/src/core/nginx.c 
======================================================================
403 :       if (ngx_process == NGX_PROCESS_SINGLE) { /*看是否是单进程模式*/
404 :           ngx_single_process_cycle(cycle);  /*单进程循环模式*/
405 :   
406 :       } else {
407 :           ngx_master_process_cycle(cycle);  /*启动 work process*/
408 :       }
```

这里就进入我们的进程选择模式了，我开始设置的是单进程，所以我们分析进入单进程的流程。

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
293 :   void
294 :   ngx_single_process_cycle(ngx_cycle_t *cycle) /*单进程循环模式*/
295 :   {
296 :       ngx_uint_t  i;
297 :   
298 :       if (ngx_set_environment(cycle, NULL) == NULL) {
299 :           /* fatal */
300 :           exit(2);
301 :       }
302 :   
303 :       for (i = 0; ngx_modules[i]; i++) {
304 :           if (ngx_modules[i]->init_process) {
305 :               if (ngx_modules[i]->init_process(cycle) == NGX_ERROR) {
306 :                   /* fatal */
307 :                   exit(2);
308 :               }
309 :           }
310 :       }
311 :   
312 :       for ( ;; ) {
313 :           ngx_log_debug0(NGX_LOG_DEBUG_EVENT, cycle->log, 0, "worker cycle");
314 :   
315 :           ngx_process_events_and_timers(cycle);  /*阻塞调用, 但进程启动之后，就阻塞在这里, 由信号驱动*/
316 :   
317 :           if (ngx_terminate || ngx_quit) {
318 :   
319 :               for (i = 0; ngx_modules[i]; i++) {
320 :                   if (ngx_modules[i]->exit_process) {
321 :                       ngx_modules[i]->exit_process(cycle);
322 :                   }
323 :               }
324 :   
325 :               ngx_master_process_exit(cycle);
326 :           }
327 :   
328 :           if (ngx_reconfigure) {
329 :               ngx_reconfigure = 0;
330 :               ngx_log_error(NGX_LOG_NOTICE, cycle->log, 0, "reconfiguring");
331 :   
332 :               cycle = ngx_init_cycle(cycle);
333 :               if (cycle == NULL) {
334 :                   cycle = (ngx_cycle_t *) ngx_cycle;
335 :                   continue;
336 :               }
337 :   
338 :               ngx_cycle = cycle;
339 :           }
340 :   
341 :           if (ngx_reopen) {
342 :               ngx_reopen = 0;
343 :               ngx_log_error(NGX_LOG_NOTICE, cycle->log, 0, "reopening logs");
344 :               ngx_reopen_files(cycle, (ngx_uid_t) -1);
345 :           }
346 :       }
347 :   }
```

我们看到上面的代码并不是很多。

这里的流程是：

1. 使用cycle设置环境变量

2. 遍历每一个模块，使用cycle初始化每一个模块的进程设置

3. 进入循环调用

nginx是完全由事件来推动的，在循环调用里当发现有事件发生，就会处理。

```
文件名： ../nginx-d0e39ec4f23f/src/os/unix/ngx_process_cycle.c 
======================================================================
315 :           ngx_process_events_and_timers(cycle);  /*阻塞调用, 但进程启动之后，就阻塞在这里, 由信号驱动*/
```

nginx的启动过程到此就全部分析完了，中间还有些函数，过程，设置的没有完全分析透彻，以后会慢慢消化，补上。

学习永无止境，学习永不停息！













