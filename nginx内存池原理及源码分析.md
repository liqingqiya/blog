nginx内存池原理及源码分析
==================================

nginx对于内存的使用是非常小气的，绝对不浪费一丝毫的内存资源。所以nginx自己设计了一个内存池的结构，
用于分配内存，这样就能最大的提高内存的分配效率，总结nginx的内存池的特点：

#### 内存分配尽量使用内存池分配，一次分配使用之后，并不会马上销毁，而是等到整个内存池都使用完了之后，才会考虑一次性的销毁内存 ####

这样利用有三个优点：

+ 效率提高，这个是相比与直接malloc，和 free来讲的

+ 减少了内存的内部碎片，因为每次销毁都会是比较大的内存块

+ 防止内存泄漏

下面解释一下内存池的原理：

1. 内存池的原理非常简单，我们事先划分出一个大内存块，等到我们需要分配一个小内存的时候，直接返回这个内存池的可用地址就行了，这样就提高分配的内存的效率了。这是想对于系统频繁的malloc和free而言的。

2. 内存池是在空间和时间效率的一个权衡得出的结果，我们分配一个大存储块来用作内存池必然会造成一定的内存空间浪费，考虑到我们的分配的高效，这个取舍在一定的条件下还是可以接受的。这个是我们在空间和时间之间权衡过之后的结果。适当使用就行。

### 我们来看nginx的内存池的源码实现： ###

这个是类型封装，定义在 nginx_core.h 头文件15行.

```
typedef struct ngx_pool_s        ngx_pool_t;			/*内存管理结构*/
```

内存池的结构体定义：

```
struct ngx_pool_s {
    ngx_pool_data_t       d;    	/*内存池数据区域*/
    size_t                max;  	/*可分配的最大数据区大小*/
    ngx_pool_t           *current;  /*指向当前可用的的内存池结构*/
    ngx_chain_t          *chain;    /*？？todo*/
    ngx_pool_large_t     *large;    /*携带的大存储块，不超过3个*/
    ngx_pool_cleanup_t   *cleanup;	/*清理内存池的回调函数*/
    ngx_log_t            *log;	/*日志*/
}; /*内存池管理结构*/
```

这个是我们的最核心的内存池结构,nginx的内存池并不是只有一块内存块，而是有众多的内存池链接起来的一个内存池链表。

下面解释下ngx_pool_s这个结构的字段：

1. d; 这个字段是实际存储数据的地方。这里以组合的形式包含在ngx_pool_s中。

2. max; 这个字段是我们在建立内存池之后，分配内存的时候，最大可以分配的内存大小。

3. current; 这个字段指向当前可用，内存池链表上最近的一个内存池结构。

4. chain; 这个应该是为了形成一个内存池链表的字段，这个字段我现在也还没有完全弄清楚，先放一下。todo

5. large; 这个结构指向一个比较大型的内存结构，应用情景在分配内存的时候，请求分配的内存太大（大于max），那么就直接开辟一个ngx_pool_large_t结构的内存块，这个内存块一个内存池最多可以开辟3个，这是一个经验值。

6. cleanup; 这个字段指向我们销毁内存池时候的回调函数。

7. log; 很简单，顾名思义，这个是用来打印日志的，一般优秀的软件都会有专业的日志打印，以便我们业务分析，bug的排查等等。

我们再来看一下另一个核心的结构——数据结构——ngx_pool_data_t：

```
typedef struct {
    u_char               *last;     /*指向数据区域的结束地址*/
    u_char               *end;      /*指向内存池结构的结束地址*/
    ngx_pool_t           *next;     /*指向下一个内存池节点*/
    ngx_uint_t           failed;    /*申请内存的时候失败的次数*/
} ngx_pool_data_t;      		/*内存数据区域*/
```

### 下面从几个内存池的几个关键函数分析：

内存池的头文件是：ngx_palloc.h,这个头文件一般是定义了我们所需要的数据结构，函数定义基本都在ngx_palloc.c文件中。

#### 1. 创建内存池

这个函数定义在ngx_palloc.c的 line 16-41

```
ngx_pool_t *
ngx_create_pool(size_t size, ngx_log_t *log)
{
    ngx_pool_t  *p;

    p = ngx_memalign(NGX_POOL_ALIGNMENT, size, log);    /*进行16个字节的内存对齐分配，对其处理一般是为了从性能上考虑？？todo*/
    if (p == NULL) {
        return NULL;
    }

    p->d.last = (u_char *) p + sizeof(ngx_pool_t);  /*内存池数据区域的结尾地址*/
    p->d.end = (u_char *) p + size;         /*分配的内存块的最后地址*/
    p->d.next = NULL;   /*指向下一个节点*/
    p->d.failed = 0;

    size = size - sizeof(ngx_pool_t);
    p->max = (size < NGX_MAX_ALLOC_FROM_POOL) ? size : NGX_MAX_ALLOC_FROM_POOL; /*todo*/

    p->current = p;     /*当前内存池的地址*/
    p->chain = NULL;
    p->large = NULL;
    p->cleanup = NULL;
    p->log = log;

    return p;
}
```

