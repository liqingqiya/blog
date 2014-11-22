nginx默认的均衡负载算法是加权论寻，下面我就源码分析下nginx的核心思想
============================

nginx使用了ngx_http_upstream_rr_peer_t结构体来抽象一个服务器

```
typedef struct {
    struct sockaddr                *sockaddr;
    socklen_t                       socklen;
    ngx_str_t                       name;

    ngx_int_t                       current_weight;     /*当前权重*/
    ngx_int_t                       effective_weight;   /*有效权重*/
    ngx_int_t                       weight;             /* 初始权重，默认为1,与加权轮询配合使用,当所有的服务器current_weight小于0时候，那么就会使用该值来进行重新初始化*/

    ngx_uint_t                      fails;              /*失败次数*/
    time_t                          accessed;
    time_t                          checked;

    ngx_uint_t                      max_fails;          /*最大失败次数*/
    time_t                          fail_timeout;       /*与max_fails配合使用，默认值为10s，如果某服务器在fail_timeout时间内，失败达到max_fails，那么就在fail_timeout时间内，是不能参与被选择的。*/

    ngx_uint_t                      down;          /* 主动标记为宕机状态，不参与被选择 unsigned  down:1; */

#if (NGX_HTTP_SSL)
    ngx_ssl_session_t              *ssl_session;   /* local to a process */
#endif
} ngx_http_upstream_rr_peer_t;       /*该结构体对应一个后端服务器*/   
```

其中，核心为current_weight, weight, effective_weight这三个权值，其中weight是我们用进行设置的，如果没有设置，那么默认值就是1,current_weight是动态
变化的，effective_weight这个字段是nginx比较新的版本引进的，是对加权负载均衡算法的一种修正。

我们来看均衡负载的一个核心函数：ngx_http_upstream_get_round_robin_peer这个函数的源码如下：

```
ngx_int_t
ngx_http_upstream_get_round_robin_peer(ngx_peer_connection_t *pc, void *data)
{
    ngx_http_upstream_rr_peer_data_t  *rrp = data;

    ngx_int_t                      rc;
    ngx_uint_t                     i, n;
    ngx_http_upstream_rr_peer_t   *peer;
    ngx_http_upstream_rr_peers_t  *peers;

    ngx_log_debug1(NGX_LOG_DEBUG_HTTP, pc->log, 0,
                   "get rr peer, try: %ui", pc->tries); /**日志打印/

    /* ngx_lock_mutex(rrp->peers->mutex); */

    pc->cached = 0;
    pc->connection = NULL;

    if (rrp->peers->single) {           /*判断时候只有一台服务器*/
        peer = &rrp->peers->peer[0];    /*yes , 选择他*/

        if (peer->down) {               /*只有一台，却是宕机，则选择失败*/
            goto failed;
        }

    } else {

        /*有多台服务器可用*/

        peer = ngx_http_upstream_get_peer(rrp);     /*选择权值最高的一台服务器*/

        if (peer == NULL) { /*选择失败*/
            goto failed;
        }

        ngx_log_debug2(NGX_LOG_DEBUG_HTTP, pc->log, 0,
                       "get rr peer, current: %ui %i",
                       rrp->current, peer->current_weight);     /*打印日志信息,定义在/src/core/ngx_log.h模块中*/
    }

    pc->sockaddr = peer->sockaddr;  /*赋值当前选到的服务器信息*/
    pc->socklen = peer->socklen;
    pc->name = &peer->name;

    /* ngx_unlock_mutex(rrp->peers->mutex); */

    if (pc->tries == 1 && rrp->peers->next) {
        pc->tries += rrp->peers->next->number;
    }

    return NGX_OK;

failed:
    ...
    return NGX_BUSY;
}

```

这个函数调用了：ngx_http_upstream_get_peer来进行真正的选择，那么这个函数的又有什么作用：

```
static ngx_http_upstream_rr_peer_t *
ngx_http_upstream_get_peer(ngx_http_upstream_rr_peer_data_t *rrp)
{
    time_t                        now;
    uintptr_t                     m;
    ngx_int_t                     total;
    ngx_uint_t                    i, n;
    ngx_http_upstream_rr_peer_t  *peer, *best;

    now = ngx_time();

    best = NULL;        /* 存储选出的服务器 */
    total = 0;

    for (i = 0; i < rrp->peers->number; i++) {      /*遍历非后备服务器*/

        n = i / (8 * sizeof(uintptr_t));
        m = (uintptr_t) 1 << i % (8 * sizeof(uintptr_t));       /*m相当于掩码，用于计算是否被选择且失败过*/

        if (rrp->tried[n] & m) {    /* 已经选择过了, tried是一个位图，用于存储这些信息 */
            continue;
        }

        peer = &rrp->peers->peer[i];

        if (peer->down) {       /*宕机，那么就不考虑该服务器，跳过本次循环*/
            continue;
        }

        if (peer->max_fails     /*连接失败次数达到最大，并且还在fail_timeout时间内，则跳过本次循环*/
            && peer->fails >= peer->max_fails
            && now - peer->checked <= peer->fail_timeout)   /*checked存储本轮轮询时间*/
        {
            continue;
        }

        peer->current_weight += peer->effective_weight;     /* effective_weight是代表什么？current_weight呢？ */
        total += peer->effective_weight;

        if (peer->effective_weight < peer->weight) {        /*effective_weight应该不会降低到比weight还低啊？为什么还要这样比较？todo*/
            peer->effective_weight++;                           /*初始设定的effective_weight降低到比weight还低的时候，effective_weight++*/
        }

        if (best == NULL || peer->current_weight > best->current_weight) {  /* 选出的指标是current_weight,那么effective_weight有什么作用？ */
            best = peer;
        }
    }

    if (best == NULL) {
        return NULL;
    }

    i = best - &rrp->peers->peer[0];        /*该服务器索引*/

    rrp->current = i;                           /*该服务器索引*/

    n = i / (8 * sizeof(uintptr_t));
    m = (uintptr_t) 1 << i % (8 * sizeof(uintptr_t));       /*m为什么是这么计算的？？*/

    rrp->tried[n] |= m;     /*位图存储该轮被选择的服务器*/

    best->current_weight -= total;      /*选中的降低权值*/

    if (now - best->checked > best->fail_timeout) {
        best->checked = now;        /*如果时间超出了fail_timeout，则重置checked时间*/
    }

    return best;        /*返回权值最大的，最佳的服务器*/
}
```

总的来说：

1. 检查位图，看看这次轮询的服务器是否被选中过，如果选中过，则本轮跳过。

2. 查看是否宕机异常，宕机则跳过。

3. 查看是否达到最大连接失败次数且还在禁止期限内，那么跳过。

4. 如果以上都检查通过了，那么就遍历我们的非后备服务器，选出current_weight最大的服务器。

选择的流程如下：

1. current_weight += effective_weight.

2. 如果effective_weight比初始的weight还小，那么effective_weight++.

3. 遍历非后备服务器列表的同时，计算所有非后备服务器的effective_weight之和，存到total_weight中.

4. 选出current_weight最大的服务器，存入best.

5. 选出之后，将选出的peer的current_weight -= total_weight，以降低权值.
