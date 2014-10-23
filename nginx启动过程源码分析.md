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