先从传入的参数说起，size_t类型的size是我们需要开辟的大小，按照这个结构开辟内存，ngx_log_t是日志结构.

第88行，我们对齐分配了size个字节的内存，返回了首地址。

第93行，p->d.last指向内存池数据区域的结尾地址。

第94行，p->d.end指向内存池结构的结尾地址。

第95行，p->d.next指向下一个内存池，这样组成了一个内存池链表。这里我们刚开始创建的时候，赋值为NULL。

第96行，p->d.failed这里是记录我们这个内存池分配内存的时候，失败次数。

failed这个字段在 函数ngx_palloc_block里会有比较和变化。

```
    /*遍历到内存池链表的末尾*/
    for (p = current; p->d.next; p = p->d.next) {
        if (p->d.failed++ > 4) {    /*4是一个经验值*/
            current = p->d.next;    /*如果当前的内存池内存分配失败次数 >4, 那么使用下一个内存池，并且failed++*/
        }
    }
```

这里的源码显示，如果我们的failed字段大于4,那么current就会指向下一个内存池，为什么是4？

你这个内存池都4次失败了，那么以后也都不会在用你了。这是个我们在实际中总结出来的值。current指向的和之后的才是可用的内存池。

下面的代码就是初始化赋值，初始化我们的内存池结构。

#### 2. 开辟内存

```
void *
ngx_palloc(ngx_pool_t *pool, size_t size)   /*尝试从pool内存池里分配size大小的内存空间*/
{
    u_char      *m;
    ngx_pool_t  *p;

    if (size <= pool->max) {    /*size在内存池设定的可分配的最大值的范围内*/

        p = pool->current;

        do {
            m = ngx_align_ptr(p->d.last, NGX_ALIGNMENT);

            if ((size_t) (p->d.end - m) >= size) {
                p->d.last = m + size;

                return m;   /*返回可用内存地址*/
            }

            p = p->d.next;  /*当前节点不够分配，那么移到下一个内存节点*/

        } while (p);

        return ngx_palloc_block(pool, size);    /*都不够分配，那么重新开辟一个内存节点节点, 并返回地址*/
    }

    return ngx_palloc_large(pool, size);    /*size太大，那么就开辟一个大内存节点结构 ngx_pool_large_t,并返回地址*/
}
```

这里我么说一下上面代码的流程思路：

1. 传入的参数是我们要用到的内存池和要开辟的大小。

2. 我们先比较size和当前内存池的最大允许开辟的内存大小，如果在范围之内，那么就进行下一步，如果大于最大的允许，那么就开辟一个ngx_pool_large_t内存块。然后pool->large会指向这个地址。

3. size<max 范围之内的时候,这里有一个循环，循环内的作用是在内存池链里选择一个合适的内存池节点来分配内存，成功就返回地址。

4. 如果没有找到合适的内存池节点，那么就开辟一个新的内存池结构出来，分配空间，并返回地址，把该新节点链接到我们的内存池链的尾巴上。

下面我们就讲一下 ngx_palloc_block(pool, size); 

```
static void *
ngx_palloc_block(ngx_pool_t *pool, size_t size) /*新建一个内存池，并与先前的内存池组成一个内存池链表*/
{
    u_char      *m;
    size_t       psize;
    ngx_pool_t  *p, *new, *current;

    psize = (size_t) (pool->d.end - (u_char *) pool);   /*当前内存池的大小*/

    m = ngx_memalign(NGX_POOL_ALIGNMENT, psize, pool->log); /*对齐分配psize大小的内存*/
    if (m == NULL) {
        return NULL;
    }

    new = (ngx_pool_t *) m; /*强制转化指针*/

    new->d.end = m + psize; /*指向新开辟的内存池的结尾*/
    new->d.next = NULL;     /*下一个内存池*/
    new->d.failed = 0;      /*内存分配失败的次数*/

    m += sizeof(ngx_pool_data_t);   
    m = ngx_align_ptr(m, NGX_ALIGNMENT);
    new->d.last = m + size; /*指向数据区域的结尾*/

    current = pool->current;    /*指向当前的内存池*/
    /*遍历到内存池链表的末尾*/
    for (p = current; p->d.next; p = p->d.next) {
        if (p->d.failed++ > 4) {    /*4是一个经验值*/
            current = p->d.next;    /*如果当前的内存池内存分配失败次数 >4, 那么使用下一个内存池，并且failed++*/
        }
    }

    p->d.next = new;    /*内存池末尾指向新开辟的内存池节点*/

    pool->current = current ? current : new;        /*current指向当前可用的内存池*/

    return m;       /*返回新的内存池的地址*/
}
```

