我们知道linux的事件驱动模型经历了select，poll，epoll的几个阶段
======================================================

web服务器响应和处理web请求的过程，很多都是基于事件驱动模型的，比如nginx就是完全基于事件驱动模型的。

包含事件收集器，事件发送器，事件处理器。

事件处理器基本有三种方式实现：

+ 事件发送器每传递一个请求，目标对象创建一个新的进程，然后在这个子进程调用事件处理器来处理该请求。

+ 事件发送器传递一个请求，目标对象创建一个新的线程，调用事件处理器处理该请求。

+ 事件发送器传递一个请求，目标对象就将其放入一个待处理事件的列表，使用非阻塞I/O方式调用事件处理器处理该请求。

但是我们知道使用多进程和多线程在请求量非常大的时候，开销是非常大的，内存开销，进程（线程）调度开销。而且这个开销随着我们的请求是线性增加的。

大多数的网络服务器都是采用上面提到的第三种方式，形成“事件驱动处理库”

事件驱动模型也叫做多路I/O复用模型。

在我们的linux操作系统上，最常见的有三种模型：select模型，poll模型，epoll模型。

下面我们以此来介绍下这三种模型：

select模型
---------------------

select模型是基础的一个事件驱动模型库，linux和windows都是支持这个接口的。

使用select事件驱动库的步骤一般是：

1. 创建所关注的事件描述符集合。对于一个描述符，可以关注上面的读事件，写事件，及异常发生事件。
所以我们需要创建三类事件描述符的集合，分别用来收集读事件的描述符，写事件描述符，异常事件描述符。

2. 调用系统调用select（）函数，等待事件发生。这里我们可以设置select的超时时间。但是select的阻塞和是否设置非阻塞I/O是没有关系的。

3. 轮询所有时间的描述符集合中的每一个事件描述符，检查是否有相应的事件发生，如果有，select（）会返回调用结果，就进行处理。

下面就在linux操作系统上的实际运用来说明：

select函数对数据结构fd_set进行操作，这个表示一个由打开的文件描述符构成的集合。然后系统定义了一组宏来控制这些集合。

```
#include <sys/types.h>
#include <sys/time.h>

void FD_ZERO(fd_set *fdset);
void FD_CLR(int fd, fd_set *fdset);
void FD_SET(int fd, fd_set *fdset);

int FD_ISSET(int fd, fd_set *fdset);
```
来解释一下上面的几个宏：

FD_ZERO用于将fd_set这个描述符集合初始化为空集合，FD_SET，FD_CLF分别用于在集合中设置和清除有参数fd传递的文件描述符。

如果FD_ISSET宏中由参数fd指向的文件描述符是由参数fdset指向的fd_set集合中的一个元素，FD_ISSET将返回非零值。

但是select有一个非常蛋疼的参数要指定，FD_SETSIZE，这个指定了我们能够监控的最大的一个描述符集合的大小。为什么会有这个？

这也是当描述符集合大到一定程度的时候，select每一次轮询都要遍历所有的文件，这会造成性能的严重下降。性能随集合大小以线性下降。

select（）函数可以使用一个超时值来防止无限期的阻塞，这个超时值由一个timeval结构给出。定义在sys/time.h中：

```
struct timeval{
       time_t tv_sec;	/*seconds*/
       long   tv_usec;	/*microseconds*/
}
```

类型time_t在头文件sys/types.h中被定义为一个整数类型。

select系统调用的原型如下：

```
#include <sys/types.h>
#include <sys/time.h>

int select(int nfds, fd_set *readfds, fd_set *writefds, fd_set * errorfds, struct timeval *timeout);
```

select调用用于测试文件描述符集合中，是否有一个文件描述符已经处于可读状态，可写状态，错误状态，select将会阻塞以等待某个文件描述符进入以上的三种状态。

参数nfds指定需要测试的文件描述符数目，测试的描述符号范围从0到nfds-1.

select函数会在以下情况下返回：

1. readfds集合中有描述符可读

2. writefds集合中有描述符可写

3. errorfds集合中有描述符遇到错误

如果上面三种情况都没有发生，select将在timeout制定时间经过后返回。如果timeout参数是一个空指针，那么将一直阻塞。

#### 当select返回时，描述符集合将被修改以指示那些描述符正处在可读，可写，错误的状态。

