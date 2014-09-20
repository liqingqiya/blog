#/usr/bin python
#-*- coding:utf-8 -*- 

a = [12,22,4,5,6,1,24,21]
n = len(a)

for i in xrange(0,n):
    for j in xrange(1,n-i):
        if a[j-1]>a[j]:
            a[j-1], a[j] = a[j], a[j-1]

print a