这里的流程如下：

1. 首先按照size开辟一个内存块，返回地址存入m，并将m强制转化为ngx_pool_t存入new。

2. 初始化end，next，failed，last等等字段。

3. 使用一个for循环，遍历到内存池的末尾，循环之后，p指向最后一个内存池，current指向第一个还能用的内存池（failed<4），这个时候在赋值到p->next就行了。

4. 返回该内存池的节点地址。

#### 3. 销毁内存池

ngx_destory_pool函数负责销毁内存池，源码如下：

```
void
ngx_destroy_pool(ngx_pool_t *pool)
{
    ngx_pool_t          *p, *n;
    ngx_pool_large_t    *l;
    ngx_pool_cleanup_t  *c;

    /*调用设定好的回调函数*/
    for (c = pool->cleanup; c; c = c->next) {
        if (c->handler) {
            ngx_log_debug1(NGX_LOG_DEBUG_ALLOC, pool->log, 0,
                           "run cleanup: %p", c);
            c->handler(c->data);
        }
    }
     /*销毁大块内存块*/
    for (l = pool->large; l; l = l->next) {

        ngx_log_debug1(NGX_LOG_DEBUG_ALLOC, pool->log, 0, "free: %p", l->alloc);

        if (l->alloc) {
            ngx_free(l->alloc);
        }
    }

#if (NGX_DEBUG)

    /*
     * we could allocate the pool->log from this pool
     * so we cannot use this log while free()ing the pool
     */

    for (p = pool, n = pool->d.next; /* void */; p = n, n = n->d.next) {
        ngx_log_debug2(NGX_LOG_DEBUG_ALLOC, pool->log, 0,
                       "free: %p, unused: %uz", p, p->d.end - p->d.last);

        if (n == NULL) {
            break;
        }
    }

#endif
    /*小块的内存块销毁，内存池的数据区域，真正的内存池的核心结构*/
    for (p = pool, n = pool->d.next; /* void */; p = n, n = n->d.next) {
        ngx_free(p);

        if (n == NULL) {
            break;
        }
    }
}
```

流程如下：

1. 首先调用我们预先设定的回调函数，这些回调函数我么存放在pool的cleanup字段中，这个字段指向一个结构体。

这是我们的回调函数链结构。


```
typedef void (*ngx_pool_cleanup_pt)(void *data);	/*封装了一个函数指针类型*/

typedef struct ngx_pool_cleanup_s  ngx_pool_cleanup_t;

struct ngx_pool_cleanup_s {
    ngx_pool_cleanup_pt   handler;  /*回调函数指针*/
    void                 *data;     /*回调函数所需要的参数*/
    ngx_pool_cleanup_t   *next;     /*指向下一个回调函数节点*/
};
```

2. 释放我们内存池的大存储块。

3. 释放我们的内存池的数据区域，也就是内存池实际的存储区域。

#### 这里注意一点：nginx中， 小块内存（内存池的数据区域）除了在内存池被销毁的时候都是不能被释放的。绝对是和内存池一起释放销毁的。但是我们的大块存储区域是在过程中释放的。 ####

#### 4. 内存池复位

```
void
ngx_reset_pool(ngx_pool_t *pool)
{
    ngx_pool_t        *p;
    ngx_pool_large_t  *l;
    /*释放大块存储区域*/
    for (l = pool->large; l; l = l->next) {
        if (l->alloc) {
            ngx_free(l->alloc);
        }
    }
    /*内存池链中的每一个内存池节点都清零failed，并且last也复位，这个时候就没有数据区域了*/
    for (p = pool; p; p = p->d.next) {
        p->d.last = (u_char *) p + sizeof(ngx_pool_t);
        p->d.failed = 0;
    }

    pool->current = pool;
    pool->chain = NULL;
    pool->large = NULL;
}
```

这个函数做了这么三个方面：

1. 释放大块内存区域

2. 复位last字段，这个时候就没有我们的数据区域了。

3. 清零failed，也就是我们每一个内存块的分配失败记录。

#### 5. 管理大块内存的两个函数

+ ngx_palloc_large 创建

+ ngx_pfree 释放


内存管理的核心就这么几个方面：
---------------------------

+ 创建内存池

+ 分配内存

+ 销毁内存池

ngx_palloc.c中还有其他的一些函数，这个下面继续学习。



