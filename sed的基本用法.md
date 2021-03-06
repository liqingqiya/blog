sed
=============================

sed 是一个非交互式文本编辑器, 可以对一个文本文件或者标准输入进行编辑.他的工作方式是什么?

+ 读取数据, 复制到缓冲区

+ 读取命令或脚本的地一个命令, 对文本进行编辑

+ 重复, 知道对所有的行都执行了命令

三种调用命令格式:

+ sed [选项] 'sed命令' input-file

+ sed [选项] -f sed脚本文件 input-file

+ ./sed脚本 输入

第三种方式, 必须在第一行写上 sha-bang, 也就是

`#!/usr/bin/sed`

三种方式默认的输入都是标准输入。

我们常用的sed有三个选项

+ -n     不打印所有行到标准输出

+ -f     表示正在调用sed脚本文件

+ -e     表示将下一个字符串解析为sed编辑命令， 如果只传递一个编辑命令给sed， -e选项可以省略

这里我们稍微提一下 `-e`， 这个选项，这个选项为什么会有用武之地，这是因为 sed 不支持同时带多个编辑命令的用法：

> sed -n '/certificate/p=' input 这种形式是错误的

我们如果要有多个编辑命令，那么一般正确的形式是：

> sed [选项] -e  编辑命令1 -e 编辑命令2 inputfile

我们的sed命令有两部分组成， 一个是文本定位，一个是文本编辑命令。

文本定位是通过：

+ 行号

+ 正则表达式

文本定位方法就是以下几种：

1. x                              x为指定行号

2. x，y                        指定从x到y的行号范围

3. /pattern/                  模式匹配的行

4. x，/pattern/             x行，到模式匹配的行

5. /pattern/，x             模式匹配的行，到x行

6. /pattern/pattern/      查询包含两个模式匹配的行

7. x，y！                     查询不包含x和y行号的行

```
input 文件

This is a Certificate Request file:

It should be mailed to zawu@seu.edu.cn

=================================================
Certificate Subject:

The above string is known as your user certific ate subject , and it uniqueley identifies this user.

\OU

to install this user certificate, please svae this e-mail message into the following file. 

/hoem/globus/.globus/usercert.pem

\OU

```

sed作业实例：

1.将input文件中的\OU字符串修改为（ou），并在与\OU匹行后追加 'We find \OU!'

> + sed -e 's/\OU/(ou)/g' -e '/ou/a\We find \\OU' input

> + sed 's/\OU/(ou)/g;/(ou)/a\We find \\OU' input 

以上的两种方本质上是一样的，都是一轮循环处理的文本行之后，再一一次循环处理。

> sed '定位 {命令1;命令2}' input 
> sed '/\OU/' input


这种方式和前面的两种多命令模式不一样， 这是对我们的定位行以此进行两个命令的处理。

2.将包含root字符串写保存缓冲区，然后遇到liqing这个字符串就交换模式缓冲区和保存缓冲区。然定向到output文件。

> cat /etc/passwd | sed -e '/root/h' -e '/liqing/x' > output
