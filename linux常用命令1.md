在linux下面常用的一些命令:

#### 1. ldd 查看一个程序需要的共享库

```
liqing@debian:~/respor/C$ ldd va_list1
	linux-vdso.so.1 =>  (0x00007fff2a37d000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f8df9621000)
	/lib64/ld-linux-x86-64.so.2 (0x00007f8df99c4000)
```
