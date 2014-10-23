nginx自己封装了一个数组的结构
----------------------------

这个结构定义在src/core/ngx_array.h/c中

```
typedef struct {
    void        *elts;      /*数组数据区域*/
    ngx_uint_t   nelts;     /*element个数*/
    size_t       size;      /*一个元素内存的字节大小*/
    ngx_uint_t   nalloc;    /*数组容量*/
    ngx_pool_t  *pool;      /*数组所在的内存池*/
} ngx_array_t;              /*数组管理器，就代表一个数组*/
```

主要能够实现的特点：
--------------------------

#### + 能够拓展容量

#### + 在内存池中分配，方便管理内存

#### + 能够存储通用数据类型

这个结构也是很简单的，只有五个方法来管理这个数组。

```
ngx_array_t *ngx_array_create(ngx_pool_t *p, ngx_uint_t n, size_t size);
void ngx_array_destroy(ngx_array_t *a);
void *ngx_array_push(ngx_array_t *a);
void *ngx_array_push_n(ngx_array_t *a, ngx_uint_t n);

static ngx_inline ngx_int_t
ngx_array_init(ngx_array_t *array, ngx_pool_t *pool, ngx_uint_t n, size_t size)    
```

这个模块怎么个使用法？

1. 调用ngx_array_create()在内存池中创建ngx_array_t数据结构的内存

2. 调用ngx_array_init（）初始化这块内存结构

3. 使用ngx_array_t数组结构

我们来看一下ngx_array_create()函数代码：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_array.c 
======================================================================
12 :   ngx_array_t *
13 :   ngx_array_create(ngx_pool_t *p, ngx_uint_t n, size_t size)
14 :   {
15 :       ngx_array_t *a;
16 :   
17 :       a = ngx_palloc(p, sizeof(ngx_array_t));     /*开辟数组内存结构*/
18 :       if (a == NULL) {
19 :           return NULL;
20 :       }
21 :   
22 :       if (ngx_array_init(a, p, n, size) != NGX_OK) {  /*初始化数组内存结构*/
23 :           return NULL;
24 :       }
25 :   
26 :       return a;           /*返回数组结构地址*/
27 :   }
```

代码很简单，第17行在内存池中分配了ngx_array_t结构大小的内存，然后第22行调用ngx_array_init进行初始化这块内存结构。最后返回这块内存地址。

ngx_array_init()声明成了文件域的函数，就只为该编译单元的create函数调用。下面是init的源码：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_array.h 
======================================================================
31 :   static ngx_inline ngx_int_t
32 :   ngx_array_init(ngx_array_t *array, ngx_pool_t *pool, ngx_uint_t n, size_t size)    
33 :   {
34 :       /*
35 :        * set "array->nelts" before "array->elts", otherwise MSVC thinks
36 :        * that "array->nelts" may be used without having been initialized
37 :        */
38 :   
39 :       array->nelts = 0;        /*元素个数*/
40 :       array->size = size;     /*单个节点的内存大小*/
41 :       array->nalloc = n;      /*数组容量*/
42 :       array->pool = pool;     /*内存池*/
43 :   
44 :       array->elts = ngx_palloc(pool, n * size);   /*分配内存空间*/
45 :       if (array->elts == NULL) {
46 :           return NGX_ERROR;
47 :       }
48 :   
49 :       return NGX_OK;
50 :   }
```

这里初始化了这个数组结构的nelts, size, nalloc, pool，分别是：数组元素个数，单个元素内存大小，数组容量，数组所在内存池。

我们的数组的准备工作就完全做好了。

怎么添加元素？

