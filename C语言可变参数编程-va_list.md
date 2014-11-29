C语言可变参数编程
=========================

va_list 是c语言解决可变参数的一组宏
----------------------------------

1. 在函数中定义va_list类型的变量, 这个变量用于指向可变参数的指针.

2. 初始化va_list类型变量

3. 从va_list中取参数

4. 关闭va_list指针

宏定义
------------------

```
#include <stdarg.h>

#ifdef _M_ALPHA
typedef struct {
    char *a0;
    int offset;
}va_list;
#else
typedef char *va_list;
#endif

...

va_start(ap, n)
va_arg(ap, int)
va_end(ap)
va_copy(dest, src)
```

##### 1. 类型

```
va_list
```

#### 2. 赋值开始

```
va_start(ap, n)
```

##### 3. 取参数

```
va_arg(ap)
```

##### 4. 结尾清理

```
va_end(ap)
```

##### 5. 复制

```
va_copy(dest, src)
```

##### 6. __VA_ARGS__

#define debug(...) printf(__VA_ARGS__)

缺省号指向变化的参数表, 使用保留名__VA_ARGS__把参数传递给宏.
当宏调用展开的时候, 实际的参数就传递给printf()
