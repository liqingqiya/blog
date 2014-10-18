nginx内存池原理及源码分析
==================================

nginx对于内存的使用是非常小气的，绝对不浪费一丝毫的内存资源。所以nginx自己设计了一个内存池的结构，
用于分配内存，这样就能最大的提高内存的分配效率，总结nginx的内存池的特点：

### 内存分配尽量使用内存池分配，一次分配使用之后，并不会马上销毁，而是等到整个内存池都使用完了之后，才会考虑一次性的销毁内存 ###

这样利用有两个优点：

+ 效率提高，这个是相比与直接malloc，和 free来讲的

+ 减少了内存的内部碎片，因为每次销毁都会是比较大的内存块

我们来看nginx的内存池的源码实现：

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

