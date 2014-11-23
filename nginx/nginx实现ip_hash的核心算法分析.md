IP 哈希
====================

ip hash也是实现负载均衡的一种算法。加权轮询是nginx负载均衡的基础策略，所以在ip hash中自然也要用到。

ip hash在nginx里作为一个可选的模块。在`src/http/modules/`目录下，模块的结构遵守http类模块的结构。

首先我们看初始化函数，`ngx_http_upstream_init_ip_hash()`,这个函数定义在`ngx_http_upstream_ip_hash_module.c`文件中，

调用时机是在解析配置文件的时候进行的初始化工作。

```
文件名： ../nginx/src/http/modules/ngx_http_upstream_ip_hash_module.c 
======================================================================
83 :   static ngx_int_t
84 :   ngx_http_upstream_init_ip_hash(ngx_conf_t *cf, ngx_http_upstream_srv_conf_t *us)
85 :   {
86 :       if (ngx_http_upstream_init_round_robin(cf, us) != NGX_OK) {             /*初始化加权轮询*/
87 :           return NGX_ERROR;
88 :       }
89 :   
90 :       us->peer.init = ngx_http_upstream_init_ip_hash_peer;                    /*初始化回调函数*/
91 :   
92 :       return NGX_OK;
93 :   }
```

这里就是进行了一些初始化，因为加权轮询策略作为我们的基础策略，这里也做了初始化。这里也设置了初始化回调函数:`ngx_http_upstream_init_ip_hash_peer`.
该函数是在一个客户端请求到来时候,我们选择上游服务器之前要做的初始化工作.

```
文件名： ../nginx/src/http/modules/ngx_http_upstream_ip_hash_module.c 
======================================================================
96 :   static ngx_int_t
97 :   ngx_http_upstream_init_ip_hash_peer(ngx_http_request_t *r,
98 :       ngx_http_upstream_srv_conf_t *us)                                       /*在对应一个request，选择后端服务器之前的初始化函数*/
99 :   {
100 :       struct sockaddr_in                     *sin;
101 :   #if (NGX_HAVE_INET6)
102 :       struct sockaddr_in6                    *sin6;
103 :   #endif
104 :       ngx_http_upstream_ip_hash_peer_data_t  *iphp;
105 :   
106 :       iphp = ngx_palloc(r->pool, sizeof(ngx_http_upstream_ip_hash_peer_data_t));
107 :       if (iphp == NULL) {
108 :           return NGX_ERROR;
109 :       }
110 :   
111 :       r->upstream->peer.data = &iphp->rrp;                                /*上游服务器列表*/
112 :   
113 :       if (ngx_http_upstream_init_round_robin_peer(r, us) != NGX_OK) {   /*初始化加权轮询模块*/
114 :           return NGX_ERROR;
115 :       }
116 :   
117 :       r->upstream->peer.get = ngx_http_upstream_get_ip_hash_peer;       /*设置选服务器的回调函数*/
118 :   
119 :       switch (r->connection->sockaddr->sa_family) {
120 :   
121 :       case AF_INET:
122 :           sin = (struct sockaddr_in *) r->connection->sockaddr;
123 :           iphp->addr = (u_char *) &sin->sin_addr.s_addr;
124 :           iphp->addrlen = 3;
125 :           break;
126 :   
127 :   #if (NGX_HAVE_INET6)
128 :       case AF_INET6:
129 :           sin6 = (struct sockaddr_in6 *) r->connection->sockaddr;
130 :           iphp->addr = (u_char *) &sin6->sin6_addr.s6_addr;
131 :           iphp->addrlen = 16;
132 :           break;
133 :   #endif
134 :   
135 :       default:
136 :           iphp->addr = ngx_http_upstream_ip_hash_pseudo_addr;
137 :           iphp->addrlen = 3;
138 :       }
139 :   
140 :       iphp->hash = 89;
141 :       iphp->tries = 0;
142 :       iphp->get_rr_peer = ngx_http_upstream_get_round_robin_peer;
143 :   
144 :       return NGX_OK;
145 :   }
```

