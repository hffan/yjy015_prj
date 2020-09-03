# -*- coding: UTF-8 -*-


import os
import stat


#判断文件是否具有可执行权限
def is_executable(file):
    print('判断文件是否有可执行权限%s'%file)
    try:
        status = os.access(file, os.X_OK)
        print (status)
        if(False==status):
            exit('%s 没有可执行权限，使用root用户，修改权限，chmod a+x %s'%(file,file))
    except Exception as e:
        exit(e)

