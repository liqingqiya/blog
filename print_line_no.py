#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
import fileinput
import pdb

if 1<=len(sys.argv)<4:
    print 'please input 2 arguments!'
    sys.exit()
elif len(sys.argv)>4:
    sys.exit('too more arguments!')

filepath = sys.argv[1]
line_begin = int(sys.argv[2])
line_end = int(sys.argv[3])

file_input = fileinput.input(filepath)

#pdb.set_trace()
for i in file_input:
    current_line_no = file_input.filelineno()

    if current_line_no==1:
        print '文件名：', file_input.filename(),'\n','='*70

    if current_line_no in xrange(line_begin, line_end+1):
        print file_input.filelineno(), ':  ', i,
    
