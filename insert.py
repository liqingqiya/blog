#/usr/bin python
#-*-coding:utf-8-*-

a = [434,653,61]
n = len(a)

for i in xrange(1,n):
    key = a[i]
    j = i - 1
    while j>=0 and key<a[j]:
        a[j+1] = a[j]
        j-=1
    a[j+1] = key

print a
