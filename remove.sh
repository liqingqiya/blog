#!/bin/bash
ls -l | grep .*~$ | awk '{print "rm", $9}' >remove_tmp.sh

