#include <stdio.h>


#define toupper(c) ((c >= 'a' && c <= 'z')? (c &~ 0x20) : c)   /*宏定义*/
#define tolower(c) ((c >= 'A' && c <= 'Z')? (c | 0x20) : c)

#define DEBUG

#define to_string(n) #n                                        /*转化为字符串*/

#define mk_id(n) i##n                                          /*粘接*/

#define fun_called() printf("%s called\n", __func__)
#define fun_returned() printf("%s returned\n", __func__)

void
test(int n, ...)
{
    fun_called();

    //only c99
    //printf(__VA_ARGS__);

    fun_returned();
}

int
main(int argc, char *const *argv)
{
    char a[100]={'\0'};
    char *p, *q;

    q = a;
    while((*p = getchar())!='\n')
        *q++ = *p;

    /*大写*/
    q = a;
    while(*q)
        *q++ = toupper(*q);
    printf("upper:%s\n", a);

    /*小写*/
    q = a;
    while(*q)
        *q++ = tolower(*q);
    printf("lower:%s\n", a);

    /*转换为字符串*/
    printf("to_string:%s\n", to_string(bababal));

    /*预定义的宏*/

    /* __LINE__
     * __FILE__
     * __DATE__
     * __TIME__
     * */

    printf("__LINE__:%d\n"                     
            "__FILE__:%s\n"                             
            "__DATE__:%s\n"                            
            "__TIME__:%s\n", 
            __LINE__, 
            __FILE__, 
            __DATE__, 
            __TIME__
            );

    /*__func__调试函数*/
    test(3,"debian");
    return 0; 
}
