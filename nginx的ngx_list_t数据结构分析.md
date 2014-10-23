nginx自己定义了特色的单链表结构
==================================

#### + nginx的单链表是顺序存储和链接存储的结合

#### + 内存池分配内存

nginx的单链表的结构体定义在，src/core/ngx_list.h/c

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_list.h 
======================================================================
15 :   /*单链表结构*/
16 :   typedef struct ngx_list_part_s  ngx_list_part_t;
17 :   
18 :   struct ngx_list_part_s {
19 :       void             *elts;     /*指向我们的元素节点*/
20 :       ngx_uint_t        nelts;    /**/
21 :       ngx_list_part_t  *next;     /*指向下一个链表元素节点*/
22 :   };
23 :   
24 :   
25 :   typedef struct {
26 :       ngx_list_part_t  *last;     /*指向最后一个节点*/
27 :       ngx_list_part_t   part;     /*第一个节点，以组合的方式放在ngx_list_t中*/
28 :       size_t            size;      /*每个元素内存大小*/
29 :       ngx_uint_t        nalloc;   /*每一个节点容量大小,也就是节点的个数*/
30 :       ngx_pool_t       *pool;     /*列表所在内存池*/
31 :   } ngx_list_t;       /*链表结构头*/
```

nginx定义了两个结构，一个结构作为管理单链表的代表 ngx_list_t，一个是定义为链表节点的结构体 ngx_list_part_s，

ngx_list_part_s提供了一层封装: typedef struct ngx_list_part_s ngx_list_part_t;

首先一行行解释下 ngx_list_t这个结构：

1. last字段，指向我们单链表的最后一个节点

2. part字段，以组合的方式，包含我们的第一个首链表节点

3. size指定我们每一个元素的内存大小

4. nalloc指定我们每一个节点的容量大小

5. pool我ie链表所在的内存池

ngx_list_part_t这个结构代表了我们的每一个节点：

1. elts指向我们的元素，在每一个节点都有一个顺序存储的结构，也就是普通的数组结构

2. nelts存储我们的元素个数

3. next指向下一个节点

ngx_list_t怎么使用？使用方法和ngx_array_t等数据结构很像。
----------------------------------

#### 1. 创建链表结构

#### 2. 初始化

#### 3. 获得可用空间地址

#### 4. 赋值到这个地址


我们看看create函数：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_list.c 
======================================================================
12 :   ngx_list_t *
13 :   ngx_list_create(ngx_pool_t *pool, ngx_uint_t n, size_t size)
14 :   {
15 :       ngx_list_t  *list;
16 :   
17 :       list = ngx_palloc(pool, sizeof(ngx_list_t)); /*创建一个列表结构*/
18 :       if (list == NULL) {
19 :           return NULL;
20 :       }
21 :   
22 :       if (ngx_list_init(list, pool, n, size) != NGX_OK) { /*初始化列表, 节点个数为n， 元素大小为size */
23 :           return NULL;
24 :       }
25 :   
26 :       return list;
27 :   }
```

这里的代码很简单：

1. 在内存池上分配了ngx_list_t数据结构

2. 调用文件域的函数ngx_list_init（）初始化这块内存结构

使用的时候，只有一个函数可用调用：ngx_list_push(),这个是我们在存入元素的时候要调用这个函数获取存取地址.

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_list.c 
======================================================================
30 :   void *
31 :   ngx_list_push(ngx_list_t *l)
32 :   {
33 :       void             *elt; /*元素指针*/
34 :       ngx_list_part_t  *last; 
36 :       last = l->last; /*存储最后一个节点*/ 
38 :       if (last->nelts == l->nalloc) { /*链表可用地址没有了,就分配一个新的链表节点 ngx_list_part_t*/
40 :           /* the last part is full, allocate a new list part */
42 :           last = ngx_palloc(l->pool, sizeof(ngx_list_part_t)); /*分配一个链表节点*/
43 :           if (last == NULL) {
44 :               return NULL;
45 :           }
47 :           last->elts = ngx_palloc(l->pool, l->nalloc * l->size); /*分配每一个节点所需要的存储数据的内存块*/
48 :           if (last->elts == NULL) {
49 :               return NULL;
50 :           }
51 :           /*初始化这个新分配的节点*/
52 :           last->nelts = 0;
53 :           last->next = NULL;
55 :           l->last->next = last;
56 :           l->last = last;
57 :       }
58 :       /*返回可用地址*/
59 :       elt = (char *) last->elts + l->size * last->nelts; /**/
60 :       last->nelts++; /*元素个数加一*/
62 :       return elt; /*返回可用地址，之后紧接着在这个地址赋值就行了*/
63 :   }
```

上面的代码，首先查看当前节点时候还有内存空间，如果没有了内存空间，就再分配一个链表节点，再返回地址，用于存储元素。

如果还有空间，那么就直接返回地址。

参考，ngx_array_t结构的实现，我们看到内存都是内存池分配的，基本都是预分配的内存，所以效率非常高，开辟内存，内存释放都是内存池的高效实现。

深深佩服nginx的设计，节约内存，效率极高。