首先，从ngx_array_t结构中返回一个可用地址，也就是调用函数：ngx_array_push()

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_array.c 
======================================================================
47 :   void *
48 :   ngx_array_push(ngx_array_t *a)
49 :   {
50 :       void        *elt, *new;
51 :       size_t       size;
52 :       ngx_pool_t  *p;
53 :   
54 :       if (a->nelts == a->nalloc) {    /*如果数组元素个数恰好超出了容量*/
55 :   
56 :           /* the array is full */
57 :   
58 :           size = a->size * a->nalloc;     /*计算数据区域总共多少内存*/
59 :   
60 :           p = a->pool;        /*内存池*/
61 :   
62 :           if ((u_char *) a->elts + size == p->d.last  /*如果内存池的last指针指向了数组的最后一个元素*/
63 :               && p->d.last + a->size <= p->d.end)         
64 :           {
65 :               /*
66 :                * the array allocation is the last in the pool
67 :                * and there is space for new allocation
68 :                */
69 :   
70 :               p->d.last += a->size;  /*分配一个size大小的空间, a->size为一个元素的内存大小*/
71 :               a->nalloc++;         /*拓展一个容量*/
72 :   
73 :           } else {
74 :               /* allocate a new array */
75 :   
76 :               new = ngx_palloc(p, 2 * size);  /*容量拓展为以前的两倍内存空间*/
77 :               if (new == NULL) {
78 :                   return NULL;
79 :               }
80 :   
81 :               ngx_memcpy(new, a->elts, size);     /*复制原来的数据到新的数据区域中*/
82 :               a->elts = new;                        /*指向新的数据区域*/  
83 :               a->nalloc *= 2;                       /*容量为2倍*/
84 :           }
85 :       }
```

这个函数在 line:54 判断当前数组是否还有空闲容量，如果有，计算可用空间地址，并返回，

现在我们讨论下如果当前数组没有空闲空间的情况：

毫无疑问，这个时候肯定是要拓展数组容量的，nginx在这里做了一些讨论。

如果没有则开辟出一个新的空间。

```
62 :           if ((u_char *) a->elts + size == p->d.last  /*如果内存池的last指针指向了数组的最后一个元素*/
63 :               && p->d.last + a->size <= p->d.end)         
```

上面的一个语句主要规定了两点情况：

+ 内存池的last指针指向了数组最后一个元素的后面一个地址，也就是说当前内存池恰好分配到该数组的最后一个元素。

+ && 内存池的剩余可分配空间大于当前数组的内存容量。

要同时满足了这两点，那么就：

1. 移动内存池的last指针，将内存池数据区域增加一个数组内存容量大小

2. 数组拓展一个节点容量

如果不满足，那么就开辟一个数组内存容量增加一倍，也就是从内存池中开辟两倍的内存出来作为新的存储区域，当然我们要把旧的数据复制过去。

```
76 :               new = ngx_palloc(p, 2 * size);  /*容量拓展为以前的两倍内存空间*/
77 :               if (new == NULL) {
78 :                   return NULL;
79 :               }
81 :               ngx_memcpy(new, a->elts, size);     /*复制原来的数据到新的数据区域中*/
82 :               a->elts = new;                        /*指向新的数据区域*/  
83 :               a->nalloc *= 2;                       /*容量为2倍*/
```

这样数组就有了可用空间了，最后把地址返回就行了：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_array.c 
======================================================================
87 :       elt = (u_char *) a->elts + a->size * a->nelts;  /*数据区中实际已经存放数据的子区的末尾*/
88 :       a->nelts++;         /*元素个数++*/
90 :       return elt;
```

如此我们通过ngx_array_push就能拿到可用的空间地址，当然这里还有一个函数：ngx_array_push_n，这个原理是一模一样的，只不过是分配拿到可以存储n个元素的可用首地址。

最后，我们拿到可用地址之后，就可以对该内存块进行赋值了，这样就是ngx_array_t的一个完整的使用流程。

下面总结下特色：
--------------------------------

1. 相比c语言的数组，这里的数组具有能够拓展容量的特性。更灵活。

2. 大家也注意到了，我们在line：76行开辟内存，line81行复制内存，那么以前的内存怎么办了？我们在这里好像没有进行任何处理。
这是nginx故意的，因为ngx_array_t是在内存池中分配的，内存池会有自己的一套管理内存的方法。我们根本不用关系上一块存储数组的内存怎么样处理。
实际上nginx的内存池并不会在ngx_destory_pool（）函数的外面销毁内存，对于这种小块内存，nginx的方法是连同内存池一块一起释放，这样效率会更高一些。
