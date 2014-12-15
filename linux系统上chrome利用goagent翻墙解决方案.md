我的操作系统是linux的,国内墙掉了一大堆的优秀互联网应用.对于it人员来说,翻墙是必须的技能.
以前是买了一个vpn, 非常好用, 但是价格不菲. 最近走了一遍利用goagent翻墙,特此记录一下.

1. 你首先的有一个google帐号.

2. 注册帐号之后, 你得创建一个gae应用.

这个时候假设你已经完成了以上两步.

3. 下载goagent程序代码, 下载地址可以去github上: https://github.com/goagent/goagent,如果你有git, 
那么可以直接克隆下来,ssh地址为:git@github.com:goagent/goagent.git.

4. 上传这个程序文件到你的gae的app上.上传很简单, 只要你运行server目录下的uploader.py就行.
在上传的过程中, 你可能会出现问题. 导致你上传不成功. 这个时候你要先把你google账户设置中的安全设置
设置为:允许不安全软件的运行.appid就是你的gae的application的名字. 邮箱密码就是你谷歌账户的
帐号密码.

5. 上传成功之后, 要修改goagent/local/proxy.ini, 将appid改成你自己的appid.
这样goagent就配置完成了

6. 安装一个插件SwitchySharp Options

7. 导入证书CA.crt

8. 启动程序proxy.py就行了.运行的时候可能会出现警告:你的先安装一些python库, 比如ssl库,crypto库.
安装:`sudo aptitude install python-openssl`和`sudo aptitude install python-crypto`
