# -*- coding: utf-8 -*-

import os
import datetime
import time
import sys

def process_bar(i, total):
    """
    1. i代表当前循环的index号
    2. total代表循环次数
    """
    #a = "#" * i + " " * (100-i) + "["+str(i) + "%"+"]"
    #a = "#" * i + " " * (total-i) + "["+str(i) + "%"+"]"
    #a = "#" * (i//total) + " " * ((total-i)//total) + "["+str(i/total) + "%"+"]"
    #a = "#" * (i//100) + " " * ((100-i)//100) + "["+str(i/total*100) + "%"+"]"
    #a = "#" * (i) + " " * (100-i) + "["+str(i/total*100) + "%"+"]"   
    #a = "|"*(i//total*100) + " "*(100-i//total*100) + "["+str(i/total*100) + "%"+"]"
    a = "#"*(i//total*100) + ""*(100-i//total*100) + "["+str(i/total*100) + "%"+"]"    
    #print (i)
    sys.stdout.write("\r%s" % a)#sys.stdout.write是将str写到流，原封不动，不会像print那样默认end＝'\n'
    #time.sleep(0.00001)
    sys.stdout.flush()#sys.stdout.flush()的作用就是显示地让缓冲区的内容输出。
    if (i % total):
        pass
    else:
        print ('\n')
    

