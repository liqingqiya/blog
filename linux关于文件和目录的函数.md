文件和目录的维护
====================================

1. chomod系统调用

```
#include <sys/stat.h>

int chmod(const char *path, mode_t mode);
```

2. chown系统调用

```
#include <sys/types.h>
#include <unistd.h>

int chown(const char *path, uid_t owner, gid_t group);
```

3. unlink, link, symlink系统调用

```
#include <unistd.h>

int unlink(const char *path);
int link(const char *path1, const char *path2);
int symlink(const char *path1, const char *path2);
```

4. mkdir, rmdir系统调用

```
#include <sys/types.h>
#include <sys/stat.h>

int mkdir(const char *path, mode_t mode);
```

```
#include <unistd.h>

int rmdir(const char *path);
```

5. chdir系统调用和getcwd函数

```
#include <unistd.h>

int chdir(const char *path);
```

```
#include <unistd.h>

char *getcwd(char *buf, size_t size);
```

扫描目录
============================

1. opendir函数

```
#include <sys/types.h>
#include <dirent.h>

DIR *opendir(const char *name);
```

2. readdir函数

```
#include <sys/types.h>
#include <dirent.h>

struct dirent *readdir(DIR *dirp);
```

3. telldir函数

```
#include <sys/types.h>
#include <dirent.h>

long int telldir(DIR *dirp);
```

4. seekdir函数

```
#include <sys/types.h>
#include <dirent.h>

void seekdir(DIR *dirp, long int loc);
```

5. closedir函数

```
#include <sys/types.h>
#include <dirent.h>

int closedir(DIR *dirp);
```
