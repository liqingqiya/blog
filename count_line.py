#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
import fileinput
import os
import fnmatch
import pdb


def count_line(filepath):
    """
    computer the line
    ====================
    ++i, if the line is not blank.
    """
    count = 0
    file_input = fileinput.input(filepath)
    for i in file_input:
        #current_line_no = file_input.filelineno()
        if i!="\n":
            count += 1
    return count


def all_file(root=".", pattern="*.[hc]"):
    """
    统计指定目录下所有文件的代码行数
    """
    line_count = 0
    file_count = 0
    #pdb.set_trace()
    for path, subdir, files in os.walk(root):
        for file_name in files:
            if fnmatch.fnmatch(file_name, pattern):
                file_full_name = os.path.join(path, file_name)

                line_count += count_line(file_full_name)
                file_count += 1

    return file_count, line_count


if __name__ == "__main__":
    root = "." if len(sys.argv)==1 else sys.argv[1]
    print all_file(root)