#### 也就是这些fd_set会修改成只留下了状态改变的fd

我们可以使用FD_ISSET()来进行测试。

我们可以使用FD_ISSET对描述符进行测试，来找到需要注意的描述符。

如果select因为超时而返回，那么所有的描述符集合都将被清空。

下面说一下select调用返回的情况：

1. 有事件发生的时候，返回状态发生变化的描述符总数。

2. 失败时，返回-1并设置errno来描述错误。可能的错误：EBADF（无效描述符），EINTR（因中断而返回），EINVAL（nfds或timeout取值错误）

3. 超时时间返回0

下面是经典的运用select的一个例子：

```
#include<sys/types.h>
#include<sys/time.h>
#include<stdio.h>
#include<fcntl.h>
#include<sys/ioctl.h>
#include<unistd.h>
#include<stdlib.h>

int main(){
    char buffer[128];
    int result, nread;

    fd_set inputs, testfds;
    struct timeval timeout;

    FD_ZERO(&inputs);
    FD_SET(0, &inputs);

    while(1){
        testfds = inputs;
        timeout.tv_sec = 2;
        timeout.tv_usec = 500000;

        //result  = select(FD_SETSIZE, &testfds, (fd_set*)NULL, (fd_set*)NULL, &timeout);
        result  = select(FD_SETSIZE, &testfds, (fd_set*)NULL, (fd_set*)NULL, (struct timeval *)NULL);

        switch(result){
            case 0:
                printf("timeout\n");
                break;
            case -1:
                perror("select");
                exit(1);
            default:
                if(FD_ISSET(0, &testfds)){
                    ioctl(0, FIONREAD, &nread);
                    if(nread==0){
                        printf("keyboard done\n");
                        exit(0);
                    }
                    nread = read(0, buffer, nread);
                    buffer[nread] = 0;
                    printf("read %d from keyboard: %s", nread, buffer);
                }
                break;
        }
    }
    return 0;
}
```

poll事件模型库
--------------------

poll库是linux的基本的事件驱动模型，在linux2.1.23中引入。作为select的一个优化。

poll与select的工作方式相同：

1. 创建一个关注事件的描述符集合

2. 等待事件的发生

3. 轮询描述符集合，检查是否有时间发生，有则处理

poll库和select库的区别在于，select库需要为读事件，写事件，异常事件分别创建描述符集合。

最后轮询的时候，要轮询三个集合。

poll只创建一个描述符集合，在每一个描述符对应的结构上分别设置读事件，写事件，异常事件，最后轮询的时候可以同时检查这三种事件是否发生。

epoll事件驱动模型
--------------------------------

epoll库是linux的高性能事件驱动库，非常优秀。在linux2.5.44中引入，linux2.6及以上版本都能使用。

epoll和select，poll最大的区别在于效率。

我们先想一想select和poll是怎么一个工作方式：

1. 创建一个待处理事件列表（描述符集合，等待关注事件的发生）

2. 把这个列表发给内核

3. 返回的时候再去轮询检查这个列表，以判断事件是否发生

前面已经提到，这样处理事件，当我们的描述符列表比较多的应用，效率会线性下降。

所以这里有一种比较好的处理方式：将描述符列表的管理交给内核，一旦有事件发生，内核把事件的描述符列表通知给进程。
这样就避免了轮询整个描述符列表。

内核怎么得到活动的描述符列表？

是不是要轮询？是不是的问？不是的，描述符结构设置了回调函数，如果有事件发生，会自己通知内核。

这样就对描述符的集合大小没有上限。

epoll就是这样的一种事件驱动模型。

+ 首先，epoll库通过相关调用通知内核创建一个有N个描述符的事件列表

+ 然后，给这些描述符设置所关注的事情，并把它添加到内核事件列表中去

+ 完成设置之后，epoll库就可以开始等待内核通知事件的发生了。

+ 某一个事件发生之后，内核将发生事件的描述符列表上报给epoll库。

+ epoll库得到事件列表之后，就能进行事件处理了。

epoll库在linux是非常高效的。支持一个进程打开大数目的事件描述符，上限是系统可以打开文件的最大数目。

epoll库的I/O效率不随描述符数目增加而线性下降，因为它只会对内核上报的活跃的描述符进行处理。