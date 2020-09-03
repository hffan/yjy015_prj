# -*- coding: UTF-8 -*-

import os
import time
import sys

"""
cd /home/YJY015/code/sys_interface; python3 sys_std.py
"""


def f_print(info):
    log_time = time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time()))
    log_pid ='[%13d]'%( os.getpid() )

    print (log_time,log_pid,info)
    
    
if __name__ == "__main__":
    pass
    # info = 'hello!\nworld!'
    # f_print(info)
    # f_print(info)
    # f_print(info)
    # f_print(info)    
