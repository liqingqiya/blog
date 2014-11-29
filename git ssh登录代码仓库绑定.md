ssh & git
========================
*当我们创建了在本地刚刚搭建好git环境,并创建了一个项目, 现在想要把这个项目和远端仓库的绑定起来, 并且是通过ssh登录,这样我们就可以不用输入用户名和密码了, 非常方便.*

ssh流程
------------------------------------

#### 1. 生成公钥/私钥

```
ssh-keygen
```

#### 2. 复制公钥添加到远端主机

公钥字符串在`~/.ssh/id_rsa.pub`文件中


git流程
----------------------------

#### 1. 安装git

```
sudo aptitude install git
```

#### 2. 进行一些全局性的设置(用户名, 密码, 颜色)

```
git config --global user.name "..."
git config --global user.email "...@...com"

git config --global color.ui true
```

#### 3. 创建一个本地仓库

```
mkdir test
touch new
git init
```

#### 4. 和远端绑定(当然了,这之前你的有一个已经创建好的远端仓库, 比如在github)

```
git remote add origin git@github.com:liqinqqiya/blog.git
```

#### 5. DONE
