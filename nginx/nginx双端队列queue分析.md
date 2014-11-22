nginx的queue是一个非常轻量级的结构，非常有着nginx特色。
-------------------------------------------------------------

nginx的queue结构体名字叫做 ngx_queue_t，是一个双向链表，如果要使用这个结构来构建我们的双向队列，只需要消耗两个指针的内存。

ngx_queue_t是nginx提供的一个基础顺序容器，以双链表的形式将数组组织在一起。

撇开具体的软件来讲，我们使用链表结构的优势在于能够高效的插入，删除，合并等，因为这些操作仅仅是对指针的操作而已。如果要实现高效的查找，nginx的核心结构是利用了红黑树来实现的。

相对于ngx_array_t和ngx_list_t等nginx里的顺序容器，ngx_queue_t有着自己的特色优点：
-----------------------------------------------------------

+ 轻量级，使用双链表的每一个节点元素只消耗两个指针的存储空间。

+ 不负责内存的分配，仅仅是负责已经分配好的内存块的链接。

+ 提供简单的排序功能。

+ 快速的进行两个链表的合并。

下面，我们就从源码的角度来分析：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_queue.h 
======================================================================
16 :   typedef struct ngx_queue_s  ngx_queue_t;
17 :
18 :   struct ngx_queue_s {
19 :       ngx_queue_t  *prev;
20 :       ngx_queue_t  *next;
21 :   };

```

在我们的 ngx_queue.h 文件中，定义了队列容器的结构体.我们可以看到这里的结构体只有两个指针，prev,next，其中，prev指向前一个节点元素，next指向后一个，

我们的ngx_queue_t其实是一个双向循环链表.

使用ngx_queue_t的情况比较特殊，下面说几个概念：
-----------------------------------------------

1. 链表容器自身使用ngx_queue_t 来代表自己。

2. 链表中的每一个元素同样使用ngx_queue_t结构来代表自己，并通过ngx_queue_t结构维持他与相邻元素之间的关系。

3. ngx_queue_t 是通过组合的方式，成为链表每一个元素的成员的。

这里要强调的是，由于容器与元素都用了ngx_queue_t的结构体来代表自己，为了避免ngx_queue_t结构体成员意义的混乱，nginx封装了链表容器与元素的所有方法。

对比与其他的容器，其他容器都需要直接使用成员变量来访问，而ngx_queue_t双向链表只能是通过我们的封装的方法来访问容器。

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_queue.h 
======================================================================
23 :   /*宏定义，就是一个队列，主要用在可重用网络连接*/
24 :   #define ngx_queue_init(q)                                                     \
25 :       (q)->prev = q;                                                            \
26 :       (q)->next = q

29 :   #define ngx_queue_empty(h)                                                    \
30 :       (h == (h)->prev)  /*队列为空*/
31 :   
32 :   /*在队列头处插入一个节点*/
33 :   #define ngx_queue_insert_head(h, x)                                           \
34 :       (x)->next = (h)->next;                                                    \
35 :       (x)->next->prev = x;                                                      \
36 :       (x)->prev = h;                                                            \
37 :       (h)->next = x
38 :   
39 :   
40 :   #define ngx_queue_insert_after   ngx_queue_insert_head
41 :   
42 :   /*将元素节点插在队列后面*/
43 :   #define ngx_queue_insert_tail(h, x)                                           \
44 :       (x)->prev = (h)->prev;                                                    \
45 :       (x)->prev->next = x;                                                      \
46 :       (x)->next = h;                                                            \
47 :       (h)->prev = x
48 :   
49 :   /*第一个节点*/
50 :   #define ngx_queue_head(h)                                                     \
51 :       (h)->next
52 :   
53 :   /*最后一个节点*/
54 :   #define ngx_queue_last(h)                                                     \
55 :       (h)->prev
56 :   
57 :   /*管理节点,也是代表我们的这个队列的节点*/
58 :   #define ngx_queue_sentinel(h)                                                 \
59 :       (h)
60 :   
61 :   /*q节点的下一个节点*/
62 :   #define ngx_queue_next(q)                                                     \
63 :       (q)->next
64 :   
65 :   /*q节点的上一个节点*/
66 :   #define ngx_queue_prev(q)                                                     \
67 :       (q)->prev
79 :   
80 :   #define ngx_queue_remove(x)                                                   \
81 :       (x)->next->prev = (x)->prev;                                              \
82 :       (x)->prev->next = (x)->next
85 :   
86 :   /*拆分队列 todo*/
87 :   #define ngx_queue_split(h, q, n)                                              \
88 :       (n)->prev = (h)->prev;                                                    \
89 :       (n)->prev->next = n;                                                      \
90 :       (n)->next = q;                                                            \
91 :       (h)->prev = (q)->prev;                                                    \
92 :       (h)->prev->next = h;                                                      \
93 :       (q)->prev = n;
94 :   
95 :   /*队列的合并，将n的队列合并到h的队列末尾*/
96 :   #define ngx_queue_add(h, n)                                                   \
97 :       (h)->prev->next = (n)->next;                                              \
98 :       (n)->next->prev = (h)->prev;                                              \
99 :       (h)->prev = (n)->prev;                                                    \
100 :       (h)->prev->next = h;
101 :   
102 :   /*非常重要的一个宏定义，能够将ngx_queue_t换算成节点结构体的地址*/
103 :   #define ngx_queue_data(q, type, link)                                         \
104 :       (type *) ((u_char *) q - offsetof(type, link))
105 :   
106 :   
107 :   ngx_queue_t *ngx_queue_middle(ngx_queue_t *queue);/**/
108 :   void ngx_queue_sort(ngx_queue_t *queue,
109 :       ngx_int_t (*cmp)(const ngx_queue_t *, const ngx_queue_t *));/*简单排序*/
110 :   
111 :   
```