这里主要工作是转存客户端IP,实现在地123-124行,和130-131行,如果是ipv4的ip地址,那么就只转存了前3个字节.
并且我们在这里117行,142行设置了获取上游服务器的回调函数.

然后就到了我们ip选择后端服务器的时候了,实现函数是:`ngx_http_upstream_get_ip_hash_peer()`

```
文件名： ../nginx/src/http/modules/ngx_http_upstream_ip_hash_module.c 
======================================================================
148 :   static ngx_int_t
149 :   ngx_http_upstream_get_ip_hash_peer(ngx_peer_connection_t *pc, void *data)
150 :   {
	...
164 :       if (iphp->tries > 20 || iphp->rrp.peers->single) {  /*当哈系选择失败20次以上，或只有一台后端服务器，此时采用加权轮询策略就可以了*/
165 :           return iphp->get_rr_peer(pc, &iphp->rrp);
166 :       }
	...
175 :       for ( ;; ) {
176 :   
177 :           for (i = 0; i < (ngx_uint_t) iphp->addrlen; i++) {      /*计算哈系值*/
178 :               hash = (hash * 113 + iphp->addr[i]) % 6271;
179 :           }
180 :   
181 :           if (!iphp->rrp.peers->weighted) {
182 :               p = hash % iphp->rrp.peers->number;                 /*根据hash值，得到被选中的后端服务器*/
183 :   
184 :           } else {
185 :               w = hash % iphp->rrp.peers->total_weight;
186 :   
187 :               for (i = 0; i < iphp->rrp.peers->number; i++) {
188 :                   w -= iphp->rrp.peers->peer[i].weight;
189 :                   if (w < 0) {
190 :                       break;
191 :                   }
192 :               }
193 :   
194 :               p = i;
195 :           }
196 :   
197 :           n = p / (8 * sizeof(uintptr_t));
198 :           m = (uintptr_t) 1 << p % (8 * sizeof(uintptr_t));
199 :   
 	...
221 :   
222 :           break;
223 :   
224 :       next_try:
225 :   
226 :           iphp->rrp.tried[n] |= m;
227 :   
228 :           /* ngx_unlock_mutex(iphp->rrp.peers->mutex); */
229 :   
230 :           pc->tries--;
231 :   
232 :       next:
233 :   
234 :           if (++iphp->tries >= 20) {
235 :               return iphp->get_rr_peer(pc, &iphp->rrp);
236 :           }
237 :       }
238 :   
239 :       iphp->rrp.current = p;
240 :   
241 :       pc->sockaddr = peer->sockaddr;   /*对nginx主动与后端服务器建立的连接进行赋值*/
242 :       pc->socklen = peer->socklen;
243 :       pc->name = &peer->name;
	...
251 :       iphp->rrp.tried[n] |= m;
252 :       iphp->hash = hash;
253 :   
254 :       return NGX_OK;
255 :   }
```

从上面的代码可以看到,这里的工作主要是:

1. ip hash直接计算出后端服务器

2. 记录位图,记录这次的选择.

其中这个函数在最前面会进行一次判断, 判断是否是只有一台服务器,或者说ip hash选择已经失败了20次, 那么这个时候,就会直接使用加权轮询算法.

之后进入for{；；}循环, 首先计算hash值.根据hash值选择后端服务器, 记录位图. 赋值到与后端服务器建立的主动连接结构就行了.


加权轮询和IP HASH两种策略的对比
-------------------------------

加权轮询策略的适用性要更强,不依赖客户端的任何信息,完全是依靠后端服务器的情况来选择.优势是能够吧客户端的请求更合理的,更均匀的分配到各个后端服务器处理,
缺点是,同一个客户端的请求,可能被分配到不同的后端服务器进行处理,无法满足会话保持的需求.

ip哈希策略能够吧同一个客户端的请求多次分配到同一台后端服务器处理,所以避免了加权轮询无法保持会话的需求.但是,因为ip哈希策略是根据客户端的ip地址来对后端服务器
进行选择,所以如果某一个时刻,来自某个ip地址的请求过多,那么将导致某一台后端服务器压力大,这样就存在负载不均衡的隐患.