这里nginx宏定义了很多语句，来完成队列的操作。

现在讲一下怎么使用ngx_queue_t这个结构体。

对于链表中的每一个元素，其类型可以是任意的struct结构体，###但是这个结构体中必须有一个ngx_queue_t类型的成员###。

在添加，删除元素的时候都是使用结构体ngx_queue_t类型成员的指针，因为ngx_queue_t作为每一个元素的代表。

当ngx_queue_t作为链表的元素成员的时候，能够使用下面几种方法：

```
ngx_queue_next(q)
ngx_queue_prev(q)
ngx_queue_data(q,type,link)
ngx_queue_insert_after(q,x)
```

下面特意介绍一下ngx_queue_data（），这个宏定义比较有意思：

```
102 :   /*非常重要的一个宏定义，能够将ngx_queue_t换算成节点结构体的地址*/
103 :   #define ngx_queue_data(q, type, link)                                         \
104 :       (type *) ((u_char *) q - offsetof(type, link))
```

这个宏定义将指向ngx_queue_t的地址换算成包含这个结构的元素节点的地址。

比如我们的节点是：

```
typedef test_node_s test_node_t;
struct test_node_s {
	u_char *name;
	ngx_queue_t qelt;
	int num;
}
```

这个时候，我们有一个指针变量q，这个变量指向一个test_node_s结构的ngx_queue_t成员，因为在使用queue的时候，我们都是用这个成员来代表我们的test_node_s的，

ngx_queue_data(q, test_node_t, qelt); 这样就能得到指向test_node_t结构的一个地址了。

现在我们一步步解释下这个宏， offsetof(test_node_t, qelt)，得到的是qelt这个成员在我们的test_node_t的结构的偏移量。然后q减去这个偏移量，也就是地址向上偏移这么多，

那么就恰好指向了我们的test_node_t结构了。

我们的ngx_queue.c提供了一个简单的排序函数。

排序方法需要自定义：

```
ngx_int_t cmp(const ngx_queue_t *q, const ngx_queue_t *p){
	test_node_t *node1 = ngx_queue_data(q,test_node_t,qelt);
	test_node_t *node2 = ngx_queue_data(p,test_node_t,qelt);
	return node1->num > node2->num;
}
```

再次强调，ngx_queue_t双向链表是完全不负责分配内存的，每一个链表元素必须自己管理自己的内存。

双向链表的结构又是怎么样子的呢？

有一个ngx_queue_t结构作为表头，其他test_node_t作为元素节点（节点一定要包含ngx_queue_t结构），如果为空的话，那么表头的next,prev就都是自己指向自己，形成自循环。

下面分析下 ngx_queue_sort()函数，这个函数定义在：src/core/ngx_queue.c中，
---------------------------------------------------------------------------

定义如下：

```
文件名： ../nginx-d0e39ec4f23f/src/core/ngx_queue.c 
======================================================================
48 :   /* the stable insertion sort */
49 :   
50 :   void
51 :   ngx_queue_sort(ngx_queue_t *queue,
52 :       ngx_int_t (*cmp)(const ngx_queue_t *, const ngx_queue_t *)) /*双端链表的插入排序*/
53 :   {
54 :       ngx_queue_t  *q, *prev, *next;
55 :   
56 :       q = ngx_queue_head(queue);  /*记录头*/
57 :   
58 :       if (q == ngx_queue_last(queue)) { /*为空，则退出*/
59 :           return;
60 :       }
61 :       /*ngx_queue_next(q)得到下一个元素节点*/
62 :       for (q = ngx_queue_next(q); q != ngx_queue_sentinel(queue); q = next) {
63 :   
64 :           prev = ngx_queue_prev(q); /*取q的上一个节点*/
65 :           next = ngx_queue_next(q); /*取q的下一个节点*/
66 :   
67 :           ngx_queue_remove(q);  /*先将q节点从链表中移除出来*/
68 :           /*该do-while循环找到节点插入的位置，用prev记录，然后把q插入到这个节点的后面.*/
69 :           do {
70 :               if (cmp(prev, q) <= 0) { /*小于, 排序结果是递增*/
71 :                   break;
72 :               }
73 :   
74 :               prev = ngx_queue_prev(prev);  /*prev其一个元素*/
75 :   
76 :           } while (prev != ngx_queue_sentinel(queue));
77 :   
78 :           ngx_queue_insert_after(prev, q);
79 :       }
80 :   }
```

这个链表的排序代码如上，就是一个非常简单的插入排序算法。这个排序算法是稳定的。
-----------------------------------------

里面的do-while循环的作用是找到q节点该插入的位置。然后调用ngx_queue_insert_after(prev,q);将q插入到prev节点的后面。

这个排序实现简单，不适合大规模的排序动作，但是对于nginx的运用范围已经足够了。


